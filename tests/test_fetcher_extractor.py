from unittest.mock import Mock
from arena.fetcher import Fetcher, FetchResult, judge_accessible
from arena.extractor import extract, publish_date
from arena.models import Source


def test_local_extract(config, market, tmp_path):
    path = tmp_path / "page.html"
    path.write_text('<meta property="article:published_time" content="2026-11-18"><p>The civic transit bill passed with 40 votes.</p>')
    source = Source("https://example.test/page", local_path=str(path))
    result = Fetcher(config).fetch(source)
    facts = extract(result, source, market)
    assert facts[0].date == "2026-11-18"
    assert facts[0].stance == "yes"
    assert extract(FetchResult(True, text=""), source, market) == []


def test_metadata():
    assert publish_date('<script type="application/ld+json">{"datePublished":"2026-11-18"}</script>') == "2026-11-18"
    assert publish_date('<time datetime="2026-11-18">today</time>') == "2026-11-18"
    assert publish_date("<html></html>") is None


def test_fetch_error_and_cap(config, tmp_path):
    session = Mock()
    session.get.side_effect = RuntimeError("broken")
    result = Fetcher(config, session).fetch(Source("https://example.test"))
    assert not result.ok and result.error == "broken"
    path = tmp_path / "big.html"
    path.write_text("too big")
    config.max_bytes = 2
    assert not Fetcher(config).fetch(Source("https://example.test", local_path=str(path))).ok
    assert not judge_accessible("https://www.reddit.com/r/test")
    assert not judge_accessible("https://x.com/test")
    assert judge_accessible("https://sec.gov/filing.pdf")
