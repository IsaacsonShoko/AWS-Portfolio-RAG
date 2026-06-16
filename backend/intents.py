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

def classify_intent(message: str, repo: str | None = None) -> str:
    """Classify the user's message into a core intent."""
    intents = [
        "compare_projects",
        "identify_strengths",
        "business_impact",
        "architecture_tradeoffs",
        "ownership_scope",
        "iot_hardware_telemetry",
        "rag_ai_systems",
        "quant_systems",
        "automation_reporting",
        "implementation_detail",
        "general_inquiry"
    ]
    
    prompt = f"""You are an intent classifier for a recruiter-facing portfolio assistant.
Classify the following user message into exactly ONE of these intents:
{json.dumps(intents, indent=2)}

Message: "{message}"

Return ONLY the string of the intent, nothing else.
"""
    try:
        response = _get_client().converse(
            modelId=MODEL_ARN,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"temperature": 0.0, "maxTokens": 50}
        )
        intent = response["output"]["message"]["content"][0]["text"].strip().lower()
        # Clean up if the model wrapped it in quotes
        intent = intent.replace('"', '').replace("'", "")
        if intent in intents:
            return intent
    except Exception as exc:
        print(f"Intent classification error: {exc}")
    
    return "general_inquiry"
