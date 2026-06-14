#!/usr/bin/env python3
"""Create a Bedrock Guardrail: block harmful content, deny prompt-injection,
mask PII, and reinforce grounded, on-topic answers."""
import os
import boto3

REGION = os.environ["AWS_REGION"]
bedrock = boto3.client("bedrock", region_name=REGION)


def main() -> None:
    resp = bedrock.create_guardrail(
        name="fourd-chat-guardrail",
        description="Recruiter-facing portfolio bot: on-topic, grounded, no PII leakage.",
        blockedInputMessaging="I can only answer questions about the engineer's public projects.",
        blockedOutputsMessaging="I do not have that in the indexed repositories.",
        contentPolicyConfig={"filtersConfig": [
            {"type": "PROMPT_ATTACK", "inputStrength": "HIGH", "outputStrength": "NONE"},
            {"type": "HATE", "inputStrength": "HIGH", "outputStrength": "HIGH"},
            {"type": "INSULTS", "inputStrength": "MEDIUM", "outputStrength": "MEDIUM"},
            {"type": "VIOLENCE", "inputStrength": "HIGH", "outputStrength": "HIGH"},
            {"type": "SEXUAL", "inputStrength": "HIGH", "outputStrength": "HIGH"},
            {"type": "MISCONDUCT", "inputStrength": "HIGH", "outputStrength": "HIGH"},
        ]},
        sensitiveInformationPolicyConfig={"piiEntitiesConfig": [
            {"type": "EMAIL", "action": "ANONYMIZE"},
            {"type": "PHONE", "action": "ANONYMIZE"},
            {"type": "CREDIT_DEBIT_CARD_NUMBER", "action": "BLOCK"},
        ]},
        contextualGroundingPolicyConfig={"filtersConfig": [
            {"type": "GROUNDING", "threshold": 0.7},
            {"type": "RELEVANCE", "threshold": 0.7},
        ]},
    )
    print(f'export GUARDRAIL_ID="{resp["guardrailId"]}"')
    print(f'export GUARDRAIL_VERSION="DRAFT"')


if __name__ == "__main__":
    main()
