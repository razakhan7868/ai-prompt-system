from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid, redis, json
from config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD

app = FastAPI(title="Prompt Processing System")

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=0, decode_responses=True)

class PromptRequest(BaseModel):
    prompt: str
    priority: Optional[int] = 1
    user_id: Optional[str] = "anonymous"
    max_tokens: Optional[int] = 512

@app.post("/api/v1/prompts")
async def submit_prompt(request: PromptRequest):
    job_id = str(uuid.uuid4())
    job_data = {
        "job_id": job_id,
        "status": "queued",
        "prompt": request.prompt,
        "user_id": request.user_id,
        "result": None,
        "cache_hit": False
    }
    r.setex(f"job:{job_id}", 3600, json.dumps(job_data))
    return {"job_id": job_id, "status": "queued", "message": "Prompt submitted successfully"}

@app.get("/api/v1/prompts/{job_id}")
async def get_job_status(job_id: str):
    data = r.get(f"job:{job_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Job not found")
    return json.loads(data)

@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}