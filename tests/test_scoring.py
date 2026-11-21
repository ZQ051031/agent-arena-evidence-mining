from dataclasses import replace
from datetime import datetime, timezone
from arena.scoring import score_fact, WEIGHTS

NOW = datetime(2026, 11, 22, tzinfo=timezone.utc)


def test_weights():
    assert round(sum(WEIGHTS.values()), 8) == 1


def test_scoring(fact, market):
    score = score_fact(fact, market, [], now=NOW)
    assert .45 < score <= 1
    assert score_fact(fact, market, [fact.text], now=NOW) == 0
    assert score_fact(replace(fact, date=None), market, [], now=NOW) < score
    assert score_fact(replace(fact, date="2026-12-25"), market, [], now=NOW) == 0
    assert score_fact(replace(fact, date="not a date"), market, [], now=NOW) == 0


def test_accessibility_and_corroboration(fact, market):
    base = score_fact(fact, market, [], now=NOW)
    assert score_fact(replace(fact, judge_fetchable=False), market, [], now=NOW) < base
    assert score_fact(fact, market, [], [fact, replace(fact, domain="other.test")], now=NOW) > base
