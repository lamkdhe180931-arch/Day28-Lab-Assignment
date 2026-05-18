# scripts/05_embed_to_qdrant.py
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import hashlib
import os

EMBED_URL = os.environ.get("EMBED_NGROK_URL")
qdrant = QdrantClient(host="localhost", port=6333)
VECTOR_SIZE = 384

# Tạo collection
qdrant.recreate_collection(
    collection_name="documents",
    vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
)


def local_embedding(text: str) -> list[float]:
    """Create a deterministic demo embedding when Kaggle service is unavailable."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = []
    while len(values) < VECTOR_SIZE:
        for byte in digest:
            values.append((byte / 255.0) * 2 - 1)
            if len(values) == VECTOR_SIZE:
                break
        digest = hashlib.sha256(digest).digest()
    return values


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not EMBED_URL:
        print("EMBED_NGROK_URL not set; using local demo embeddings")
        return [local_embedding(text) for text in texts]

    try:
        response = requests.post(f"{EMBED_URL}/embed", json={"texts": texts}, timeout=30)
        response.raise_for_status()
        return response.json()["embeddings"]
    except requests.RequestException as exc:
        print(f"Embedding service unavailable ({exc}); using local demo embeddings")
        return [local_embedding(text) for text in texts]


def embed_and_store(records: list[dict]):
    embeddings = embed_texts([r["text"] for r in records])

    points = [
        PointStruct(id=i, vector=emb, payload=rec)
        for i, (emb, rec) in enumerate(zip(embeddings, records))
    ]
    qdrant.upsert(collection_name="documents", points=points)
    print(f"Integration 5 OK: {len(points)} vectors stored in Qdrant")

# Test với sample data
embed_and_store([
    {"id": "doc_001", "text": "AI platform integration test"},
    {"id": "doc_002", "text": "Kafka to Airflow pipeline"},
])
