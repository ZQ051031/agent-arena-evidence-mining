import hashlib
import json
import logging
from dataclasses import asdict
from pathlib import Path
from .dedup import fingerprint
from .models import Submission, parse_time, utcnow
from .rules import MAX_ATTACHMENTS

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".csv", ".txt", ".md"}


def stable_key(agent_id, market_id, facts):
    content = [agent_id, market_id, sorted(set(fingerprint(f.text) for f in facts))]
    return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()


class SubmissionBuilder:
    def __init__(self, config, state, out="out"):
        self.config, self.state, self.out = config, state, Path(out)

    def validate(self, payload, market, facts, now=None):
        if (now or utcnow()) >= parse_time(market.evidence_cutoff):
            raise ValueError("Market evidence cutoff has passed")
        if not self.state.can_submit(market.id):
            raise ValueError("Three submissions per market cap reached")
        if not payload["note"].strip() or len(payload["note"]) > 1200 or not payload["links"]:
            raise ValueError("Non-empty short note and links required")
        if len(payload["attachments"]) > MAX_ATTACHMENTS:
            raise ValueError("Maximum 3 attachments")
        for file in payload["attachments"]:
            path = Path(file)
            if path.suffix.lower() not in ALLOWED_EXTENSIONS:
                raise ValueError("Unsupported attachment extension")
            if path.stat().st_size > self.config.max_bytes:
                raise ValueError("Attachment size cap exceeded")
        if not facts or any(f.stance != payload["stance"] for f in facts) or payload["stance"] not in ("yes", "no"):
            raise ValueError("Single clear stance required")
        prior = self.state.stance(market.id)
        if prior and prior != payload["stance"]:
            raise ValueError("Stance conflicts with prior submissions")

    def build(self, market, facts):
        if not facts:
            raise ValueError("At least one fact required")
        key = stable_key(self.config.agent_id, market.id, facts)
        attachments = []
        for index, fact in enumerate(facts):
            if not fact.judge_fetchable:
                self.out.mkdir(parents=True, exist_ok=True)
                path = self.out / (key + f"-{index}-snapshot.txt")
                path.write_text(("SAMPLE OUTPUT\n" if self.config.dry_run else "") +
                                f"URL: {fact.url}\nRetrieved: {utcnow().isoformat()}\n{fact.quote}")
                attachments.append(str(path))
                logging.warning("Inaccessible source: text snapshot is NOT a screenshot; real screenshot recommended")
        prefix = "SAMPLE — FICTIONAL FIXTURE, NOT REAL EVIDENCE. " if self.config.dry_run else ""
        note = prefix + f"Claim ({facts[0].stance}; heuristic): " + " ".join(
            f'{f.date or "Undated"}: "{f.quote or f.text}"' for f in facts)
        note += f" Relevance: bears on {market.question} Sources: " + ", ".join(f.url for f in facts)
        payload = asdict(Submission(market.id, note[:1200], sorted({f.url for f in facts}),
                                    attachments, facts[0].stance, key, self.config.dry_run))
        self.validate(payload, market, facts)
        return payload
