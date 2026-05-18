# Lab #28 - Full Platform Integration Sprint

## Thong Tin Demo

Demo trien khai AI platform theo kien truc hybrid-ready, trong do local stack chay bang Docker Compose va model serving duoc abstract qua API Gateway. Khi khong co GPU endpoint, API Gateway su dung local fallback de van dam bao duoc full luong end-to-end: data ingestion, feature store, vector store, gateway, metrics va dashboard.

## Kien Truc

```text
Kafka -> Prefect -> Delta Lake/Parquet -> Redis Feature Store
                         |
                         v
                    Qdrant Vector Store
                         |
                         v
                FastAPI API Gateway
                         |
                         v
              Prometheus -> Grafana
```

Thanh phan:
- Kafka: nhan event `data.raw`.
- Prefect: orchestration cho pipeline Kafka to Delta.
- Delta Lake/Parquet: luu batch data dang parquet.
- Redis: online feature store.
- Qdrant: vector database cho document embeddings.
- FastAPI Gateway: endpoint `/health`, `/api/v1/chat`, `/metrics`.
- Prometheus: scrape metrics tu API Gateway.
- Grafana: dashboard/health monitoring.

## Cach Chay

```bash
cp .env.example .env
docker compose up -d --build

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-local.txt

python scripts/quick_local_demo.py
pytest smoke-tests/ -v
python scripts/production_readiness_check.py
```

## Environment

```env
LOCAL_DEMO_MODE=true
VLLM_NGROK_URL=
EMBED_NGROK_URL=
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=lab28-platform
```

## Ket Qua API Gateway

Health check:

```bash
curl http://localhost:8000/health
```

Ket qua:

```json
{
  "status": "ok",
  "mode": "local-demo"
}
```

Chat request:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"What is platform engineering?","embedding":[0.1,0.1,0.1]}'
```

Ket qua mau:

```json
{
  "answer": "Local demo answer: platform engineering is the practice of combining infrastructure, automation, observability, and developer workflows into a reliable internal platform.",
  "latency_ms": 42.18,
  "model": "local-demo-fallback"
}
```

## Ket Qua Smoke Tests

```text
============================= test session starts =============================
collected 7 items

smoke-tests/test_e2e.py::TestHappyPath::test_full_inference_returns_200 PASSED
smoke-tests/test_e2e.py::TestHappyPath::test_health_check_passes PASSED
smoke-tests/test_e2e.py::TestDataIngestion::test_kafka_ingest_and_qdrant_store PASSED
smoke-tests/test_e2e.py::TestObservability::test_prometheus_scrapes_api_gateway PASSED
smoke-tests/test_e2e.py::TestObservability::test_grafana_dashboard_accessible PASSED
smoke-tests/test_e2e.py::TestFailurePath::test_invalid_request_returns_422 PASSED
smoke-tests/test_e2e.py::TestFeatureStore::test_feast_redis_has_features PASSED

============================== 7 passed in 18.42s =============================
```

## Production Readiness

```text
=== RELIABILITY ===
  [PASS] Health check endpoint
  [PASS] API Gateway responds

=== OBSERVABILITY ===
  [PASS] Prometheus up
  [PASS] Grafana up
  [PASS] Metrics endpoint exposed

=== SECURITY ===
  [PASS] Unauthorized request rejected

=== VECTOR STORE ===
  [PASS] Qdrant healthy
  [PASS] Collection exists

=== FEATURE STORE ===
  [PASS] Redis reachable

=== KAFKA ===
  [PASS] Kafka topics exist

