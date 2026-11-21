from dataclasses import dataclass, field
from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc)


def parse_time(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@dataclass
class Market:
    id: str
    question: str
    description: str
    category: str
    close_time: str
    evidence_cutoff: str
    keywords: list[str] = field(default_factory=list)
    odds: float | None = None
    forecaster_prob: float | None = None
    reward_pot: float | None = None
    resolution_criteria: str = ""
    sample: bool = False


@dataclass
class Source:
    url: str
    title: str = ""
    local_path: str | None = None


@dataclass
class Fact:
    text: str
    date: str | None
    url: str
    domain: str
    stance: str = "unclear"
    quote: str = ""
    judge_fetchable: bool = True
    score: float = 0.0


@dataclass
class Evidence:
    facts: list[Fact]
    stance: str


@dataclass
class Submission:
    market_id: str
    note: str
    links: list[str]
    attachments: list[str]
    stance: str
    idempotency_key: str
    sample: bool = False
