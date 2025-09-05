from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

mongo_url = os.getenv("MONGO_URL")
db_name = os.getenv("LOG_DB_NAME")
collection_name = os.getenv("LOG_COLLECTION_NAME")

client = MongoClient(mongo_url)
db = client[db_name]
collection = db[collection_name]

def log_trace(trace_id: str, session_id: str, user_id: str, steps: list, latency_ms: int):
    doc = {
        "trace_id": trace_id,
        "session_id": session_id,
        "user_id": user_id,
        "steps": steps,
        "latency_ms": latency_ms,
        "timestamp": datetime.utcnow()
    }
    collection.insert_one(doc)

def log_feedback(trace_id: str, feedback: str):
    collection.update_one({"trace_id": trace_id}, {"$set": {"feedback": feedback}})