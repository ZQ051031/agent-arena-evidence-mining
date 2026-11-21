"""Weights prioritize relevant, recent new facts, not volume.
Relevance .30; dated recency .20; domain credibility .15; basic-fetch
accessibility .10; independent-domain corroboration .10; novelty .15.
Undated facts get low recency, repeats zero. Future/post-cutoff dates zero.
"""
from .dedup import normalize, similarity, is_repeat
from .models import parse_time, utcnow

WEIGHTS = dict(relevance=.30, recency=.20, credibility=.15,
               accessibility=.10, corroboration=.10, novelty=.15)


def credibility(domain):
    if domain.endswith((".gov", ".gov.uk")) or domain in ("reuters.com", "apnews.com", "sec.gov", "cmegroup.com", "coinbase.com"):
        return 1.0
    if domain in ("bbc.com", "theguardian.com", "bloomberg.com"):
        return .8
    if "blog" in domain:
        return .35
    return .25


def score_fact(fact, market, known, peers=(), now=None, has_snapshot=False):
    now = now or utcnow()
    if is_repeat(fact.text, known):
        return 0.0
    recency = .1
    if fact.date:
        try:
            date = parse_time(fact.date)
        except ValueError:
            return 0.0
        if date > now or date > parse_time(market.evidence_cutoff):
            return 0.0
        recency = max(.2, 1 - (now - date).days / 365)
    keywords = normalize(" ".join(market.keywords))
    relevance = len(normalize(fact.text) & keywords) / max(1, len(keywords))
    domains = {f.domain for f in peers if similarity(f.text, fact.text) >= .72}
    parts = dict(relevance=min(1, relevance), recency=recency, credibility=credibility(fact.domain),
                 accessibility=1 if fact.judge_fetchable else (.5 if has_snapshot else 0),
                 corroboration=min(1, max(0, len(domains) - 1) / 2),
                 novelty=1 - max((similarity(fact.text, x) for x in known), default=0))
    return sum(WEIGHTS[k] * value for k, value in parts.items())
