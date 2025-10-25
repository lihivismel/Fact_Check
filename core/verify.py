from typing import List, Dict, Any
from datetime import datetime, timezone

from core.search import search_serper
from core.scrape import fetch_page
from core.utils import select_top_chunks, keywords_from_claim, score_chunk_by_keywords
from core.config import get_cfg
from core.nli import nli_support_contradict

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

def _domain_weight(domain: str, cfg: Dict[str, Any]) -> float:
    if not domain:
        return 1.0
    dmap = cfg.get("DOMAIN_WEIGHTS", {})
    if domain in dmap:
        return float(dmap[domain])
    for suffix, val in cfg.get("SUFFIX_DEFAULTS", {}).items():
        if domain.endswith(suffix):
            return float(val)
    return 1.0

def _recency_weight(published_at: str | None, cfg: Dict[str, Any]) -> float:
    d = _parse_date(published_at)
    if not d:
        return 1.0
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    d_naive = d.replace(tzinfo=None)
    days = (now - d_naive).days
    for item in cfg.get("RECENCY_BUCKETS", []):
        try:
            limit, w = int(item[0]), float(item[1])
        except Exception:
            continue
        if days <= limit:
            return w
    buckets = cfg.get("RECENCY_BUCKETS", [])
    return float(buckets[-1][1]) if buckets else 1.0

def _coverage_bucket_factor(unique_domains: int, cfg: Dict[str, Any]) -> tuple[float, str]:
    low_th  = int(cfg.get("COVERAGE_LOW_THRESHOLD", 4))
    high_th = int(cfg.get("COVERAGE_HIGH_THRESHOLD", 8))
    low_f   = float(cfg.get("COVERAGE_LOW_FACTOR", 0.5))
    mid_f   = float(cfg.get("COVERAGE_MID_FACTOR", 1.0))
    high_f  = float(cfg.get("COVERAGE_HIGH_FACTOR", 1.1))
    if unique_domains < low_th:
        return low_f, "low"
    if unique_domains <= high_th:
        return mid_f, "mid"
    return high_f, "high"

def _heuristic_score(evidence: List[Dict[str, Any]], cfg: Dict[str, Any]) -> tuple[float, float, str]:
    domains_seen = {ev["domain"] for ev in evidence}
    factor, bucket = _coverage_bucket_factor(len(domains_seen), cfg)
    base = float(cfg.get("BASE_SCORE", 45.0)) * factor

    bonus = 0.0
    dscale = float(cfg.get("BONUS_DOMAIN_SCALE", 6.0))
    rscale = float(cfg.get("BONUS_RECENCY_SCALE", 5.0))

    dbg = bool(cfg.get("DEBUG_NUMERIC_ONLY", False))
    if dbg:
        print(f"[HEUR] domains={len(domains_seen)} bucket={bucket} factor={factor}")

    for ev in evidence:
        w = _domain_weight(ev["domain"], cfg)
        r = _recency_weight(ev.get("published_at"), cfg)
        bonus += dscale * (w - 1.0)
        bonus += rscale * (r - 1.0)
        if dbg:
            # numeric-only: print domain and numeric weights
            print(f"[HEUR] domain={ev['domain']} w={w:.2f} r={r:.2f}")

    raw = max(0.0, min(100.0, base + bonus))
    if dbg:
        print(f"[HEUR] base={base:.1f} bonus={bonus:.1f} total={raw:.1f}")
    return raw, factor, bucket

