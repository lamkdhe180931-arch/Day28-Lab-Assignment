"""Seed the local-only demo path for submission without Kaggle GPU."""

import json
import runpy
import time


def seed_kafka_topic():
    try:
        from kafka import KafkaProducer

        producer = KafkaProducer(
            bootstrap_servers="localhost:9092",
            value_serializer=lambda v: json.dumps(v).encode(),
        )
        producer.send(
            "data.raw",
            {
                "id": "demo_001",
                "text": "Local-only AI platform submission demo",
                "timestamp": time.time(),
            },
        )
        producer.flush()
        print("Kafka demo message sent")
    except Exception as exc:
        print(f"Kafka seed skipped: {exc}")


if __name__ == "__main__":
    seed_kafka_topic()
    runpy.run_path("scripts/03_delta_to_feast.py", run_name="__main__")
    runpy.run_path("scripts/05_embed_to_qdrant.py", run_name="__main__")
    print("Local demo seed complete: Redis features and Qdrant vectors are ready")
