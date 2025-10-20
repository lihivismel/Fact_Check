import re
from collections import Counter

def split_to_chunks(text: str, max_chars: int = 500) -> list[str]:
    sents = re.split(r'(?<=[.!?])\s+|\n+', text)
    chunks, buf = [], ""
    for s in sents:
        s = s.strip()
        if not s:
            continue
        if len(buf) + len(s) <= max_chars:
            buf = (buf + " " + s).strip()
        else:
            if buf:
                chunks.append(buf)
            buf = s
    if buf:
        chunks.append(buf)
    return chunks

def keywords_from_claim(claim: str) -> list[str]:
    claim_lc = claim.lower()
    tokens = re.findall(r"[a-zA-Zא-ת]+", claim_lc)
    stop = set(["של", "על", "עם", "אם", "את", "זה", "זו", "that", "the", "and", "or", "is", "are"])
    kws = [t for t in tokens if t not in stop and len(t) > 1]
    freq = Counter(kws)
    return [w for w, _ in freq.most_common(10)]

def score_chunk_by_keywords(chunk: str, keywords: list[str]) -> int:
    c = chunk.lower()
    score = 0
    for kw in keywords:
        if kw in c:
            score += 1
    return score

def select_top_chunks(text: str, claim: str, top_n: int = 8) -> list[str]:
    chunks = split_to_chunks(text, max_chars=500)
    kws = keywords_from_claim(claim)
    scored = [(score_chunk_by_keywords(ch, kws), ch) for ch in chunks]
    scored.sort(key=lambda x: x[0], reverse=True)
    filtered = [ch for sc, ch in scored if sc > 0]
    return filtered[:top_n] if filtered else chunks[:top_n]
