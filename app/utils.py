from fastapi import Header, HTTPException
from dotenv import load_dotenv
import time
import uuid
import os

load_dotenv()

api_key = os.getenv("API_KEY")

def check_auth(x_api_key: str = Header(None)):
    if x_api_key != api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

def measure_latency(func):
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        latency_ms = int((time.time() - start) * 1000)
        return result, latency_ms
    return wrapper

def generate_trace_id():
    return str(uuid.uuid4())