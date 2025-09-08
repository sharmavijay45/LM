# main.py
import os
import uuid
import logging
import httpx
from fastapi import FastAPI
from pydantic import BaseModel
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from dotenv import load_dotenv
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "vedas_knowledge_base")
INSTANCE_NAMES = os.getenv("QDRANT_INSTANCE_NAMES", "").split(",")
VECTOR_SIZE = int(os.getenv("QDRANT_VECTOR_SIZE", 384))
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", 5))

OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

client = QdrantClient(QDRANT_URL)
embedder = SentenceTransformer("all-MiniLM-L6-v2")

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComposeRequest(BaseModel):
    query: str

@app.post("/compose")
async def compose(req: ComposeRequest):
    query = req.query
    logger.info(f"Processing compose request: {query}")

    query_vector = embedder.encode(query).tolist()
    results = []

    for instance in INSTANCE_NAMES:
        collection = f"{instance.strip()}_{QDRANT_COLLECTION}"
        try:
            hits = client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=RETRIEVAL_TOP_K
            )
            results.extend(hits)
        except Exception as e:
            logger.warning(f"⚠️ Error querying {collection}: {e}")

    if not results:
        return {"answer": "⚠️ No relevant knowledge found in Qdrant."}

    context = "\n".join([hit.payload.get("text", "") for hit in results])

    # Ask Ollama
    try:
        async with httpx.AsyncClient() as http:
            resp = await http.post(
                OLLAMA_URL,
                json={"model": OLLAMA_MODEL, "prompt": f"Answer based on:\n{context}\n\nQ: {query}\nA:"}
            )
            resp.raise_for_status()
            answer = resp.json().get("response", "")
    except Exception as e:
        answer = f"⚠️ Failed to query Ollama: {e}"

    trace_id = str(uuid.uuid4())
    logger.info(f"Compose completed, trace_id: {trace_id}")

    return {
        "trace_id": trace_id,
        "query": query,
        "context": context,
        "answer": answer
    }
