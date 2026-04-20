import time
import redis
from config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=0, decode_responses=True)

RATE_LIMIT = 300
WINDOW_SEC = 60
RATE_KEY = "provider:rate_limit"

def _current_window():
    return str(int(time.time()) // WINDOW_SEC)

def acquire_rate_slot(timeout=30.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        window = _current_window()
        key = f"{RATE_KEY}:{window}"
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.expire(key, WINDOW_SEC + 5)
        count, _ = pipe.execute()
        if count <= RATE_LIMIT:
            return True
        seconds_left = WINDOW_SEC - (int(time.time()) % WINDOW_SEC)
        print(f"[RateLimit] Limit reached ({count}/{RATE_LIMIT}). Sleeping {seconds_left}s")
        time.sleep(min(seconds_left, deadline - time.time()))
    return False

def current_usage():
    window = _current_window()
    key = f"{RATE_KEY}:{window}"
    count = int(r.get(key) or 0)
    return {
        "requests_this_window": count,
        "limit": RATE_LIMIT,
        "remaining": max(0, RATE_LIMIT - count)
    }