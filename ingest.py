# ingest.py
import os
import glob
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
import fitz  # PyMuPDF for PDF
import docx

# Load ENV
from dotenv import load_dotenv
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "vedas_knowledge_base")
VECTOR_SIZE = int(os.getenv("QDRANT_VECTOR_SIZE", 384))
DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH", "./source_documents")
INSTANCE_NAMES = os.getenv("QDRANT_INSTANCE_NAMES", "").split(",")

# Init models
embedder = SentenceTransformer("all-MiniLM-L6-v2")
client = QdrantClient(QDRANT_URL)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

def load_txt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def load_pdf(path):
    text = ""
    pdf = fitz.open(path)
    for page in pdf:
        text += page.get_text()
    return text

def load_docx(path):
    doc = docx.Document(path)
    return "\n".join([p.text for p in doc.paragraphs])

def get_documents():
    docs = []
    for ext in ["*.txt", "*.pdf", "*.docx"]:
        for file in glob.glob(os.path.join(DOCUMENTS_PATH, ext)):
            if ext == "*.txt":
                text = load_txt(file)
            elif ext == "*.pdf":
                text = load_pdf(file)
            elif ext == "*.docx":
                text = load_docx(file)
            else:
                continue

            for chunk in splitter.split_text(text):
                docs.append({"text": chunk, "source": file})
    return docs

def ensure_collection(name):
    if not client.get_collection(name, with_vectors=False, raise_on_error=False):
        client.recreate_collection(
            collection_name=name,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        print(f"✅ Created collection: {name}")
    else:
        print(f"ℹ️ Collection already exists: {name}")

def ingest():
    docs = get_documents()
    if not docs:
        print(f"⚠️ No documents found in {DOCUMENTS_PATH}")
        return

    for instance in INSTANCE_NAMES:
        collection = f"{instance.strip()}_{QDRANT_COLLECTION}"
        ensure_collection(collection)

        vectors = embedder.encode([d["text"] for d in docs], show_progress_bar=True)

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vec.tolist(),
                payload=d
            )
            for d, vec in zip(docs, vectors)
        ]

        client.upsert(collection_name=collection, points=points)
        print(f"✅ Inserted {len(points)} points into {collection}")

if __name__ == "__main__":
    ingest()
