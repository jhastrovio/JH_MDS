import os
import redis

def test_redis_connection():
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        print("REDIS_URL is not set in the environment variables.")
        return

    try:
        client = redis.StrictRedis.from_url(redis_url)
        client.ping()
        print("Successfully connected to Redis!")
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")

if __name__ == "__main__":
    test_redis_connection()