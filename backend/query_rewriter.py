import json
import boto3
import os
from typing import Any

REGION = os.environ.get("AWS_REGION", "us-east-1")
MODEL_ARN = os.environ.get("GEN_MODEL_ARN", "")

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = boto3.client("bedrock-runtime", region_name=REGION)
    return _client

def rewrite_query(message: str, intent: str, repo: str | None = None) -> list[str]:
    """Rewrite the recruiter question into retrieval-friendly subqueries."""
    prompt = f"""You are a query rewriter for a portfolio retrieval system.
The user asked: "{message}"
The classified intent is: "{intent}"
Target repository filter (if any): "{repo or 'None'}"

Rewrite the question into 2-3 specific, retrieval-friendly subqueries. 
For abstract recruiter questions (like "what is his strongest skill?"), translate them into queries that look for technical evidence, business impact, ownership, or architectural tradeoffs.
Return ONLY a JSON array of strings. Do not include markdown formatting or explanations.

Example output:
["Find projects involving data capture, backend logic, and operational ownership", "Search summary docs for business impact and outcomes"]
"""
    try:
        response = _get_client().converse(
            modelId=MODEL_ARN,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"temperature": 0.2, "maxTokens": 200}
        )
        text = response["output"]["message"]["content"][0]["text"].strip()
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            arr = json.loads(text[start:end+1])
            if isinstance(arr, list):
                return [str(q) for q in arr][:3]
    except Exception as exc:
        print(f"Query rewriting error: {exc}")
        
    return [message]