========================================
Production Readiness Score: 10/10 = 100%
Target: >80% - Status: READY
```

## 10 Integration Points

| # | Integration | Trang Thai |
|---|-------------|------------|
| 1 | Data ingestion to Kafka | Hoan thanh |
| 2 | Kafka to Prefect pipeline | Hoan thanh |
| 3 | Prefect to Delta/Parquet | Hoan thanh |
| 4 | Delta/Parquet to Redis feature store | Hoan thanh |
| 5 | Data to Qdrant vector store | Hoan thanh |
| 6 | Model serving abstraction | Hoan thanh |
| 7 | API Gateway to model endpoint/fallback | Hoan thanh |
| 8 | API Gateway to Qdrant retrieval | Hoan thanh |
| 9 | API Gateway metrics to Prometheus | Hoan thanh |
| 10 | Grafana observability dashboard | Hoan thanh |

## Screenshots Can Co

- `screenshots/api_gateway.png`: ket qua `curl http://localhost:8000/health`.
- `screenshots/grafana_dashboard.png`: Grafana health/dashboard tai `http://localhost:3000`.
- `screenshots/prometheus.png`: Prometheus target/query tai `http://localhost:9090`.
- `screenshots/qdrant.png`: Qdrant collection `documents`.
- `smoke_tests_results.png`: ket qua `pytest smoke-tests/ -v`.
- `production_readiness.png`: readiness score.

## Cau Hoi 1: Trade-offs Trong Kien Truc

Kien truc tach rieng ingestion, orchestration, feature store, vector store va serving gateway. Cach nay tang maintainability vi tung component co trach nhiem ro rang va co the thay the doc lap. Trade-off la he thong co nhieu service nen setup phuc tap hon monolith, nhung doi lai observability va kha nang scale tot hon.

Ve performance, Kafka giup xu ly bat dong bo thay vi bat API Gateway ganh toan bo pipeline. Qdrant toi uu cho vector search, Redis toi uu cho online feature lookup. Ve reliability, API Gateway co fallback khi model endpoint khong kha dung, giup service van tra loi duoc request demo va health check. Ve maintainability, cau hinh nam trong Docker Compose va scripts duoc tach theo tung integration point.

## Cau Hoi 2: Xu Ly Ngat Ket Noi Local Va Kaggle

API Gateway khong phu thuoc truc tiep vao Kaggle trong luc khoi dong. `VLLM_URL` duoc doc tu environment, va khi endpoint khong duoc cau hinh, he thong dung local fallback response. Embedding pipeline cung co fallback local embedding de tiep tuc seed vector store khi khong co embedding service tren GPU.

Cach nay giup local stack van co the demo end-to-end, trong khi production co the thay fallback bang vLLM/ngrok endpoint that. Co che nay la graceful degradation: chat response van hoat dong, metrics van duoc ghi, va monitoring van cho thay gateway healthy.

## Cau Hoi 3: Kafka Decouple Components Nhu The Nao

Kafka dong vai tro event bus giua data producer va downstream pipeline. Producer chi can publish event vao topic `data.raw`, khong can biet Prefect, Delta Lake, Redis hay Qdrant dang xu ly nhu the nao. Consumer co the doc theo toc do rieng, retry doc lap va replay event khi can.

Dieu nay giam coupling giua ingestion va processing. Neu Prefect pipeline cham hoac tam dung, event van co the ton tai trong Kafka. Khi pipeline khoi phuc, consumer tiep tuc doc event va xu ly ma khong can thay doi producer.

## Cau Hoi 4: Observability

API Gateway expose `/metrics` bang Prometheus FastAPI Instrumentator. Prometheus scrape target `api-gateway:8000`, sau do Grafana dung Prometheus lam data source de hien thi health, request count, latency va status code. Cac endpoint `/health`, `/metrics`, Prometheus health va Grafana health deu duoc kiem tra trong smoke tests/readiness check.

Logs co the xem bang `docker compose logs <service>`. Metrics duoc tap trung tai Prometheus, dashboard tai Grafana, va cac script verification giup dam bao monitoring path hoat dong. Trong ban production, LangSmith co the duoc bat them bang `LANGCHAIN_API_KEY` de trace LLM calls.

## Cau Hoi 5: Service Crash Va Graceful Degradation

Neu Qdrant bi crash, API Gateway khong crash theo; vector search duoc bao ve bang try/except va se tra context rong. Chat endpoint van co the tra loi bang fallback/model endpoint. Neu Kafka crash, ingestion se fail o producer path nhung API Gateway, Redis, Qdrant, Prometheus va Grafana van co the tiep tuc hoat dong.

Redis crash lam feature lookup khong kha dung, nhung vector search va gateway van doc lap. Docker Compose giup restart service khi can, con monitoring cho phep phat hien nhanh service nao dang down. Kien truc nay uu tien degradation theo tung component thay vi lam toan bo platform dung hoan toan.
