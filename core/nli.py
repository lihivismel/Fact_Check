from __future__ import annotations
import os
import math
from typing import Dict, Tuple
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from core.config import get_cfg

_model = None
_tokenizer = None
_label_map = None
_device = "cpu"

def _pick_device(cfg: Dict) -> str:
    pref = str(cfg.get("NLI_DEVICE", "auto")).lower()
    if pref == "cpu":
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"

def load_nli() -> None:
    global _model, _tokenizer, _label_map, _device
    if _model is not None:
        return
    cfg = get_cfg()
    name = cfg.get("NLI_MODEL_NAME", "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
    _device = _pick_device(cfg)
    _tokenizer = AutoTokenizer.from_pretrained(name)
    _model = AutoModelForSequenceClassification.from_pretrained(name)
    _model.to(_device)
    # build label map dynamically
    id2label = _model.config.id2label
    label2id = {v.lower(): k for k, v in id2label.items()}
    # normalize keys
    def find(key: str) -> int:
        key = key.lower()
        for cand in (key, f"mnli_{key}", f"xnli_{key}"):
            if cand in label2id:
                return label2id[cand]
        raise RuntimeError(f"Label {key} not found in model labels: {list(label2id.keys())}")
    _label_map = {
        "entailment": find("entailment"),
        "neutral": find("neutral"),
        "contradiction": find("contradiction"),
    }

def nli_scores(premise: str, hypothesis: str) -> Dict[str, float]:
    """
    Returns probabilities for entailment/neutral/contradiction in [0,1].
    Premise = evidence chunk; Hypothesis = user claim.
    """
    load_nli()
    inputs = _tokenizer(
        premise,
        hypothesis,
        truncation=True,
        padding=False,
        max_length=512,
        return_tensors="pt",
    )
    inputs = {k: v.to(_device) for k, v in inputs.items()}
    with torch.no_grad():
        logits = _model(**inputs).logits[0]
    probs = torch.softmax(logits, dim=-1).detach().cpu().numpy().tolist()
    out = {}
    for name, idx in _label_map.items():
        out[name] = float(probs[idx])
    return out

def nli_support_contradict(premise: str, hypothesis: str) -> Tuple[float, float, float]:
    s = nli_scores(premise, hypothesis)
    return s.get("entailment", 0.0), s.get("contradiction", 0.0), s.get("neutral", 0.0)
