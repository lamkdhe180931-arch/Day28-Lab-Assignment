# api-gateway/main.py
from fastapi import FastAPI, HTTPException, Request
from prometheus_fastapi_instrumentator import Instrumentator
import httpx, os, time

app = FastAPI(title="AI Platform API Gateway")
Instrumentator().instrument(app).expose(app)  # Integration 9: Prometheus

LOCAL_DEMO_MODE = os.environ.get("LOCAL_DEMO_MODE", "").lower() in {"1", "true", "yes"}
VLLM_URL = None if LOCAL_DEMO_MODE else (os.environ.get("VLLM_URL") or os.environ.get("VLLM_NGROK_URL"))
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4"


async def search_context(embedding: list[float]) -> list:
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            search_resp = await client.post(f"{QDRANT_URL}/collections/documents/points/search", json={
                "vector": embedding,
                "limit": 3
            })
            if search_resp.status_code >= 400:
                return []
            return search_resp.json().get("result", [])
    except httpx.HTTPError:
        return []


async def call_vllm(prompt: str) -> tuple[str, str]:
    if not VLLM_URL:
        return (
            "Local demo answer: platform engineering is the practice of combining "
            "infrastructure, automation, observability, and developer workflows into "
            "a reliable internal platform. This lab runs in local fallback mode "
            "because Kaggle GPU serving is not configured.",
            "local-demo-fallback",
        )

    async with httpx.AsyncClient(timeout=30) as client:
        llm_resp = await client.post(f"{VLLM_URL}/v1/chat/completions", json={
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}]
        })
        llm_resp.raise_for_status()
        result = llm_resp.json()
        return result["choices"][0]["message"]["content"], result.get("model", MODEL_NAME)

@app.post("/api/v1/chat")
async def chat(request: Request):
    body = await request.json()
    query = body.get("query")
    if not query:
        raise HTTPException(status_code=422, detail="query is required")

    start = time.time()

    # 1. Vector search
    context = await search_context(body.get("embedding", [0.0] * 384))

    # 2. LLM inference
    prompt = f"Context: {context}\n\nQuery: {query}"
    answer, model = await call_vllm(prompt)
    latency = (time.time() - start) * 1000

    return {
        "answer": answer,
        "latency_ms": round(latency, 2),
        "model": model
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "mode": "kaggle-vllm" if VLLM_URL else "local-demo",
    }
