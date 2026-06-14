"""API Gateway (proxy integration) Lambda entry point for the chat endpoint."""
from __future__ import annotations

import json
from typing import Any

from backend import bedrock
from backend.citations import build_response

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}
MAX_MESSAGE_LEN = 1000


def _resp(status: int, payload: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", **CORS},
        "body": "" if payload is None else json.dumps(payload),
    }


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 204, "headers": CORS, "body": ""}

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _resp(400, {"error": "invalid JSON body"})

    message = (body.get("message") or "").strip()
    if not message:
        return _resp(400, {"error": "message is required"})
    message = message[:MAX_MESSAGE_LEN]

    session_id = body.get("sessionId") or None
    repo = body.get("repo") or None

    try:
        rag = bedrock.retrieve_and_generate(message, session_id=session_id, repo=repo)
    except Exception as exc:  # surface a clean error; details go to CloudWatch
        print(f"bedrock error: {type(exc).__name__}: {exc}")
        return _resp(502, {"error": "the assistant is temporarily unavailable"})

    result = build_response(rag)
    # Generate follow-up questions
    follow_ups = bedrock.generate_follow_ups(result["answer"])
    if follow_ups:
        result["followUps"] = follow_ups

    # Lightweight, privacy-respecting observability (no PII beyond the question itself).
    print(json.dumps({"event": "chat", "repo": repo, "session": bool(session_id),
                      "num_citations": len(result["citations"]), "q_len": len(message)}))
    return _resp(200, result)
