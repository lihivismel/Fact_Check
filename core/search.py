import os
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()
_SERPER_KEY = os.getenv("SERPER_API_KEY")

class SearchError(Exception):
    pass

def _domain_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""

def search_serper(query: str, k: int = 8) -> list[dict]:
    if not _SERPER_KEY:
        raise SearchError("Missing SERPER_API_KEY in .env")

    headers = {"X-API-KEY": _SERPER_KEY}
    payload = {"q": query}

    try:
        r = requests.post("https://google.serper.dev/search", headers=headers, json=payload, timeout=15)
    except requests.RequestException as e:
        raise SearchError(f"Network error: {e}") from e

    if r.status_code != 200:
        raise SearchError(f"Serper error {r.status_code}: {r.text}")

    data = r.json()
    organic = data.get("organic", []) or []

    results = []
    for i, item in enumerate(organic[: k * 2], start=1):
        link = item.get("link") or ""
        results.append({
            "title": item.get("title", ""),
            "link": link,
            "snippet": item.get("snippet", ""),
            "date": item.get("date", None),
            "source": item.get("source", _domain_of(link)),
            "domain": _domain_of(link),
            "rank": i
        })

    unique_by_domain = {}
    for res in results:
        d = res["domain"]
        if d and d not in unique_by_domain:
            unique_by_domain[d] = res

    deduped = list(unique_by_domain.values())
    deduped.sort(key=lambda x: x["rank"])
    return deduped[:k]
