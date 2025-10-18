from typing import List, Dict, Any
from datetime import datetime, timezone
from urllib.parse import urlparse

from core.search import search_serper
from core.scrape import fetch_page
from core.utils import select_top_chunks
from core.config import get_cfg

def _domain_weight(domain: str, cfg: Dict[str, Any]) -> float:
    if not domain:
        return 1.0
    domain_weights = cfg.get("DOMAIN_WEIGHTS", {})
    if domain in domain_weights:
        return float(domain_weights[domain])
    suffix_defaults = cfg.get("SUFFIX_DEFAULTS", {})
    for suffix, val in suffix_defaults.items():
        if domain.endswith(suffix):
            return float(val)
    return 1.0

def _parse_date(dt: str | None) -> datetime | None:
    if not dt:
        return None
    dt = dt.replace("Z", "")
    fmts = ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d", "%d/%m/%Y")
    for f in fmts:
        try:
            return datetime.strptime(dt, f)
        except Exception:
            continue
    return None

def _recency_weight(published_at: str | None, cfg: Dict[str, Any]) -> float:
    d = _parse_date(published_at)
    if not d:
        return 1.0
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    d_naive = d.replace(tzinfo=None)
    days = (now - d_naive).days
    buckets = cfg.get("RECENCY_BUCKETS", [])
    for item in buckets:
        try:
            limit, w = int(item[0]), float(item[1])
        except Exception:
            continue
        if days <= limit:
            return w
    return float(buckets[-1][1]) if buckets else 1.0

def _coverage_factor(unique_domains: int, cfg: Dict[str, Any]) -> float:
    min_f = float(cfg.get("COVERAGE_MIN_FACTOR", 0.6))
    max_f = float(cfg.get("COVERAGE_MAX_FACTOR", 1.0))
    target = int(cfg.get("COVERAGE_TARGET_DOMAINS", 10))
    if unique_domains <= 0:
        return min_f
    ratio = min(unique_domains / max(target, 1), 1.0)
    return min_f + ratio * (max_f - min_f)

def verify_claim_pipeline(claim: str, search_k: int = 30, fetch_k: int = 12, chunks_per_page: int = 6) -> Dict[str, Any]:
    cfg = get_cfg()

    search_results = search_serper(claim, k=search_k)
    picked = search_results[:fetch_k]

    evidence: List[Dict[str, Any]] = []
    domains_seen = set()

    for res in picked:
        page = fetch_page(res["link"])
        if not page.get("ok"):
            continue

        domains_seen.add(page["domain"])
        top_chunks = select_top_chunks(page["text"], claim, top_n=chunks_per_page)

        evidence.append({
            "url": page["url"],
            "domain": page["domain"],
            "title": page["title"],
            "published_at": page["published_at"],
            "language": page["language"],
            "chunks": top_chunks,
        })

    coverage = _coverage_factor(len(domains_seen), cfg)
    base_score = float(cfg.get("BASE_SCORE", 60.0))
    base = base_score * coverage

    bonus = 0.0
    domain_scale = float(cfg.get("BONUS_DOMAIN_SCALE", 6.0))
    recency_scale = float(cfg.get("BONUS_RECENCY_SCALE", 5.0))
    relevance_scale = float(cfg.get("BONUS_RELEVANCE_SCALE", 5.0))

    for ev in evidence:
        w = _domain_weight(ev["domain"], cfg)
        r = _recency_weight(ev.get("published_at"), cfg)
        rel = min(1.0, len(ev.get("chunks", [])) / max(1, chunks_per_page))

        bonus += domain_scale * (w - 1.0)
        bonus += recency_scale * (r - 1.0)
        bonus += relevance_scale * rel

    raw = max(0.0, min(100.0, base + bonus))

    return {
        "claim": claim,
        "score_heuristic": round(raw, 1),
        "unique_domains": len(domains_seen),
        "coverage_factor": round(coverage, 3),
        "sources": evidence,
        "notes": "Heuristic score from config.json; tune values there."
    }
