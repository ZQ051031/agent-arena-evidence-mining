"""Facts supplied from DoraHacks detail page, read 22 November 2026."""
FACTS_URL = "https://dorahacks.io/hackathon/delphi-agent-competition2/detail"
MAX_SUBMISSIONS = 3
MAX_ATTACHMENTS = 3
QUALIFY_SUBMISSIONS = 10
QUALIFY_MARKETS = 3
PRIZES_USD = {"first": 3000, "second": 2000, "third": 1000, "feedback_each": 250}
FEEDBACK_BOUNTIES = 5
PRIZE_POOL_USD = 7250
TIMELINE = {
    "registration": "2026-11-13T17:00:00Z",
    "opens": "2026-11-25T17:00:00Z",
    "submission_opens_utc8": "2026-11-26T01:00:00+08:00",
    "deadline": "2026-12-11T17:00:00Z",
    "submission_deadline_utc8": "2026-12-12T01:00:00+08:00",
    "winners": "2026-12-16T17:00:00Z",
}
DISCORD = "https://discord.gg/SaCPyB4fZX"
RULES = (
    "Evidence rewards are separate from prizes. New markets every few days.",
    "One wallet per entry; use same main Delphi wallet on DoraHacks; agent name added within ~12h.",
    "API access, starter agent, guide and one-line prompt published 25 Nov.",
    "Send agent ID, harness and model headers; read odds, close time, cutoff and reward pot.",
    "One market per submission: short note, links, up to 3 files; max 3 submissions per agent per market.",
    "Dated sourced new facts earn most; repeated FACTS across URLs, quotes or languages earn nothing.",
    "Already-known facts earn nothing; opposite sides cancel. Evidence cutoff is submission deadline.",
    "Receipt verdict, rationale and judgment reward within minutes; USDC.e wallet payment 24h later; settlement reward may follow.",
    "Rank by judgment + settlement rewards on competition markets, not counts; ties earliest total.",
    "Qualify with >=10 judged submissions across >=3 markets.",
    "Prizes in USDC after integrity review, sanctions screening and KYC.",
    "Real public evidence only; no fabricated facts, copying, judge manipulation, collusion, confidential or private personal data, or terms violations.",
    "Judge fetches links once, basic fetch only; X, Reddit, paywalls and logins usually fail.",
    "Paste key text and attach screenshot with URL and date for inaccessible links; judge reads PDFs.",
    "Forecaster researches independently; API/UI forecaster probabilities or market odds fallback.",
    "No edit/retraction. On timeout check GET /v1/submissions and retry SAME Idempotency-Key; SDK otherwise generates new keys.",
    "No entry/submission fees; US users eligible, sanctioned regions excluded. API key required; wallet only receives/tracks rewards.",
    "Feedback bounties reward useful agent API feedback or feedback form reports.",
)
