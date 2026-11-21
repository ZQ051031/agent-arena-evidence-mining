from dataclasses import replace
from datetime import datetime, timezone
import pytest
from arena.submission import SubmissionBuilder


def test_cap(config, state, market, fact, tmp_path):
    builder = SubmissionBuilder(config, state, tmp_path)
    for index in range(3):
        item = replace(fact, text=fact.text + f" stage {index}")
        payload = builder.build(market, [item])
        state.record_pending(payload, [item.text])
    assert state.count_for_market(market.id) == 3
    with pytest.raises(ValueError, match="cap"):
        builder.build(market, [fact])


def test_validation(config, state, market, fact, tmp_path):
    builder = SubmissionBuilder(config, state, tmp_path)
    payload = builder.build(market, [fact])
    with pytest.raises(ValueError, match="cutoff"):
        builder.validate(payload, market, [fact], datetime(2027, 1, 1, tzinfo=timezone.utc))
    with pytest.raises(ValueError, match="Single"):
        builder.validate(payload, market, [fact, replace(fact, stance="no")])
    with pytest.raises(ValueError, match="links"):
        builder.validate(dict(payload, note=""), market, [fact])
    with pytest.raises(ValueError, match="3 attachments"):
        builder.validate(dict(payload, attachments=["x"] * 4), market, [fact])
    bad = tmp_path / "bad.exe"
    bad.write_text("not evidence")
    with pytest.raises(ValueError, match="extension"):
        builder.validate(dict(payload, attachments=[str(bad)]), market, [fact])


def test_prior_stance(config, state, market, fact, tmp_path):
    builder = SubmissionBuilder(config, state, tmp_path)
    state.record_pending(builder.build(market, [fact]), [fact.text])
    with pytest.raises(ValueError, match="prior"):
        builder.build(market, [replace(fact, stance="no")])


def test_snapshot(config, state, market, fact, tmp_path):
    payload = SubmissionBuilder(config, state, tmp_path).build(market, [replace(fact, judge_fetchable=False)])
    assert len(payload["attachments"]) == 1
    assert "SAMPLE" in payload["note"]


def test_empty_and_size(config, state, market, fact, tmp_path):
    builder = SubmissionBuilder(config, state, tmp_path)
    with pytest.raises(ValueError, match="At least one"):
        builder.build(market, [])
    payload = builder.build(market, [fact])
    attachment = tmp_path / "large.txt"
    attachment.write_text("oversize")
    config.max_bytes = 2
    with pytest.raises(ValueError, match="size cap"):
        builder.validate(dict(payload, attachments=[str(attachment)]), market, [fact])


def test_state_restart_reserves_pending(config, state, market, fact, tmp_path):
    from arena.state import State
    builder = SubmissionBuilder(config, state, tmp_path)
    payload = builder.build(market, [fact])
    state.record_pending(payload, [fact.text])
    state.record_pending(payload, [fact.text])
    reopened = State(config.state_path)
    assert reopened.count_for_market(market.id) == 1
    reopened.db.close()


def test_pending_receipt_keeps_polling(config, state, market, fact, tmp_path):
    payload = SubmissionBuilder(config, state, tmp_path).build(market, [fact])
    key = payload["idempotency_key"]
    state.record_pending(payload, [fact.text])
    state.mark_sent(key, {"verdict": "pending"})
    assert state.rows()[0]["status"] == "sent"
    state.reconcile([{"idempotency_key": key, "verdict": "accepted"}])
    assert state.rows()[0]["status"] == "confirmed"
    assert state.eligibility()["judged"] == 1
