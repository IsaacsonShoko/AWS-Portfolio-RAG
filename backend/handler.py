"""API Gateway (proxy integration) Lambda entry point for the chat endpoint."""
from __future__ import annotations

import json
from typing import Any

from backend.intents import classify_intent
from backend.query_rewriter import rewrite_query
from backend.retrieval_router import search_project_profiles, retrieve_code_evidence
from backend.answer_composer import compose_answer, suggest_follow_ups

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
        # 1. Intent Classification
        intent = classify_intent(message, repo=repo)

        # 2. Query Rewriting
        rewritten_queries = rewrite_query(message, intent=intent, repo=repo)

        # 3. Retrieval Routing
        semantic_hits = []
        code_hits = []

        abstract_intents = {"compare_projects", "identify_strengths", "business_impact", "ownership_scope"}
        if intent in abstract_intents:
            semantic_hits = search_project_profiles(rewritten_queries, repo=repo)
            code_hits = retrieve_code_evidence(rewritten_queries, repo=repo)
        else:
            code_hits = retrieve_code_evidence(rewritten_queries, repo=repo)
            semantic_hits = search_project_profiles(rewritten_queries, repo=repo)

        # 4. Answer Composition
        result = compose_answer(
            original_question=message,
            intent=intent,
            semantic_hits=semantic_hits,
            code_hits=code_hits,
        )
        
        # Add Session ID
        result["sessionId"] = session_id
        
        # 5. Follow-ups
        follow_ups = suggest_follow_ups(intent, semantic_hits)
        if follow_ups:
            result["followUps"] = follow_ups

    except Exception as exc:  # surface a clean error; details go to CloudWatch
        print(f"Pipeline error: {type(exc).__name__}: {exc}")
        return _resp(502, {"error": "the assistant is temporarily unavailable"})

    # Lightweight, privacy-respecting observability
    print(json.dumps({"event": "chat", "repo": repo, "session": bool(session_id),
                      "num_citations": len(result.get("citations", [])), "q_len": len(message), "intent": intent}))
    return _resp(200, result)
