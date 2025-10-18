from pydantic import BaseModel, Field
from typing import Optional, List

class SearchRequest(BaseModel):
    q: str = Field(..., description="Search query")

class SearchResultItem(BaseModel):
    title: str
    link: str
    snippet: str
    date: Optional[str] = None
    source: Optional[str] = None
    domain: Optional[str] = None
    rank: int

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]

class FetchRequest(BaseModel):
    url: str

class FetchResponse(BaseModel):
    url: str
    domain: str
    title: str
    published_at: str | None
    language: str | None
    text: str
    ok: bool
    reason: str | None
    elapsed_sec: float | None = None


class VerifyRequest(BaseModel):
    claim: str = Field(..., description="Claim to verify")

class EvidenceItem(BaseModel):
    url: str
    domain: str
    title: str
    published_at: Optional[str] = None
    language: Optional[str] = None
    chunks: List[str]

class VerifyResponse(BaseModel):
    claim: str
    score_heuristic: float
    unique_domains: int
    sources: List[EvidenceItem]
    notes: Optional[str] = None
