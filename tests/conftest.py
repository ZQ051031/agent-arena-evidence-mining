import pytest
from datetime import datetime, timezone
from arena.config import Config
from arena.markets import load_markets, DATA
from arena.models import Fact
from arena.state import State


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Tests must not access the network")
    monkeypatch.setattr("requests.sessions.Session.request", blocked)
    now = lambda: datetime(2026, 11, 22, tzinfo=timezone.utc)
    for module in ("arena.models", "arena.markets", "arena.scoring", "arena.submission", "arena.state"):
        monkeypatch.setattr(module + ".utcnow", now)


@pytest.fixture
def config(tmp_path):
    return Config(state_path=str(tmp_path / "state.db"))


@pytest.fixture
def state(config):
    store = State(config.state_path)
    yield store
    store.db.close()


@pytest.fixture
def market():
    return load_markets(DATA / "sample_markets.json")[0]


@pytest.fixture
def fact():
    return Fact("On 2026-11-18 the civic transit bill passed with 40 votes.", "2026-11-18",
                "https://example.test/a", "example.test", "yes",
                "On 2026-11-18 the civic transit bill passed with 40 votes.")
