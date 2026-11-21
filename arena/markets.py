import json
from pathlib import Path
from .models import Market, parse_time, utcnow

DATA = Path(__file__).resolve().parent.parent / "data"


def load_markets(path=None, client=None):
    if path:
        raw = json.loads(Path(path).read_text())
        return [Market(**item) for item in raw["markets"]]
    return client.list_markets()


def open_markets(markets, now=None):
    now = now or utcnow()
    return [m for m in markets if now < parse_time(m.evidence_cutoff)]
