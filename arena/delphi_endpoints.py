"""PLACEHOLDER configuration: do not treat these as a real Delphi API schema."""
import json
import os
from copy import deepcopy
from .models import Market

# TODO(25 Nov): paste paths from the official starter agent / agent guide
PLACEHOLDER = {
    "paths": {"submissions": "/v1/submissions",  # Only FAQ-confirmed endpoint
              "markets": "PLACEHOLDER", "submit": "PLACEHOLDER",
              "receipt": "PLACEHOLDER", "feedback": "PLACEHOLDER"},
    "headers": {"authorization": "Authorization",  # Bearer assumed, unverified
                "agent_id": "X-Agent-Id", "harness": "X-Agent-Harness", "model": "X-Agent-Model"},
    "auth_prefix": "Bearer ",
    "market_fields": {name: name for name in Market.__dataclass_fields__},
    "payload_fields": {name: name for name in ("market_id", "note", "links", "attachments")},
    "list_fields": {"markets": "markets", "submissions": "submissions"},
    "receipt_id_field": "PLACEHOLDER",
    "feedback_text_field": "PLACEHOLDER",
    "verified": False,
}


def load_endpoints():
    config = deepcopy(PLACEHOLDER)
    if os.environ.get("DELPHI_ENDPOINTS_JSON"):
        with open(os.environ["DELPHI_ENDPOINTS_JSON"]) as handle:
            override = json.load(handle)
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(config.get(key), dict):
                config[key].update(value)
            else:
                config[key] = value
    return config


def map_market(data, config):
    return Market(**{local: data[remote] for local, remote in config["market_fields"].items()
                     if remote in data})
