import hashlib
import psycopg2
from datetime import datetime
from typing import Dict

# You must configure DATABASE_URL in your environment
import os


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable not set.")


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
