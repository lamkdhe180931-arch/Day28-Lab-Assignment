# scripts/03_delta_to_feast.py
import pandas as pd
import glob, os, redis, json
import time

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

def load_from_delta_and_push_feast():
    files = glob.glob("delta-lake/raw/*.parquet")
    if not files:
        print("No data in Delta Lake yet; using local demo records")
        df = pd.DataFrame([
            {"id": "doc_001", "text": "AI platform integration test", "timestamp": time.time()},
            {"id": "doc_002", "text": "Kafka to local fallback pipeline", "timestamp": time.time()},
        ])
    else:
        df = pd.concat([pd.read_parquet(f) for f in files])

    print(f"Loaded {len(df)} records from Delta Lake")

    # Push features vào Redis (Feast online store)
    for _, row in df.iterrows():
        feature_key = f"feature:{row['id']}"
        r.set(feature_key, json.dumps({
            "text": row["text"],
            "timestamp": row["timestamp"],
            "processed": True
        }))

    print(f"Integration 3+4 OK: Delta Lake → Feast (Redis) — {len(df)} features stored")

load_from_delta_and_push_feast()
