import importlib.util
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient


def load_app_without_vllm_url():
    os.environ.pop("VLLM_URL", None)
    os.environ.pop("LOCAL_DEMO_MODE", None)
    os.environ["QDRANT_URL"] = "http://127.0.0.1:1"
    sys.modules.pop("main", None)

    module_path = Path(__file__).with_name("main.py")
    spec = importlib.util.spec_from_file_location("main", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app


def test_chat_uses_local_demo_response_when_vllm_url_missing():
    client = TestClient(load_app_without_vllm_url())

    response = client.post(
        "/api/v1/chat",
        json={"query": "What is platform engineering?", "embedding": [0.1] * 384},
    )

    assert response.status_code == 200
    body = response.json()
    assert "answer" in body
    assert len(body["answer"]) > 10
    assert body["model"] == "local-demo-fallback"


def test_chat_rejects_missing_query():
    client = TestClient(load_app_without_vllm_url())

    response = client.post("/api/v1/chat", json={})

    assert response.status_code == 422


def test_local_demo_mode_overrides_vllm_url():
    os.environ["VLLM_URL"] = "https://example.invalid"
    os.environ["LOCAL_DEMO_MODE"] = "true"
    os.environ["QDRANT_URL"] = "http://127.0.0.1:1"
    sys.modules.pop("main", None)

    module_path = Path(__file__).with_name("main.py")
    spec = importlib.util.spec_from_file_location("main", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    client = TestClient(module.app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["mode"] == "local-demo"
