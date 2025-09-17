# main.py
import os
import logging
import httpx
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
import time
import uuid
from app.kb_retriever import retrieve_from_kb
from app.composer import compose_answer

from dotenv import load_dotenv
import os
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "vedas_knowledge_base")
INSTANCE_NAMES = os.getenv("QDRANT_INSTANCE_NAMES", "").split(",")
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", 5))

OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

mongo_url = os.getenv("MONGO_URL")
mongo_client = MongoClient(mongo_url)
db = mongo_client.uniguru
traces_collection = db.traces
feedback_collection = db.feedback

auth_key = os.getenv("API_KEY")

client = QdrantClient(QDRANT_URL)
embedder = SentenceTransformer("all-MiniLM-L6-v2")

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComposeRequest(BaseModel):
    query: str
    session_id: str = None
    user_id: str = None

class FeedbackRequest(BaseModel):
    trace_id: str
    reward: float
    feedback_text: str

@app.post("/compose")
async def compose(req: ComposeRequest, authorization: str = Header(None)):
    if authorization != auth_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    query = req.query
    logger.info(f"Processing compose request: {query}")

    # Retrieve from KB
    contexts = retrieve_from_kb(query)
    if not contexts:
        return {"answer": "⚠️ No relevant knowledge found."}

    # Compose answer
    answer, citations = compose_answer(query, contexts)

    trace_id = str(uuid.uuid4())
    session_id = req.session_id if req.session_id else str(uuid.uuid4())
    user_id = req.user_id if req.user_id else "anonymous"

    # Log to Mongo
    trace_log = {
        "trace_id": trace_id,
        "session_id": session_id,
        "user_id": user_id,
        "timestamp": time.time(),
        "steps": [
            {"kb": [ctx["text"][:100] for ctx in contexts]},
            {"composer": answer[:100]}
        ],
        "latency_ms": 0  # Calculate if needed
    }
    traces_collection.insert_one(trace_log)

    return {
        "trace_id": trace_id,
        "final_text": answer,
        "citations": citations,
        "audio_url": None  # For now
    }

@app.post("/feedback")
async def feedback(req: FeedbackRequest):
    feedback_collection.insert_one({
        "trace_id": req.trace_id,
        "reward": req.reward,
        "feedback_text": req.feedback_text,
        "timestamp": time.time()
    })
    return {"status": "ok"}
