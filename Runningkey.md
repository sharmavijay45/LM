# How to Run the Uniguru-LM Project

This document provides a step-by-step guide to set up and run the Uniguru-LM project.

## 1. Prerequisites

Make sure you have the following software installed on your system:

- **Python (3.8+ recommended)**: [Download Python](https://www.python.org/downloads/)
- **Docker**: [Install Docker](https://docs.docker.com/get-docker/)

## 2. Installation

Clone the repository and install the required Python packages.

```bash
git clone <repository-url>
cd LMTask
pip install -r requirements.txt
```

## 3. Environment Setup

Create a `.env` file in the root of the project and add the following environment variables. This file is used to configure the application.

```
# NAS Configuration
NAS_IP=192.168.0.94
DOCUMENTS_PATH=\\192.168.0.94\Guruukul_DB\source_documents

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_INSTANCE_NAMES=vedas_knowledge_base,vedas_legacy_data
RETRIEVAL_TOP_K=5

# Ollama Configuration
OLLAMA_URL=<your-ollama-url>
OLLAMA_MODEL=llama3.1

# MongoDB Configuration for Logging
MONGO_URL=<your-mongodb-url>
LOG_DB_NAME=uniguru
LOG_COLLECTION_NAME=traces

# API Key for Authentication
API_KEY=your_secret_key_here
```

**Note:** Replace `<your-ollama-url>` and `<your-mongodb-url>` with your actual Ollama and MongoDB URLs.

## 4. NAS Setup

Mount the network-attached storage (NAS) to make the source documents available to the application.

```bash
net use G: \\192.168.0.94\Guruukul_DB /user:Vijay vijay45
```

**Note:** This command is for Windows. For other operating systems, use the appropriate command to mount a network drive.

## 5. Start Docker and Qdrant

The `docker-compose.yml` file is configured to start the Qdrant vector database.

```bash
docker-compose up -d
```

This command will start a Qdrant container and mount the `qdrant_data` directory from the NAS.

## 6. Data Ingestion

After starting Qdrant, you need to ingest the documents from the NAS into the Qdrant database. The `ingest.py` script is used for this purpose.

```bash
python ingest.py
```

This script will:
- Read the documents from the `DOCUMENTS_PATH`.
- Create text embeddings using a sentence transformer model.
- Ingest the embeddings into the Qdrant collections specified in `QDRANT_INSTANCE_NAMES`.

## 7. Running the Application

Once the data is ingested, you can run the main FastAPI application.

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

The application will be available at `http://localhost:8080`.

## 8. API Usage

You can interact with the API using the following `curl` commands.

### Compose Endpoint

This endpoint takes a query and returns a composed answer based on the knowledge base.

```bash
curl -X POST http://localhost:8080/compose \
-H "Content-Type: application/json" \
-H "Authorization: your_secret_key_here" \
-d '{"query": "What is Vedas?", "session_id": "sess123", "user_id": "user456"}'
```

### Feedback Endpoint

This endpoint is used to provide feedback on a composed answer.

```bash
curl -X POST http://localhost:8080/feedback \
-H "Content-Type: application/json" \
-H "Authorization: your_secret_key_here" \
-d '{"trace_id": "some-trace-id", "reward": 1.0, "feedback_text": "Good response"}'
```
