"""Conservative lexical fact identity across sources; not semantic translation."""
import re
from datetime import datetime
STOP = set("a an the on in at of to for is was are were has have had by with and that as from it".split())
MONTHS = {datetime(2026, n, 1).strftime("%B").lower(): n for n in range(1, 13)}


def normalize(text):
    text = text.lower()
    for month, n in MONTHS.items():
        names = month + "|" + month[:3] + r"\.?"
        text = re.sub(r"\b(\d{1,2})\s+(?:" + names + r")\s+(\d{4})",
                      lambda m: f"{m[2]}-{n:02d}-{int(m[1]):02d}", text)
        text = re.sub(r"\b(?:" + names + r")\s+(\d{1,2}),?\s+(\d{4})",
                      lambda m: f"{m[2]}-{n:02d}-{int(m[1]):02d}", text)
    tokens = re.findall(r"\d{4}-\d{2}-\d{2}|\d+(?:\.\d+)?|[a-z]+", text.replace(",", ""))
    return set(token for token in tokens if token not in STOP)


def fingerprint(text):
    return " ".join(sorted(normalize(text)))


def similarity(a, b):
    a, b = normalize(a), normalize(b)
    if not a or not b:
        return 0.0
    numbers_a = {x for x in a if x[0].isdigit()}
    numbers_b = {x for x in b if x[0].isdigit()}
    if numbers_a and numbers_b and numbers_a != numbers_b:
        return 0.0
    return len(a & b) / len(a | b)


def is_repeat(text, known, threshold=0.72):
    return any(similarity(text, other) >= threshold for other in known)


def unique_facts(facts, known):
    accepted = []
    for fact in facts:
        if not is_repeat(fact.text, known + [f.text for f in accepted]):
            accepted.append(fact)
    return accepted
