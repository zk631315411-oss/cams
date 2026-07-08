"""
Cross-encoder re-rank server for CAMS evidence pipeline.

Maps to WeKnora rerank_server_demo.py + OpenAIReranker.Rerank().
Accepts POST /rerank with {query, documents[]}, returns {results: [{index, score}]}.

Usage:
    pip install torch transformers fastapi uvicorn
    python rerank_server.py

Environment:
    RERANK_MODEL_PATH  — HuggingFace cross-encoder path (default: BAAI/bge-reranker-base)
    RERANK_MAX_LENGTH  — max token length per pair (default: 512)
    RERANK_DEVICE      — torch device (default: cuda if available else cpu)
    RERANK_PORT         — server port (default: 8000)
"""
import gc
import os
import torch
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from typing import List


# --- data models ---

class RerankRequest(BaseModel):
    query: str
    documents: List[str]


class RerankResult(BaseModel):
    index: int
    document: dict  # {"text": str}
    score: float


class RerankResponse(BaseModel):
    results: List[RerankResult]


# --- load model ---

MODEL_PATH = os.environ.get("RERANK_MODEL_PATH", "BAAI/bge-reranker-base")
MAX_LENGTH = int(os.environ.get("RERANK_MAX_LENGTH", "512"))
DEVICE = os.environ.get("RERANK_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")

print(f"Loading cross-encoder: {MODEL_PATH} on {DEVICE}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
model.to(DEVICE)
model.eval()
print("Cross-encoder loaded.")


# --- FastAPI app ---

app = FastAPI(title="CAMS Evidence Reranker", version="1.0.0")


@app.post("/rerank", response_model=RerankResponse)
def rerank(req: RerankRequest):
    if not req.documents:
        return RerankResponse(results=[])

    pairs = [[req.query, doc] for doc in req.documents]
    all_scores = torch.empty(len(pairs), dtype=torch.float32)

    batch_size = 50
    with torch.no_grad():
        for start in range(0, len(pairs), batch_size):
            batch = pairs[start:start + batch_size]
            inputs = tokenizer(
                batch, padding=True, truncation=True,
                return_tensors="pt", max_length=MAX_LENGTH,
            ).to(DEVICE)
            logits = model(**inputs, return_dict=True).logits.view(-1).float()
            all_scores[start:start + len(batch)] = torch.sigmoid(logits).cpu()
            del inputs, logits

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    results = [
        RerankResult(
            index=i,
            document={"text": doc},
            score=round(all_scores[i].item(), 6),
        )
        for i, doc in enumerate(req.documents)
    ]
    results.sort(key=lambda r: r.score, reverse=True)
    return RerankResponse(results=results)


@app.get("/")
def health():
    return {"status": "ok", "model": MODEL_PATH, "device": DEVICE}


if __name__ == "__main__":
    port = int(os.environ.get("RERANK_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
