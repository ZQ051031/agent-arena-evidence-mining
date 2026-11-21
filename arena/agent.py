import json
import logging
import re
from pathlib import Path
from .dedup import unique_facts, fingerprint
from .extractor import extract
from .fetcher import Fetcher
from .markets import load_markets, open_markets
from .scoring import score_fact
from .search import REGISTRY
from .stance import choose_stance
from .submission import SubmissionBuilder


class Agent:
    def __init__(self, config, state, client, out="out", markets=None):
        self.config, self.state, self.client = config, state, client
        self.out, self.markets_path = Path(out), markets

    def poll_receipts(self):
        if not self.config.dry_run:
            self.state.reconcile(self.client.list_submissions())
        for row in self.state.rows():
            if row["status"] == "sent":
                receipt = self.client.get_receipt(row["idempotency_key"])
                self.state.mark_sent(row["idempotency_key"], receipt)

    def cycle(self):
        if not self.config.dry_run and self.config.provider == "local":
            raise ValueError("Local fictional corpus is forbidden in live mode")
        if any(json.loads(row["payload"]).get("sample", False) != self.config.dry_run
               for row in self.state.rows()):
            raise ValueError("Do not mix live and sample state: choose a separate ARENA_STATE_PATH")
        self.poll_receipts()
        # Resume ambiguous sends with their persisted key, never a fresh key.
        for row in self.state.rows():
            if row["status"] == "pending":
                payload = json.loads(row["payload"])
                receipt = self.client.submit_evidence(payload, row["idempotency_key"])
                self.state.mark_sent(row["idempotency_key"], receipt)
        built = []
        for market in open_markets(load_markets(self.markets_path, self.client)):
            if not self.config.dry_run and market.sample:
                raise ValueError("Sample markets are forbidden live")
            if not self.state.can_submit(market.id):
                continue
            known = self.state.known(market.id) + re.split(
                r"(?<=[.!?])\s+", market.description + " " + market.resolution_criteria)
            facts = []
            try:
                sources = REGISTRY[self.config.provider]().search(market.question)
            except Exception as exc:
                logging.warning("Search failed for %s: %s", market.id, exc)
                continue
            for source in sources:
                result = Fetcher(self.config).fetch(source)
                if result.ok:
                    facts.extend(extract(result, source, market))
            for fact in facts:
                fact.score = score_fact(fact, market, known, facts)
            unique = unique_facts(sorted(facts, key=lambda f: f.score, reverse=True), known)
            side = choose_stance(unique, self.state.stance(market.id))
            candidates = [f for f in unique if f.stance == side and f.score >= self.config.min_score]
            if not candidates:
                continue
            # One strongest fact per slot avoids long notes and weak bundles.
            chosen = candidates[:1]
            payload = SubmissionBuilder(self.config, self.state, str(self.out)).build(market, chosen)
            self.state.record_pending(payload, [fingerprint(f.text) for f in chosen])
            if self.config.dry_run:
                self.out.mkdir(parents=True, exist_ok=True)
                (self.out / ("sample-" + payload["idempotency_key"] + ".json")).write_text(json.dumps(payload, indent=2))
            receipt = self.client.submit_evidence(payload, payload["idempotency_key"])
            self.state.mark_sent(payload["idempotency_key"], receipt)
            built.append(payload)
            print(f'{"SAMPLE dry-run" if self.config.dry_run else "LIVE"}: {market.id} stance={side} status={receipt.get("verdict", "sent")}')
        self.poll_receipts()
        print(f"Cycle complete: {len(built)} submissions built; no rewards claimed.")
        return built
