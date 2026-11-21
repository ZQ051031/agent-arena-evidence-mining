import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    api_key: str = ""
    base_url: str = ""
    agent_id: str = "sample-agent"
    harness: str = "arena-python"
    model: str = "heuristic-no-model"
    dry_run: bool = True
    state_path: str = "arena.db"
    provider: str = "local"
    user_agent: str = "EvidenceArena/0.1"
    timeout: float = 15
    retries: int = 2
    max_bytes: int = 2_000_000
    min_score: float = 0.45

    def validate(self):
        if not self.dry_run and (not self.api_key or not self.base_url):
            raise ValueError("Live mode requires DELPHI_API_KEY and DELPHI_API_BASE_URL")
        if not self.dry_run and not self.base_url.startswith("https://"):
            raise ValueError("Live API base URL must use HTTPS")


def load_config(env_file=".env"):
    values = {}
    path = Path(env_file)
    if path.is_file():
        for line in path.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip("\"'")
    values.update(os.environ)
    mapping = {"api_key": "DELPHI_API_KEY", "base_url": "DELPHI_API_BASE_URL",
               "agent_id": "DELPHI_AGENT_ID", "harness": "DELPHI_AGENT_HARNESS",
               "model": "DELPHI_AGENT_MODEL", "state_path": "ARENA_STATE_PATH",
               "provider": "ARENA_SEARCH_PROVIDER", "user_agent": "ARENA_USER_AGENT"}
    kwargs = {key: values[name] for key, name in mapping.items() if name in values}
    kwargs["dry_run"] = values.get("ARENA_DRY_RUN", "true").lower() not in ("false", "0", "no")
    for name, cast in (("timeout", float), ("retries", int), ("max_bytes", int), ("min_score", float)):
        if "ARENA_" + name.upper() in values:
            kwargs[name] = cast(values["ARENA_" + name.upper()])
    return Config(**kwargs)
