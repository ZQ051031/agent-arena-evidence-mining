"""Lightweight dated sentence extraction and explicitly heuristic stance."""
import json
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from .models import Fact
from .dedup import fingerprint

DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}\s+[A-Z][a-z]+\s+\d{4}\b|\b[A-Z][a-z]+\.?\s+\d{1,2},?\s+\d{4}\b")


def publish_date(html):
    soup = BeautifulSoup(html, "html.parser")
    meta = soup.find("meta", attrs={"property": "article:published_time"})
    if meta:
        return meta.get("content")
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            for item in data if isinstance(data, list) else [data]:
                if isinstance(item, dict) and item.get("datePublished"):
                    return item["datePublished"]
        except (ValueError, TypeError):
            pass
    time = soup.find("time")
    return time.get("datetime", time.get_text()) if time else None


def heuristic_stance(text, question):
    # Lexical cues are deliberately not a claim of semantic understanding.
    no = {"reject", "rejected", "declined", "fell", "lost", "delay", "cancelled", "below"}
    yes = {"approved", "passed", "increased", "rose", "won", "launched", "above"}
    tokens = set(text.lower().split())
    negative = bool(tokens & no)
    positive = bool(tokens & yes)
    if negative == positive:
        return "unclear"
    direction = "no" if negative else "yes"
    if any(cue in question.lower() for cue in ("decrease", "fall", "below", "lose", "reject")):
        direction = "yes" if direction == "no" else "no"
    return direction


def extract(result, source, market):
    facts = []
    page_date = publish_date(result.html)
    for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", result.text):
        if "SAMPLE FIXTURE" in sentence:
            continue
        if not any(k.lower() in sentence.lower() for k in market.keywords):
            continue
        date = DATE_RE.search(sentence)
        if not date and not re.search(r"\d", sentence):
            continue
        date_tokens = fingerprint(date.group()) if date else ""
        iso = next((token for token in date_tokens.split() if re.fullmatch(r"\d{4}-\d{2}-\d{2}", token)), None)
        facts.append(Fact(sentence, iso or page_date, source.url, urlparse(source.url).hostname or "",
                          heuristic_stance(sentence, market.question), sentence, result.judge_fetchable))
    return facts
