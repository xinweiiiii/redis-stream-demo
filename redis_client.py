from redis.asyncio import Redis
import os

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)  # or just load_dotenv() to auto-find


def connect_redis():
    redis = Redis(
        host=os.environ["REDIS_HOST"],
        port=int(os.environ["REDIS_PORT"]),
        password=os.environ["REDIS_PASSWORD"],
        decode_responses=True
    )

    return redis
