import json
import requests
from .delphi_endpoints import load_endpoints, map_market
from .markets import load_markets, DATA


class DelphiClient:
    def __init__(self, config, session=None):
        config.validate()
        self.config, self.session = config, session or requests.Session()
        self.endpoints = load_endpoints()
        if not self.endpoints["verified"]:
            raise ValueError("Delphi schema is PLACEHOLDER; configure official paths/headers/fields and verified=true in DELPHI_ENDPOINTS_JSON")

    def headers(self):
        names = self.endpoints["headers"]
        c = self.config
        return {names["authorization"]: self.endpoints["auth_prefix"] + c.api_key,
                names["agent_id"]: c.agent_id, names["harness"]: c.harness,
                names["model"]: c.model, "User-Agent": c.user_agent}

    def request(self, method, operation, **kwargs):
        path = self.endpoints["paths"][operation]
        if "PLACEHOLDER" in path:
            raise ValueError(f"Official {operation} endpoint not configured")
        headers = self.headers()
        headers.update(kwargs.pop("headers", {}))
        response = self.session.request(method, self.config.base_url.rstrip("/") + path,
                                        headers=headers, timeout=self.config.timeout, **kwargs)
        response.raise_for_status()
        return response.json()

    def list_markets(self):
        data = self.request("GET", "markets")
        rows = data if isinstance(data, list) else data[self.endpoints["list_fields"]["markets"]]
        return [map_market(item, self.endpoints) for item in rows]

    def list_submissions(self):
        data = self.request("GET", "submissions")
        return data if isinstance(data, list) else data[self.endpoints["list_fields"]["submissions"]]

    def submit_evidence(self, payload, idempotency_key):
        if payload.get("sample"):
            raise ValueError("Refusing to submit sample evidence live")
        if payload.get("attachments"):
            raise ValueError("Live attachment transport unknown; configure official adapter before sending attachments")
        mapped = {remote: payload[local] for local, remote in self.endpoints["payload_fields"].items()}
        for attempt in range(self.config.retries + 1):
            try:
                return self.request("POST", "submit", json=mapped,
                                    headers={"Idempotency-Key": idempotency_key})
            except (requests.Timeout, requests.ConnectionError):
                if attempt == self.config.retries:
                    for item in self.list_submissions():
                        if item.get("idempotency_key") == idempotency_key:
                            return item
                    raise

    def get_receipt(self, submission_id):
        field = self.endpoints["receipt_id_field"]
        if field == "PLACEHOLDER":
            raise ValueError("Official receipt ID query field not configured")
        return self.request("GET", "receipt", params={field: submission_id})

    def send_feedback(self, text):
        field = self.endpoints["feedback_text_field"]
        if field == "PLACEHOLDER":
            raise ValueError("Official feedback text field not configured")
        return self.request("POST", "feedback", json={field: text})


class MockDelphiClient:
    def __init__(self, state=None):
        self.state, self.submissions = state, []

    def list_markets(self):
        return load_markets(DATA / "sample_markets.json")

    def list_submissions(self):
        return self.submissions

    def submit_evidence(self, payload, idempotency_key):
        receipt = {"mock": True, "verdict": "not_judged_mock",
                   "idempotency_key": idempotency_key, "market_id": payload["market_id"]}
        self.submissions.append(receipt)
        return receipt

    def get_receipt(self, submission_id):
        return {"mock": True, "verdict": "not_judged_mock", "id": submission_id}

    def send_feedback(self, text):
        return {"mock": True, "feedback": text, "sent": False}
