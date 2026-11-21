from arena.agent import Agent
from arena.delphi_client import MockDelphiClient
from arena.dedup import is_repeat
from arena.markets import load_markets, DATA


def test_cycles(config, state, tmp_path):
    agent = Agent(config, state, MockDelphiClient(state), tmp_path / "out")
    first = agent.cycle()
    assert len(first) == 4
    for _ in range(5):
        agent.cycle()
    markets = load_markets(DATA / "sample_markets.json")
    for market in markets:
        assert state.count_for_market(market.id) == 3
        fingerprints = state.known(market.id)
        for index, fp in enumerate(fingerprints):
            assert not is_repeat(fp, fingerprints[:index])
    assert state.eligibility()["judged"] == 0
    assert all(item["sample"] for item in first)
    assert len(list((tmp_path / "out").glob("sample-*.json"))) == 12
