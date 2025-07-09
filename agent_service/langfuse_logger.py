# agent_service/langfuse_logger.py
import httpx
import os
import uuid
from datetime import datetime

LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "http://host.docker.internal:3000")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {LANGFUSE_SECRET_KEY}",
}


def start_trace(name: str, user_id: str = "user-1") -> str:
    trace_id = str(uuid.uuid4())
    payload = {
        "id": trace_id,
        "name": name,
        "userId": user_id,
        "publicApiKey": LANGFUSE_PUBLIC_KEY,
        "timestamp": datetime.datetime.now(datetime.timezone.utc),
    }
    try:
        r = httpx.post(
            f"{LANGFUSE_HOST}/api/public/ingestion/traces",
            headers=HEADERS,
            json=payload,
            timeout=5.0
        )
        r.raise_for_status()
    except Exception as e:
        print("[Langfuse] Trace creation failed:", e)
    return trace_id


def log_span(trace_id: str, name: str, start_time: datetime, end_time: datetime):
    span_id = str(uuid.uuid4())
    payload = {
        "id": span_id,
        "traceId": trace_id,
        "name": name,
        "startTime": start_time.isoformat(),
        "endTime": end_time.isoformat(),
        "publicApiKey": LANGFUSE_PUBLIC_KEY,
    }
    try:
        r = httpx.post(
            f"{LANGFUSE_HOST}/api/public/ingestion/spans",
            headers=HEADERS,
            json=payload,
            timeout=5.0
        )
        r.raise_for_status()
    except Exception as e:
        print(f"[Langfuse] Span '{name}' failed:", e)
