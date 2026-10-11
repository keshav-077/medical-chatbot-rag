"""Langfuse traces. No-op when keys or the package are missing.

LANGFUSE_HOST and LANGFUSE_BASE_URL are both accepted.
"""

import logging
import os
import uuid

logger = logging.getLogger(__name__)


class _Noop:
    def __init__(self, trace_id: str):
        self.trace_id = trace_id

    def end(self, output=None, metadata=None):
        return None


def start_trace(name: str, user_id, inputs: dict, request_id: str = ""):
    trace_id = str(uuid.uuid4())
    public = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret = os.getenv("LANGFUSE_SECRET_KEY")
    if not public or not secret:
        return _Noop(trace_id)
    try:
        from langfuse import Langfuse

        client = Langfuse(
            public_key=public,
            secret_key=secret,
            host=os.getenv("LANGFUSE_HOST")
            or os.getenv("LANGFUSE_BASE_URL")
            or "https://cloud.langfuse.com",
        )
        trace = client.trace(
            id=trace_id,
            name=name,
            user_id=str(user_id) if user_id else None,
            input=inputs,
            metadata={"request_id": request_id},
        )
        return _LangfuseHandle(client, trace, trace_id)
    except Exception as exc:
        logger.warning("Langfuse disabled: %s", exc)
        return _Noop(trace_id)


class _LangfuseHandle:
    def __init__(self, client, trace, trace_id: str):
        self.client = client
        self.trace = trace
        self.trace_id = trace_id

    def end(self, output=None, metadata=None):
        try:
            self.trace.update(output=output, metadata=metadata or {})
            self.client.flush()
        except Exception as exc:
            logger.warning("Langfuse flush failed: %s", exc)
