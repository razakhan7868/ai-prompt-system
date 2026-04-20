import json, time, redis
from config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
from app.semantic_cache import check_cache, store_cache
from app.rate_limiter import acquire_rate_slot

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=0, decode_responses=True)

def _update_job(job_id, **fields):
    raw = r.get(f"job:{job_id}")
    if not raw:
        return
    data = json.loads(raw)
    data.update(fields)
    r.setex(f"job:{job_id}", 3600, json.dumps(data))

def _call_llm(prompt, max_tokens):
    time.sleep(0.3)
    return f"[LLM Response] Answer for: {prompt[:60]}..."

def process_prompt(job_id, prompt, max_tokens=512):
    print(f"[{job_id}] Processing...")
    _update_job(job_id, status="processing")
    try:
        cached = check_cache(prompt)
        if cached:
            print(f"[{job_id}] Cache HIT")
            _update_job(job_id, status="completed", result=cached["result"],
                       cache_hit=True, similarity=cached["similarity"])
            return cached["result"]
        if not acquire_rate_slot(timeout=60):
            raise RuntimeError("Rate limit timeout")
        result = _call_llm(prompt, max_tokens)
        store_cache(prompt, result)
        _update_job(job_id, status="completed", result=result, cache_hit=False)
        print(f"[{job_id}] Done.")
        return result
    except Exception as e:
        print(f"[{job_id}] Error: {e}")
        _update_job(job_id, status="failed", error=str(e))