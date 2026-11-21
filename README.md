# Agent Arena: Evidence Mining

Conservative, offline-first Python 3.10 entry for the Gensyn / Delphi
[DoraHacks Agent Arena: Evidence Mining](https://dorahacks.io/hackathon/delphi-agent-competition2/detail).
**No results or rewards are claimed.** Default runs use conspicuously fictional
fixtures, not real Delphi markets or evidence. No paid APIs or LLM are needed.

## What it does / architecture

```
CLI → config + rules → markets → search → fetcher → extractor
                                  ↓                 ↓
                            local/DDG/RSS     dated facts (heuristic stance)
                                                    ↓
SQLite state ← stable key ← submission ← one-side policy ← dedup + scoring
      ↓                            ↓
pending / sent / confirmed    mock client OR operator-configured Delphi adapter
```

- `models.py`: Market, Source, Fact, Evidence, Submission dataclasses.
- `rules.py`: source, prizes, timeline, qualification and integrity rules.
- `config.py`: hand-parsed optional .env plus environment overrides.
- `delphi_endpoints.py`: single explicitly **PLACEHOLDER** API configuration.
- `delphi_client.py`: agent headers, same-key retries, timeout reconciliation;
  mock receipts always `mock: true, verdict: not_judged_mock`, never invented rewards.
- `markets.py`, `search.py`: open-cutoff filtering and local, DDG HTML,
  Google News RSS + custom RSS/Atom, or direct URLs.
- `fetcher.py`, `extractor.py`: capped requests, HTML text, date metadata and
  numeric/date sentences with market keyword overlap. PDF fetchable, extraction skipped.
- `dedup.py`, `scoring.py`, `stance.py`: URL-independent fact identity,
  ranking and consistent per-market direction.
- `submission.py`, `state.py`, `agent.py`: short note, links, attachment
  validation, durable SQLite reservations, at most one strongest fact per market/cycle.
- `cli.py`: run-once, loop, markets, status, receipts, feedback, check-config.
- `data/`: clearly fictional sample markets and HTML corpus. Duplicate fact
  across domains, undated facts, X-style sources and both sides included.

### Scoring

Weights in `WEIGHTS` sum to 1:

| Signal | Weight | Rationale |
|---|---:|---|
| Relevance | .30 | Market keyword coverage rather than generic news |
| Recency / datedness | .20 | Explicit recent dates preferred; undated gets .1 signal |
| Credibility | .15 | Government/regulator/exchange/major wire > established news > blogs > unknown |
| Judge accessibility | .10 | Basic-fetchable preferred; quote/snapshot mitigates partially |
| Corroboration | .10 | Independent domains supporting the same fact |
| Novelty | .15 | 1 − highest similarity to known/submitted facts |

Repeats score zero; future or post-cutoff dates score zero. Default minimum .45.
Similarity is token Jaccard with numeric/date agreement; normalized date formats,
punctuation, stopwords and URLs do not create new facts. Batch and saved-state
dedup use threshold .72. Opposite evidence is discarded, not bundled: select the
stronger total-score direction initially, then preserve the saved direction.
Unclear stance is never submitted. Counts alone do not earn rank.

## Install and offline quickstart

Use system Python 3.10 (verified Python 3.10.12), stdlib + requests +
beautifulsoup4, pytest for development:

```sh
python --version
python -m pip install -r requirements-dev.txt .
cp .env.example .env
python -m arena check-config
python -m arena run-once --dry-run --provider local
python -m arena run-once --dry-run --provider local
python -m arena run-once --dry-run --provider local
python -m arena run-once --dry-run --provider local
python -m arena status
python -m pytest -q
```

The installed console command `arena` is equivalent to `python -m arena`.
Use a fresh state path for a fresh demonstration; never delete production state.
The sample dates are Nov 18–20 and the cutoff is Dec 11, 2026; after cutoff no
sample submissions are built. Tests freeze their clock to remain offline/reproducible.
Captured output from the four run-once commands followed by status:

```text
SAMPLE dry-run: civic stance=yes status=not_judged_mock
SAMPLE dry-run: macro stance=yes status=not_judged_mock
SAMPLE dry-run: tech stance=yes status=not_judged_mock
SAMPLE dry-run: sport stance=yes status=not_judged_mock
Cycle complete: 4 submissions built; no rewards claimed.
SAMPLE dry-run: civic stance=yes status=not_judged_mock
SAMPLE dry-run: macro stance=yes status=not_judged_mock
SAMPLE dry-run: tech stance=yes status=not_judged_mock
SAMPLE dry-run: sport stance=yes status=not_judged_mock
Cycle complete: 4 submissions built; no rewards claimed.
SAMPLE dry-run: civic stance=yes status=not_judged_mock
SAMPLE dry-run: macro stance=yes status=not_judged_mock
SAMPLE dry-run: tech stance=yes status=not_judged_mock
SAMPLE dry-run: sport stance=yes status=not_judged_mock
Cycle complete: 4 submissions built; no rewards claimed.
Cycle complete: 0 submissions built; no rewards claimed.
civic: 3/3 slots reserved
macro: 3/3 slots reserved
sport: 3/3 slots reserved
tech: 3/3 slots reserved
Eligibility: 0/10 judged across 0/3 markets (mock receipts excluded)
```

Full offline test summary: `23 passed in 0.41s`.

Outputs are `out/sample-<key>.json` and include `sample: true` plus a fictional
evidence warning. Mock receipts do **not** count toward eligibility.

## Connecting to Delphi on / after 25 November

1. Create a Delphi account; note the **main wallet** receiving rewards/prizes.
2. Register on DoraHacks using that same wallet and agent name. Allow ~12 hours
   for addition. Complete the DoraHacks BUIDL submission yourself.
3. Get the Delphi API key from its API key page when access opens 25 Nov.
   Wallet signing is not the API requirement; the API key is.
4. Read the published one-line prompt, agent guide and starter agent. Only
   **GET /v1/submissions** is publicly FAQ-confirmed. **No other endpoint,
   authentication scheme, header spelling or payload shape is asserted here.**
5. Copy official paths, agent ID/harness/model header names, auth prefix, market
   fields, payload fields, list envelope fields, receipt query and feedback field
   into `arena/delphi_endpoints.py`, or preferably a JSON file referenced by
   `DELPHI_ENDPOINTS_JSON`. The TODO(25 Nov) block is the single schema source.
   Its Authorization Bearer and X-Agent-* names are assumptions, NOT verified API.
6. Set `verified: true` in that JSON only after checking the official schema.
   Example override **shape only**, not working endpoints:

```json
{
  "verified": false,
  "paths": {"markets": "PLACEHOLDER", "submit": "PLACEHOLDER",
            "receipt": "PLACEHOLDER", "feedback": "PLACEHOLDER"},
  "headers": {"authorization": "Authorization", "agent_id": "X-Agent-Id",
              "harness": "X-Agent-Harness", "model": "X-Agent-Model"},
  "auth_prefix": "Bearer ",
  "market_fields": {"id": "id", "question": "question"},
  "payload_fields": {"market_id": "market_id", "note": "note",
                     "links": "links", "attachments": "attachments"},
  "list_fields": {"markets": "markets", "submissions": "submissions"},
  "receipt_id_field": "PLACEHOLDER",
  "feedback_text_field": "PLACEHOLDER"
}
```

All required Market fields must be mapped; the minimal shape above is not a
complete configuration. Response reconciliation currently expects canonical
`idempotency_key`, `verdict`, `mock` fields; adapt the client if official
response formats differ. Receipt polling assumes a configurable query argument
accepting the saved key; if the API uses receipt IDs/path templates, adapt it.
**Live attachment upload intentionally refuses until the official transport is
implemented.** Do not mark schema verified and assume that tests validate Delphi.

Configure private .env (never commit secrets):
`DELPHI_API_KEY`, `DELPHI_API_BASE_URL`, `DELPHI_AGENT_ID`,
`DELPHI_AGENT_HARNESS`, `DELPHI_AGENT_MODEL`, `DELPHI_ENDPOINTS_JSON`,
`ARENA_DRY_RUN=false`, `ARENA_STATE_PATH=live.db`,
`ARENA_SEARCH_PROVIDER=ddg`, `ARENA_USER_AGENT` with a contact.
Live mode requires HTTPS base URL and key. Use a different state database for
sample and live; mixing is refused. Local corpus/sample markets cannot go live.

```sh
python -m arena check-config --live
python -m arena markets --live
python -m arena run-once --live --provider ddg --out out
python -m arena receipts --live
python -m arena feedback --live "Useful bug report with reproducible public details"
```

Never send fabricated feedback or sample evidence. Review the heuristics and
real sources manually before entrusting live submission slots.

Other settings: `ARENA_TIMEOUT` seconds (15), `ARENA_RETRIES` (2),
`ARENA_MAX_BYTES` (2000000 per fetched file/attachment), `ARENA_MIN_SCORE` (.45).
Provider options: `local|ddg|rss|direct`; RSS adds comma-separated `ARENA_FEEDS`,
direct uses comma-separated `ARENA_URLS`. `--markets FILE` accepts the same JSON
envelope as the samples, with `sample: false` for verified real markets.

### Idempotency and caps

A stable SHA-256 key uses agent ID, market ID and sorted normalized fact sets,
not URLs or ordering. It is reserved in SQLite **before** sending. Pending,
sent and confirmed each reserve one of three slots; a crash cannot free a slot.
On restart pending requests reuse saved payload/key; on timeout/connection
failure retries reuse **the same Idempotency-Key** then check GET /v1/submissions.
The official SDK reportedly makes a fresh key per call unless explicitly given
one. Sending without the same key can consume another slot. Do not edit saved
payloads, remove state or re-key a timeout. Submissions cannot be edited/retracted.
Run only one agent process per state DB; the DB atomically enforces slot caps,
but concurrent independent workers are not a supported dedup scheduling model.

## Judge-fetch caveats and safety

Judge fetches each URL once with basic HTTP, not browser/search. X, Reddit,
paywalls/logins usually fail. Paste key text, cite link and attach a screenshot
with URL and date. The builder writes a URL/timestamp/excerpt text snapshot and
warns: this is **not a screenshot**. You must obtain a real screenshot yourself;
no automatic browser/screenshots are provided. PDFs can be read by the judge,
but this agent doesn't extract their text. Max three files; allowed PDF, PNG,
JPG/JPEG, CSV, TXT/MD; size cap is a local conservative cap, not a claimed API cap.
Do not bypass site terms, authentication or paywalls.

## Hosting: competition window (25 Nov–11 Dec, reserve ~18 days)

Use persistent storage and backups for the SQLite DB, .env and output snapshots;
never store production state only in a temporary folder/container filesystem.
An operator-edited systemd unit is under `deploy/arena.service`. Install it with
your system administrator, check paths/Python and private EnvironmentFile,
enable it, and monitor `journalctl -u arena -f`. It defaults to env-configured
mode: leave dry-run on until integration is checked. Restart only on failure;
normal deadline exit must not restart.

Or use tmux/nohup on your host:
```sh
nohup python -m arena loop --interval 60 --until 2026-12-11T17:00:00Z > arena.log 2>&1 &
```
This sleeps minutes between cycles, logs activity, exits at deadline and handles
Ctrl-C gracefully in the foreground. Operator owns uptime, backups and costs.
Do not run multiple loops or use your sample DB for production.

## Verified hackathon rules (read 22 Nov 2026)

Source: linked DoraHacks detail page above; encoded in `arena/rules.py`.

- **$7,250 USD** pool: 1st $3,000; 2nd $2,000; 3rd $1,000; five $250
  useful-feedback bounties (agent API feedback or form, e.g. bugs / inability).
  Evidence rewards are separate.
- All timeline times **17:00 UTC**: registration opened Nov 13; competition,
  instructions, one-line prompt, agent guide, starter agent and first markets
  Nov 25; mining Nov 25–Dec 11 2026; winners Dec 16. New markets every few days.
  DoraHacks submission opens **2026-11-25 17:00 UTC = Nov 26 01:00 UTC+8**;
  deadline **2026-12-11 17:00 UTC = Dec 12 01:00 UTC+8**.
- Read competition market list: odds, close time, evidence cutoff, reward pot.
  Each submission is a short note + links + ≤3 files for **one market**;
  max **3 submissions per agent per market**. Cutoff is submission deadline.
- Dated, sourced facts the forecaster does not know earn most. Already-known
  facts and repeats earn nothing. Repeat means the **fact**, even with different
  URL, quote or language. Opposing evidence on the same market cancels out.
- Receipt with verdict/rationale/judgment reward within minutes. Rewards paid
  **USDC.e to main wallet 24 hours later**; settlement rewards can follow.
  Forecaster researches independently; probabilities via API/UI, market odds fallback.
- Rank by **total judgment + settlement rewards on competition markets**, not
  submission counts; ties go to whoever reached total first.
- Eligibility: **≥10 judged submissions across ≥3 markets**. Prize payments
  in **USDC**, after integrity review, sanctions screening and KYC.
- One wallet per entry; no fee; US users may enter, sanctioned regions may not.
  Real public evidence only: no fabricated facts, copying entrants, judge tricks,
  collusion, confidential data, private individuals' personal data or terms violations.
- Help/feedback community: https://discord.gg/SaCPyB4fZX.

### Eligibility / operator checklist

- [ ] Delphi account, main wallet and API key obtained by you
- [ ] DoraHacks registration: same wallet, agent name, BUIDL entry submitted by you
- [ ] Official Nov 25 adapter schema checked; real sources reviewed
- [ ] Persistent live state and hosting for full window
- [ ] ≥10 actual judged submissions across ≥3 competition markets (see status)
- [ ] KYC / sanctions screening and integrity requirements completed by you

## Limitations

Heuristic extraction/stance is not a forecaster or semantic proof. Negation,
context, multilingual paraphrases and complex resolution criteria need human
review. Lexical dedup cannot guarantee detection of all same-fact paraphrases.
Credibility is a small domain tier list, not truth verification. DDG HTML can
rate-limit/change markup; RSS may link to intermediary pages; respect site terms.
No auto screenshots, OCR, PDF extraction, paid models or private information.
Unknown official API schemas/attachment transport remain explicit adapter work;
there has been **no live Delphi validation**, no deployment and no reward claim.
The tool does not guarantee qualification, accuracy, novelty or profit.

License: MIT, Copyright 2026 ZQ051031.
