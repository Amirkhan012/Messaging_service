import redis

from core.config import settings


redis_client = redis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD,
    decode_responses=True
)

try:
    redis_client.ping()
    print(
        "Connection to Redis successful: "
        f"{settings.REDIS_HOST}:{settings.REDIS_PORT}"
    )
except redis.ConnectionError as e:
    print(f"Error connecting to Redis: {e}")
