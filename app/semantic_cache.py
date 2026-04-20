import json, hashlib
import redis
from config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD

CACHE_PREFIX = "semantic_cache:"
EMBEDDING_TTL = 86400

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=0,
    decode_responses=True
)

def _simple_similarity(a, b):
    set_a = set(a.lower().split())
    set_b = set(b.lower().split())
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)

def check_cache(prompt):
    for key in r.scan_iter(f"{CACHE_PREFIX}*"):
        raw = r.get(key)
        if not raw:
            continue
        entry = json.loads(raw)
        sim = _simple_similarity(prompt, entry["original_prompt"])
        if sim >= 0.6:
            print(f"[Cache HIT] similarity={sim:.4f}")
            return {
                "result": entry["result"],
                "cache_hit": True,
                "similarity": sim
            }
    return None

def store_cache(prompt, result):
    key = f"{CACHE_PREFIX}{hashlib.md5(prompt.encode()).hexdigest()}"
    entry = {"original_prompt": prompt, "result": result}
    r.setex(key, EMBEDDING_TTL, json.dumps(entry))
    print(f"[Cache STORE] key={key}")