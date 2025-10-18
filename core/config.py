import json
import os
from typing import Any, Dict

_DEFAULTS: Dict[str, Any] = {
    "BASE_SCORE": 60.0,
    "COVERAGE_TARGET_DOMAINS": 10,
    "COVERAGE_MIN_FACTOR": 0.6,
    "COVERAGE_MAX_FACTOR": 1.0,
    "BONUS_DOMAIN_SCALE": 6.0,
    "BONUS_RECENCY_SCALE": 5.0,
    "BONUS_RELEVANCE_SCALE": 5.0,
    "RECENCY_BUCKETS": [
        [90, 1.15],
        [365, 1.10],
        [1095, 1.00],
        [3650, 0.95],
    ],
    "SUFFIX_DEFAULTS": {},
    "DOMAIN_WEIGHTS": {}
}

def _load_from_disk(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    out = dict(_DEFAULTS)
    out.update(data or {})
    return out

def get_cfg() -> Dict[str, Any]:
    """
    Loads configuration from JSON file each call.
    Path is taken from env FACTCHECK_CONFIG or defaults to ./config.json
    """
    path = os.getenv("FACTCHECK_CONFIG", "config.json")
    try:
        return _load_from_disk(path)
    except Exception:
        return dict(_DEFAULTS)
