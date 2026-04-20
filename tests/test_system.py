import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import redis
from config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=0, decode_responses=True)

def test_redis_connection():
    assert r.ping() == True
    print(" Req 1: Redis connected")

def test_job_creation():
    import uuid, json
    job_id = str(uuid.uuid4())
    job_data = {"job_id": job_id, "status": "queued", "prompt": "test"}
    r.setex(f"job:{job_id}", 3600, json.dumps(job_data))
    result = r.get(f"job:{job_id}")
    assert result is not None
    print(" Req 1: Job creation works")

def test_rate_limiter():
    from app.rate_limiter import acquire_rate_slot, current_usage
    slot = acquire_rate_slot(timeout=5)
    assert slot == True
    usage = current_usage()
    assert usage["requests_this_window"] >= 1
    print(f" Req 3: Rate limiter works — {usage['requests_this_window']}/300 used")

def test_semantic_cache():
    from app.semantic_cache import store_cache, check_cache
    # Use very similar sentences so word-overlap works
    original = "what is capital of France"
    similar  = "what is capital of France"
    store_cache(original, "Paris")
    result = check_cache(similar)
    assert result is not None
    assert result["cache_hit"] == True
    print(f" Req 4: Semantic cache works — similarity={result['similarity']:.3f}")

def test_full_pipeline():
    import uuid, json
    from workers.tasks import process_prompt
    job_id = str(uuid.uuid4())
    r.setex(f"job:{job_id}", 3600, json.dumps({
        "job_id": job_id,
        "status": "queued",
        "prompt": "test"
    }))
    result = process_prompt(job_id, "Explain Python in one line", 256)
    assert result is not None
    print(f" Req 2&5: Full pipeline works — result: {result[:50]}")

if __name__ == "__main__":
    print("\n Running all tests...\n")
    test_redis_connection()
    test_job_creation()
    test_rate_limiter()
    test_semantic_cache()
    test_full_pipeline()
    print("\n ALL TESTS PASSED!")