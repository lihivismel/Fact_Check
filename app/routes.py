from fastapi import APIRouter, HTTPException
from app.schemas import (
    SearchRequest, SearchResponse, SearchResultItem,
    FetchRequest, FetchResponse,
    VerifyRequest, VerifyResponse
)
from core.search import search_serper, SearchError
from core.scrape import fetch_page
from core.verify import verify_claim_pipeline


router = APIRouter()

# @router.get("/hello")
# def say_hello():
#     return {"message": "Hello from FactCheck!"}

@router.post("/api/search", response_model=SearchResponse)
def api_search(body: SearchRequest):
    try:
        results = search_serper(body.q, k=20)  
    except SearchError as e:
        raise HTTPException(status_code=502, detail=str(e))
    items = [SearchResultItem(**r) for r in results[:12]]
    return SearchResponse(query=body.q, results=items)

@router.post("/api/fetch", response_model=FetchResponse)
def api_fetch(body: FetchRequest):
    page = fetch_page(body.url)
    return FetchResponse(**page)

@router.post("/api/verify", response_model=VerifyResponse)
def api_verify(body: VerifyRequest):
    try:
        result = verify_claim_pipeline(body.claim, search_k=20, fetch_k=10, chunks_per_page=6)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return VerifyResponse(**result)
