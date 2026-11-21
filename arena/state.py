import json
import sqlite3
from .models import utcnow
from .rules import MAX_SUBMISSIONS, QUALIFY_MARKETS, QUALIFY_SUBMISSIONS


class State:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS submissions (
          market_id TEXT, idempotency_key TEXT UNIQUE, status TEXT, stance TEXT,
          fingerprints TEXT, payload TEXT, receipt TEXT, created TEXT, updated TEXT);
        CREATE TABLE IF NOT EXISTS seen_facts (
          market_id TEXT, fingerprint TEXT, UNIQUE(market_id, fingerprint));
        """)

    def rows(self):
        return [dict(r) for r in self.db.execute("SELECT * FROM submissions")]

    def count_for_market(self, market_id):
        return self.db.execute(
            "SELECT count(*) FROM submissions WHERE market_id=? AND status IN ('pending','sent','confirmed')",
            (market_id,)).fetchone()[0]

    def can_submit(self, market_id):
        return self.count_for_market(market_id) < MAX_SUBMISSIONS

    def known(self, market_id):
        return [r[0] for r in self.db.execute("SELECT fingerprint FROM seen_facts WHERE market_id=?", (market_id,))]

    def stance(self, market_id):
        row = self.db.execute("SELECT stance FROM submissions WHERE market_id=? AND status!='failed' LIMIT 1",
                              (market_id,)).fetchone()
        return row[0] if row else None

    def record_pending(self, payload, fingerprints):
        key, market = payload["idempotency_key"], payload["market_id"]
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            if self.db.execute("SELECT 1 FROM submissions WHERE idempotency_key=?", (key,)).fetchone():
                return
            if not self.can_submit(market):
                raise ValueError("Three submissions per market cap reached")
            now = utcnow().isoformat()
            self.db.execute("INSERT INTO submissions VALUES (?,?,?,?,?,?,?,?,?)",
                            (market, key, "pending", payload["stance"], json.dumps(fingerprints),
                             json.dumps(payload), None, now, now))
            for fp in fingerprints:
                self.db.execute("INSERT OR IGNORE INTO seen_facts VALUES (?,?)", (market, fp))

    def mark_sent(self, key, receipt=None):
        verdict = (receipt or {}).get("verdict")
        status = "confirmed" if verdict and verdict != "pending" else "sent"
        with self.db:
            self.db.execute("UPDATE submissions SET status=?, receipt=?, updated=? WHERE idempotency_key=?",
                            (status, json.dumps(receipt), utcnow().isoformat(), key))

    def reconcile(self, remote):
        for item in remote:
            key = item.get("idempotency_key")
            if key:
                self.mark_sent(key, item)

    def mark_failed(self, key):
        """Use only for a definitive rejection, never an ambiguous timeout."""
        with self.db:
            self.db.execute("UPDATE submissions SET status='failed', updated=? WHERE idempotency_key=?",
                            (utcnow().isoformat(), key))

    def eligibility(self):
        judged = [r for r in self.rows() if r["receipt"] and
                  (lambda x: not x.get("mock") and x.get("verdict") not in (None, "pending", "not_judged_mock"))(json.loads(r["receipt"]))]
        return {"judged": len(judged), "markets": len({r["market_id"] for r in judged}),
                "required_submissions": QUALIFY_SUBMISSIONS, "required_markets": QUALIFY_MARKETS}
