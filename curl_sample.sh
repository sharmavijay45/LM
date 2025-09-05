#!/bin/bash

# Compose
curl -X POST http://localhost:8080/compose \
-H "Content-Type: application/json" \
-H "X-API-KEY: your_secret_key_here" \
-d '{"query": "What is Vedas?", "session_id": "sess123", "user_id": "user456"}'

# Feedback
curl -X POST http://localhost:8080/feedback \
-H "Content-Type: application/json" \
-H "X-API-KEY: your_secret_key_here" \
-d '{"trace_id": "some-trace-id", "feedback": "Great answer!"}'