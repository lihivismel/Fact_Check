import re
import time
import json
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import trafilatura
from langdetect import detect, LangDetectException

#user agent for preventing blocking
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"

def domain_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""

def fetch_html(url: str, timeout: int = 15) -> str:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout, allow_redirects=True)
    r.raise_for_status()
    return r.text

def extract_published_time(soup: BeautifulSoup) -> str | None:
    candidates = [
        ('meta', {'property': 'article:published_time'}, 'content'),
        ('meta', {'property': 'og:updated_time'}, 'content'),
        ('meta', {'name': 'date'}, 'content'),
        ('meta', {'itemprop': 'datePublished'}, 'content'),
        ('meta', {'property': 'article:modified_time'}, 'content'),
        ('meta', {'name': 'DC.date.issued'}, 'content'),
        ('time', {}, 'datetime'),
    ]
    for tag, attrs, attr_name in candidates:
        el = soup.find(tag, attrs=attrs)
        if el and el.get(attr_name):
            return el.get(attr_name)

    return None

def detect_language(text: str) -> str | None:
    try:
        return detect(text)
    except LangDetectException:
        return None

def extract_readable_text(html: str) -> str:
    txt = trafilatura.extract(html, include_comments=False, include_tables=False) or ""
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt

def fetch_page(url: str) -> dict:
    start = time.time()
    try:
        html = fetch_html(url)
    except requests.RequestException as e:
        return {"url": url, "domain": domain_of(url), "title": "", "published_at": None,
                "language": None, "text": "", "ok": False, "reason": f"network_error: {e}"}

    soup = BeautifulSoup(html, "lxml")

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    ogt = soup.find("meta", {"property": "og:title"})
    if ogt and ogt.get("content"):
        title = ogt["content"].strip() or title

    published_at = extract_published_time(soup)
    text = extract_readable_text(html)

    if len(text) < 400:  
        return {"url": url, "domain": domain_of(url), "title": title, "published_at": published_at,
                "language": None, "text": "", "ok": False, "reason": "too_short"}

    language = detect_language(text)

    return {
        "url": url,
        "domain": domain_of(url),
        "title": title,
        "published_at": published_at,
        "language": language,
        "text": text,
        "ok": True,
        "reason": None,
        "elapsed_sec": round(time.time() - start, 2),
    }
