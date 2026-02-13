import os
import hashlib
from datetime import datetime
from typing import Dict

import psycopg2


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable not set.")


def _ensure_table_exists() -> None:
    """
    Ensures the sentinel_logs table exists.
    Safe to call multiple times (idempotent).
    """
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS sentinel_logs (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP NOT NULL,
                        query_hash TEXT NOT NULL,
                        provider TEXT NOT NULL,
                        model_used TEXT NOT NULL,
                        estimated_cost FLOAT NOT NULL,
                        actual_cost FLOAT NOT NULL,
                        confidence_score FLOAT NOT NULL,
                        refusal_flag BOOLEAN NOT NULL,
                        latency_ms INTEGER NOT NULL,
                        input_tokens INTEGER NOT NULL,
                        output_tokens INTEGER NOT NULL
                    );
                """)
    finally:
        conn.close()


def _hash_query(query: str) -> str:
    return hashlib.sha256(query.encode("utf-8")).hexdigest()


def log_request(record: Dict) -> None:
    """
    record must contain:
    {
        query,
        provider,
        model_used,
        estimated_cost,
        actual_cost,
        confidence_score,
        refusal_flag,
        latency_ms,
        input_tokens,
        output_tokens
    }
    """

    try:
        # Ensure table exists before insert
        _ensure_table_exists()

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        insert_query = """
        INSERT INTO sentinel_logs (
            timestamp,
            query_hash,
            provider,
            model_used,
            estimated_cost,
            actual_cost,
            confidence_score,
            refusal_flag,
            latency_ms,
            input_tokens,
            output_tokens
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            insert_query,
            (
                datetime.utcnow(),
                _hash_query(record["query"]),
                record["provider"],
                record["model_used"],
                record["estimated_cost"],
                record["actual_cost"],
                record["confidence_score"],
                record["refusal_flag"],
                record["latency_ms"],
                record["input_tokens"],
                record["output_tokens"],
            ),
        )

        conn.commit()
        cursor.close()
        conn.close()

    except Exception:
        # Fail closed — governance requires audit integrity
        raise RuntimeError("logging_failure")