def verify_claim_pipeline(
    claim: str,
    search_k: int = 20,
    fetch_k: int = 6,
    chunks_per_page: int = 3
) -> Dict[str, Any]:
    cfg = get_cfg()
    dbg = bool(cfg.get("DEBUG_NUMERIC_ONLY", False))
    if dbg:
        print(f"[CLAIM] {claim}")

    # 1. search
    search_results = search_serper(claim, k=search_k)
    picked = search_results[:fetch_k]
    if dbg:
        print(f"[SEARCH] total={len(search_results)} picked={len(picked)}")

    evidence: List[Dict[str, Any]] = []
    all_chunks: List[Dict[str, Any]] = []

    # 2. keywords for pre-filter
    kws = keywords_from_claim(claim)
    kw_min = int(cfg.get("NLI_MIN_KEYWORD_MATCH", 2))
    if dbg:
        print(f"[KWS] {kws} min_match={kw_min}")

    # 3. fetch pages + take top chunks
    for res in picked:
        page = fetch_page(res["link"])
        if not page.get("ok"):
            continue

        chunks = select_top_chunks(page["text"], claim, top_n=chunks_per_page)

        ev = {
            "url": page["url"],
            "domain": page["domain"],
            "title": page["title"],
            "published_at": page["published_at"],
            "language": page["language"],
            "chunks": chunks
        }
        evidence.append(ev)

        # keyword gate for NLI
        for ch in chunks:
            score = score_chunk_by_keywords(ch, kws)
            if score >= kw_min:
                all_chunks.append({
                    "domain": page["domain"],
                    "url": page["url"],
                    "chunk": ch
                })
            elif dbg:
                print(f"[FILTER] domain={page['domain']} kw_score={score} -> skip")

    if dbg:
        print(f"[CHUNKS] eligible_for_nli={len(all_chunks)}")

    # 4. safety cap on NLI volume
    max_total = int(cfg.get("NLI_MAX_CHUNKS_TOTAL", 30))
    if len(all_chunks) > max_total:
        if dbg:
            print(f"[LIMIT] chunks {len(all_chunks)} -> {max_total}")
        all_chunks = all_chunks[:max_total]

    # 5. run NLI and aggregate per source (url)
    per_source: Dict[str, Dict[str, Any]] = {}
    for item in all_chunks:
        ent, contra, neut = nli_support_contradict(item["chunk"], claim)

        u = item["url"]
        rec = per_source.setdefault(u, {
            "domain": item["domain"],
            "url": u,
            "max_entail": 0.0,
            "max_contra": 0.0,
            "neutral": 0.0,
            "nli_evaluated": True,
            "best_ent_chunk": "",
            "best_contra_chunk": ""
        })

        if ent > rec["max_entail"]:
            rec["max_entail"] = ent
            rec["best_ent_chunk"] = item["chunk"]

        if contra > rec["max_contra"]:
            rec["max_contra"] = contra
            rec["best_contra_chunk"] = item["chunk"]

        rec["neutral"] = max(rec["neutral"], neut)

        if dbg:
            print(f"[NLI] domain={item['domain']} entail={ent:.3f} contra={contra:.3f} neut={neut:.3f}")

    # 6. add sources we saw but didn't evaluate via NLI
    evaluated_urls = set(per_source.keys())
    for ev in evidence:
        if ev["url"] not in evaluated_urls:
            per_source[ev["url"]] = {
                "domain": ev["domain"],
                "url": ev["url"],
                "max_entail": 0.0,
                "max_contra": 0.0,
                "neutral": 0.0,
                "best_ent_chunk": "",
                "best_contra_chunk": "",
                "nli_evaluated": False,
                "nli_included": False
            }
            if dbg:
                print(f"[NLI] domain={ev['domain']} not_evaluated")

    # 7. heuristic score (authority, coverage, recency...)
    score_h, coverage_factor, coverage_bucket = _heuristic_score(evidence, cfg)

    # 8. NLI scoring with stricter filtering
    supp_scale   = float(cfg.get("NLI_SUPPORT_SCALE", 80.0))
    cont_pen     = float(cfg.get("NLI_CONTRADICT_PENALTY", 50.0))
    neutral_as   = float(cfg.get("INCLUDE_NEUTRAL_AS", 0.0))
    min_conf     = float(cfg.get("NLI_MIN_SOURCE_CONF", 0.20))
    min_import   = float(cfg.get("NLI_SOURCE_MIN_IMPORTANCE", 0.4))

    nli_vals: List[float] = []

    for rec in per_source.values():
        rec["nli_included"] = False

        if not rec["nli_evaluated"]:
            # cannot use this source in NLI score
            continue

        # gate 1: require at least one strong side
        if max(rec["max_entail"], rec["max_contra"]) < min_conf:
            if dbg:
                print(
                    f"[SRC] domain={rec['domain']} skipped(min_conf) "
                    f"entail={rec['max_entail']:.2f} contra={rec['max_contra']:.2f}"
                )
            continue

        # gate 2: require overall importance
        importance = rec["max_entail"] + rec["max_contra"]
        if importance < min_import:
            if dbg:
                print(
                    f"[SRC] domain={rec['domain']} skipped(importance<{min_import}) "
                    f"entail={rec['max_entail']:.2f} contra={rec['max_contra']:.2f} sum={importance:.2f}"
                )
            continue

        # passed both gates, include in NLI score
        s_val = supp_scale * rec["max_entail"] - cont_pen * rec["max_contra"]
        if neutral_as != 0.0:
            s_val += neutral_as * rec["neutral"]

        rec["nli_included"] = True
        rec["nli_score_component"] = s_val  # save for later debugging/sorting
        nli_vals.append(s_val)

        if dbg:
            print(
                f"[SRC] domain={rec['domain']} included "
                f"entail={rec['max_entail']:.2f} contra={rec['max_contra']:.2f} s={s_val:.1f}"
            )

    # 9. compute aggregate NLI score
    if nli_vals:
        nli_score = max(0.0, min(100.0, sum(nli_vals) / len(nli_vals)))
    else:
        nli_score = 0.0

    # final blend
    alpha = float(cfg.get("FINAL_BLEND_ALPHA", 0.75))
    final_score = (1 - alpha) * score_h + alpha * nli_score
    final_score = max(0.0, min(100.0, final_score))

    if dbg:
        print(f"[NLI_SUM] n={len(nli_vals)} mean={nli_score:.1f}")
        print(
            f"[FINAL] alpha={alpha} heuristic={score_h:.1f} "
            f"nli={nli_score:.1f} -> score={final_score:.1f}"
        )

    # 10. build list for frontend.
    # We only want sources that actually passed nli_included == True.
    # After that, we'll RANK them and take only top 5 for the UI.
    excerpt_thr = float(cfg.get("NLI_EXCERPT_THRESHOLD", 0.65))

    enriched_sources_full: List[Dict[str, Any]] = []
    for ev in evidence:
        rec = per_source[ev["url"]]

        if not rec.get("nli_included", False):
            # hide weak/irrelevant sources completely
            continue

        ent_ex = rec["best_ent_chunk"] if rec["max_entail"] >= excerpt_thr else ""
        con_ex = rec["best_contra_chunk"] if rec["max_contra"] >= excerpt_thr else ""

        enriched_sources_full.append({
            **ev,
            "nli_evaluated": rec["nli_evaluated"],
            "nli_included": rec.get("nli_included", False),
            "nli_max_entail": round(rec["max_entail"], 3),
            "nli_max_contra": round(rec["max_contra"], 3),
            "nli_best_ent_chunk": ent_ex,
            "nli_best_contra_chunk": con_ex,
            "nli_score_component": rec.get("nli_score_component", 0.0),
            "domain_bonus": float(cfg.get("BONUS_DOMAINS", {}).get(rec["domain"], 1.0))
        })

    # 11. sort sources for presentation priority:
    #    1) higher domain_bonus first (authoritative domains first)
    #    2) higher nli_score_component (stronger evidence)
    enriched_sources_full.sort(
        key=lambda s: (
            s.get("domain_bonus", 1.0),
            s.get("nli_score_component", 0.0)
        ),
        reverse=True
    )

    # 12. take top 5 only for the frontend
    enriched_top5 = enriched_sources_full[:5]

    return {
        "claim": claim,
        "score": round(final_score, 1),
        "unique_domains": len({ev["domain"] for ev in evidence}),
        "coverage_bucket": coverage_bucket,
        "sources": enriched_top5,
        "notes": (
            "Only top sources shown (ranked by domain authority + evidence strength). "
            "Full set used internally for scoring."
        )
    }
