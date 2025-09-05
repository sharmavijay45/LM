import logging
import time, os
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import ResponseHandlingException
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

qdrant_url = os.getenv("QDRANT_URL")
collections = os.getenv("QDRANT_INSTANCE_NAMES").split(",")
top_k = int(os.getenv("RETRIEVAL_TOP_K", 5))

embedder = SentenceTransformer('all-MiniLM-L6-v2')
client = None

def init_qdrant_client():
    global client
    max_retries = 3
    retry_delay = 5
    for attempt in range(max_retries):
        try:
            client = QdrantClient(qdrant_url, timeout=10)
            logger.info(f"Connected to Qdrant at {qdrant_url} on attempt {attempt + 1}")
            return
        except Exception as e:
            logger.error(f"Qdrant connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error(f"Max retries reached; Qdrant at {qdrant_url} unavailable")
    client = None

init_qdrant_client()

def retrieve_from_kb(query: str) -> List[Dict]:
    logger.info(f"Retrieving for query: {query}")
    results = []

    if not client:
        logger.error(f"Qdrant client not initialized for {qdrant_url}; cannot retrieve")
        return results

    try:
        query_vector = embedder.encode(query).tolist()
        for collection in collections:
            collection_name = f"{collection.strip()}_vedas_knowledge_base"
            if not client.collection_exists(collection_name):
                logger.warning(f"Collection {collection_name} does not exist on {qdrant_url}")
                continue
            logger.debug(f"Searching collection: {collection_name} on {qdrant_url}")
            try:
                search_result = client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=top_k,
                    with_payload=True
                )
                logger.debug(f"Found {len(search_result)} hits in {collection_name}")
                for hit in search_result:
                    payload = hit.payload or {}
                    text = payload.get("text", "")
                    metadata = payload.get("metadata", {"source": f"qdrant:{qdrant_url}:{collection_name}:{hit.id}"})
                    if text:
                        results.append({
                            "text": text[:500],
                            "metadata": metadata
                        })
            except ResponseHandlingException as e:
                logger.error(f"Qdrant search error for {collection_name} on {qdrant_url}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error searching {collection_name} on {qdrant_url}: {e}")
    except Exception as e:
        logger.error(f"Embedding or search error for {qdrant_url}: {e}")

    # Dedup
    seen_texts = set()
    unique_results = []
    for res in results:
        if res["text"] not in seen_texts:
            seen_texts.add(res["text"])
            unique_results.append(res)
    results = unique_results[:top_k]
    logger.info(f"Retrieved {len(results)} unique results from Qdrant at {qdrant_url}")
    
    if not results:
        logger.warning(f"No results retrieved from {qdrant_url}; check collections or server status")
    
    return results