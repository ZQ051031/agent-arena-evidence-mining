from dataclasses import replace
from unittest.mock import Mock
import requests
import pytest
from arena.delphi_client import DelphiClient
from arena.delphi_endpoints import PLACEHOLDER
from arena.submission import stable_key


def client(config, monkeypatch, session):
    from copy import deepcopy
    schema = deepcopy(PLACEHOLDER)
    schema["verified"] = True
    schema["paths"]["submit"] = "/test-only-submit"
    monkeypatch.setattr("arena.delphi_client.load_endpoints", lambda: schema)
    return DelphiClient(replace(config, dry_run=False, api_key="dummy", base_url="https://api.example.test"), session)


def test_stability(fact):
    other = replace(fact, text=fact.text + " Extra report 12.")
    assert stable_key("a", "m", [fact, other]) == stable_key("a", "m", [other, replace(fact, url="https://other.test")])
    assert stable_key("a", "m", [fact]) != stable_key("a", "m", [other])


def test_retry_reuses_header(config, monkeypatch):
    session = Mock()
    response = Mock()
    response.json.return_value = {"id": "test"}
    session.request.side_effect = [requests.Timeout(), response]
    api = client(config, monkeypatch, session)
    api.submit_evidence({"market_id": "m", "note": "n", "links": ["https://example.test"], "attachments": []}, "stable")
    assert [call.kwargs["headers"]["Idempotency-Key"] for call in session.request.call_args_list] == ["stable", "stable"]


def test_headers(config, monkeypatch):
    session = Mock()
    api = client(config, monkeypatch, session)
    session.request.return_value.json.return_value = []
    api.list_submissions()
    headers = session.request.call_args.kwargs["headers"]
    assert headers["X-Agent-Id"] == config.agent_id
    assert headers["X-Agent-Harness"] == config.harness
    assert headers["X-Agent-Model"] == config.model
    assert headers["Authorization"] == "Bearer dummy"


def test_timeout_fallback(config, monkeypatch):
    session = Mock()
    response = Mock()
    response.json.return_value = [{"idempotency_key": "stable", "verdict": "pending"}]
    session.request.side_effect = [requests.Timeout()] * 3 + [response]
    api = client(config, monkeypatch, session)
    payload = dict(market_id="m", note="n", links=["https://example.test"], attachments=[])
    assert api.submit_evidence(payload, "stable")["idempotency_key"] == "stable"


def test_missing_config_and_sample_refusal(config, monkeypatch):
    with pytest.raises(ValueError, match="requires"):
        replace(config, dry_run=False).validate()
    api = client(config, monkeypatch, Mock())
    with pytest.raises(ValueError, match="sample"):
        api.submit_evidence({"sample": True}, "test")
