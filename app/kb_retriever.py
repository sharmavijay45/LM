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

qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
collections = os.getenv("QDRANT_INSTANCE_NAMES", "").split(",")
top_k = int(os.getenv("RETRIEVAL_TOP_K", 5))

embedder = SentenceTransformer("all-MiniLM-L6-v2")
client: QdrantClient | None = None


def init_qdrant_client():
    global client
    max_retries = 5
    retry_delay = 3
    for attempt in range(max_retries):
        try:
            client = QdrantClient(url=qdrant_url, timeout=20)
            # test connection
            client.get_collections()
            logger.info(f"✅ Connected to Qdrant at {qdrant_url} (attempt {attempt + 1})")
            return
        except Exception as e:
            logger.error(f"❌ Qdrant connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    client = None
    logger.error(f"🚨 Could not connect to Qdrant at {qdrant_url}")


init_qdrant_client()


def retrieve_from_kb(query: str) -> List[Dict]:
    logger.info(f"Retrieving for query: {query}")
    results = []

    if not client:
        logger.error("🚨 Qdrant client not initialized; cannot retrieve")
        return results

    try:
        query_vector = embedder.encode(query).tolist()
        for collection in collections:
            collection_name = collection.strip()
            if not client.collection_exists(collection_name):
                logger.warning(f"⚠️ Collection {collection_name} does not exist on {qdrant_url}")
                continue
            try:
                search_result = client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=top_k,
                    with_payload=True
                )
                for hit in search_result:
                    payload = hit.payload or {}
                    text = payload.get("text", "")
                    metadata = payload.get(
                        "metadata",
                        {"source": f"qdrant:{qdrant_url}:{collection_name}:{hit.id}"}
                    )
                    if text:
                        results.append({
                            "text": text[:500],
                            "metadata": metadata
                        })
            except ResponseHandlingException as e:
                logger.error(f"Qdrant search error in {collection_name}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error searching {collection_name}: {e}")
    except Exception as e:
        logger.error(f"Embedding/search error: {e}")

    # Dedup results
    seen_texts = set()
    unique_results = []
    for res in results:
        if res["text"] not in seen_texts:
            seen_texts.add(res["text"])
            unique_results.append(res)

    final_results = unique_results[:top_k]
    logger.info(f"✅ Retrieved {len(final_results)} results from Qdrant")
    return final_results
