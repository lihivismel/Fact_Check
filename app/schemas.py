from pydantic import BaseModel, Field
from typing import Optional, List

class VerifyRequest(BaseModel):
    claim: str = Field(..., description="Claim to verify")

class EvidenceItem(BaseModel):
    url: str
    domain: str
    title: str
    published_at: Optional[str] = None
    language: Optional[str] = None
    chunks: List[str]

    nli_evaluated: Optional[bool] = None
    nli_max_entail: Optional[float] = None
    nli_max_contra: Optional[float] = None
    nli_best_ent_chunk: Optional[str] = None
    nli_best_contra_chunk: Optional[str] = None

class VerifyResponse(BaseModel):
    claim: str
    score: float
    unique_domains: int
    coverage_bucket: Optional[str] = None
    sources: List[EvidenceItem]
    notes: Optional[str] = None
