"""Search providers return public URLs; local fixtures never use the network."""
import os
from pathlib import Path
from urllib.parse import quote, urlparse, parse_qs
from xml.etree import ElementTree
import requests
from bs4 import BeautifulSoup
from .markets import DATA
from .models import Source


class SearchProvider:
    def search(self, query):
        raise NotImplementedError


class LocalCorpusProvider(SearchProvider):
    def search(self, query):
        result = []
        for path in sorted((DATA / "sample_corpus").glob("*.html")):
            soup = BeautifulSoup(path.read_text(), "html.parser")
            result.append(Source(soup.find("link", rel="canonical")["href"], path.stem, str(path)))
        return result


class DirectURLProvider(SearchProvider):
    def search(self, query):
        return [Source(url.strip()) for url in os.getenv("ARENA_URLS", "").split(",") if url.strip()]


class DuckDuckGoProvider(SearchProvider):
    def search(self, query):
        response = requests.get("https://html.duckduckgo.com/html/", params={"q": query}, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        result = []
        for node in soup.select("a.result__a")[:10]:
            href = node.get("href", "")
            href = parse_qs(urlparse(href).query).get("uddg", [href])[0]
            if href.startswith(("https://", "http://")):
                result.append(Source(href, node.get_text()))
        return result


class RSSProvider(SearchProvider):
    def search(self, query):
        urls = ["https://news.google.com/rss/search?q=" + quote(query)]
        urls += [u for u in os.getenv("ARENA_FEEDS", "").split(",") if u]
        result = []
        for url in urls:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            root = ElementTree.fromstring(response.content)
            for item in root.findall(".//item"):
                if item.findtext("link"):
                    result.append(Source(item.findtext("link"), item.findtext("title", "")))
            for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
                for link in entry.findall("{http://www.w3.org/2005/Atom}link"):
                    if link.get("rel", "alternate") == "alternate" and link.get("href"):
                        result.append(Source(link.get("href")))
        return result[:20]


REGISTRY = {"local": LocalCorpusProvider, "ddg": DuckDuckGoProvider,
            "rss": RSSProvider, "direct": DirectURLProvider}
