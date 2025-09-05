from fastapi import FastAPI, Depends, HTTPException
from dotenv import load_dotenv
from app.models import ComposeRequest, ComposeResponse, FeedbackRequest
from app.kb_retriever import retrieve_from_kb
from app.composer import compose_answer
from app.logger import log_trace, log_feedback
from app.utils import check_auth, generate_trace_id
import time
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Uniguru-LM API")

@app.post("/compose", response_model=ComposeResponse)
async def compose(request: ComposeRequest, auth: str = Depends(check_auth)):
    trace_id = generate_trace_id()
    start = time.time()
    try:
        logger.info(f"Processing compose request: {request.query}")
        kb_results = retrieve_from_kb(request.query)
        logger.debug(f"KB results: {len(kb_results)} items")
        
        answer, citations = compose_answer(request.query, kb_results)
        
        audio_url = "mock_audio_url"  # Replace with Vaani call later
        
        steps = [
            {"kb": [r["text"] for r in kb_results]},
            {"composer": answer}
        ]
        
        response = ComposeResponse(
            final_text=answer,
            citations=citations,
            audio_url=audio_url,
            trace_id=trace_id
        )
        
        latency_ms = int((time.time() - start) * 1000)
        log_trace(trace_id, request.session_id, request.user_id, steps, latency_ms)
        logger.info(f"Compose completed, trace_id: {trace_id}, latency: {latency_ms}ms")
        
        return response
    except Exception as e:
        logger.error(f"Compose error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/feedback")
async def feedback(request: FeedbackRequest, auth: str = Depends(check_auth)):
    try:
        log_feedback(request.trace_id, request.feedback)
        logger.info(f"Feedback logged for trace_id: {request.trace_id}")
        return {"status": "Feedback logged"}
    except Exception as e:
        logger.error(f"Feedback error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)