"""Store uploads locally, and in S3 or R2 when credentials exist."""

import os
import uuid
from pathlib import Path


def _local_root() -> Path:
    root = Path(os.getenv("UPLOAD_DIR", "instance/uploads"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_bytes(filename: str, data: bytes) -> str:
    safe = os.path.basename(filename) or "upload.bin"
    key = f"{uuid.uuid4().hex}_{safe}"
    bucket = os.getenv("S3_BUCKET")
    if bucket and os.getenv("AWS_ACCESS_KEY_ID"):
        try:
            import boto3

            client = boto3.client(
                "s3",
                endpoint_url=os.getenv("S3_ENDPOINT_URL") or None,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_REGION", "auto"),
            )
            client.put_object(Bucket=bucket, Key=key, Body=data)
            return f"s3://{bucket}/{key}"
        except Exception:
            pass
    path = _local_root() / key
    path.write_bytes(data)
    return str(path)


def read_bytes(storage_key: str) -> bytes:
    if storage_key.startswith("s3://"):
        import boto3

        _, _, rest = storage_key.partition("s3://")
        bucket, _, key = rest.partition("/")
        client = boto3.client(
            "s3",
            endpoint_url=os.getenv("S3_ENDPOINT_URL") or None,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "auto"),
        )
        obj = client.get_object(Bucket=bucket, Key=key)
        return obj["Body"].read()
    return Path(storage_key).read_bytes()
