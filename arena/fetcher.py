from dataclasses import dataclass
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup


@dataclass
class FetchResult:
    ok: bool
    status: int | None = None
    text: str = ""
    content_type: str = ""
    error: str = ""
    judge_fetchable: bool = True
    html: str = ""


def judge_accessible(url):
    host = urlparse(url).hostname or ""
    blocked = ("x.com", "twitter.com", "reddit.com", "wsj.com", "ft.com", "nytimes.com")
    return not any(host == d or host.endswith("." + d) for d in blocked) and not any(
        token in url.lower() for token in ("/login", "/signin", "/paywall"))


class Fetcher:
    def __init__(self, config, session=None):
        self.config = config
        self.session = session or requests.Session()

    def fetch(self, source):
        accessible = judge_accessible(source.url)
        try:
            if source.local_path:
                from pathlib import Path
                raw = Path(source.local_path).read_bytes()
                if len(raw) > self.config.max_bytes:
                    return FetchResult(False, error="size cap", judge_fetchable=accessible)
                html, status, content_type = raw.decode(), 200, "text/html"
            else:
                for attempt in range(self.config.retries + 1):
                    try:
                        with self.session.get(source.url, timeout=self.config.timeout, stream=True,
                                              headers={"User-Agent": self.config.user_agent}) as response:
                            response.raise_for_status()
                            content_type = response.headers.get("Content-Type", "")
                            raw = bytearray()
                            for chunk in response.iter_content(8192):
                                raw.extend(chunk)
                                if len(raw) > self.config.max_bytes:
                                    return FetchResult(False, response.status_code, error="size cap", judge_fetchable=accessible)
                            html, status = raw.decode(response.encoding or "utf-8", errors="replace"), response.status_code
                        break
                    except requests.RequestException:
                        if attempt == self.config.retries:
                            raise
            if "pdf" in content_type:
                return FetchResult(True, status, "", content_type, "PDF fetchable; extraction skipped", accessible)
            soup = BeautifulSoup(html, "html.parser")
            for node in soup(["script", "style", "nav"]):
                node.decompose()
            return FetchResult(True, status, soup.get_text(" ", strip=True), content_type,
                               judge_fetchable=accessible, html=html)
        except Exception as exc:
            return FetchResult(False, error=str(exc), judge_fetchable=accessible)
