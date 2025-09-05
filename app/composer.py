import requests
import os
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

ollama_url = os.getenv("OLLAMA_URL")
ollama_model = os.getenv("OLLAMA_MODEL")

def compose_answer(query: str, contexts: List[Dict]) -> tuple[str, List[Dict]]:
    context_text = "\n".join([ctx["text"] for ctx in contexts])
    prompt = f"Based on this context: {context_text}\n\nAnswer the query: {query}"
    
    payload = {
        "model": ollama_model,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(ollama_url, json=payload)
        response.raise_for_status()
        answer = response.json().get("response", "No answer generated.")
    except Exception as e:
        answer = f"Error composing: {e}"
    
    citations = [{"source": ctx["metadata"].get("source", "unknown"), "snippet": ctx["text"][:100]} for ctx in contexts]
    return answer, citations