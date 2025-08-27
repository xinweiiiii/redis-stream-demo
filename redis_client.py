# redis_client.py
import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from redis.asyncio import Redis as AsyncRedis
from redis import Redis as SyncRedis

# Load .env that sits next to this file (fallback to default .env search if missing)
env_path = Path(__file__).with_name(".env")
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

def connect_redis() -> AsyncRedis:
    """
    Returns an asyncio Redis client.
    Falls back to REDIS_HOST/REDIS_PORT/REDIS_PASSWORD (+ TLS by default).
    """
    url = os.getenv("REDIS_URL")
    if url:
        parsed = urlparse(url)
        return AsyncRedis.from_url(url, decode_responses=True, ssl=(parsed.scheme == "rediss"))

    host = os.environ["REDIS_HOST"]
    port = int(os.environ.get("REDIS_PORT", "6379"))
    password = os.environ.get("REDIS_PASSWORD")
    return AsyncRedis(host=host, port=port, password=password, decode_responses=True)

# ---------- Sync (if your code is synchronous) ----------
def connect_redis_sync() -> SyncRedis:
    url = os.getenv("REDIS_URL")
    if url:
        parsed = urlparse(url)
        return SyncRedis.from_url(url, decode_responses=True, ssl=(parsed.scheme == "rediss"))

    host = os.environ["REDIS_HOST"]
    port = int(os.environ.get("REDIS_PORT", "6379"))
    password = os.environ.get("REDIS_PASSWORD")
    return SyncRedis(host=host, port=port, password=password, decode_responses=True)
