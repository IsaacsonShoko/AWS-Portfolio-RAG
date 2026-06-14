# backend/tests/test_handler.py
import json
from botocore.stub import Stubber
import backend.bedrock as bedrock
from backend import handler


def _event(body: dict) -> dict:
    return {"httpMethod": "POST", "body": json.dumps(body)}


def test_happy_path_returns_answer_and_citations(monkeypatch):
    monkeypatch.setattr(bedrock, "KB_ID", "kb-1")
    monkeypatch.setattr(bedrock, "MODEL_ARN", "arn:model")
    client = bedrock._runtime()
    stubber = Stubber(client)
    stubber.add_response(
        "retrieve_and_generate",
        {
            "output": {"text": "He used Axios."},
            "sessionId": "sess-9",
            "citations": [
                {"generatedResponsePart": {"textResponsePart": {"text": "He used Axios.", "span": {"start": 0, "end": 14}}},
                 "retrievedReferences": [{"content": {"text": "import axios"},
                                          "metadata": {"github_url": "https://github.com/me/r/blob/main/api.ts", "repo": "r", "path": "api.ts"}}]},
            ],
        },
        {"input": {"text": "What did he use?"},
         "retrieveAndGenerateConfiguration": {
             "type": "KNOWLEDGE_BASE",
             "knowledgeBaseConfiguration": {
                 "knowledgeBaseId": "kb-1", "modelArn": "arn:model",
                 "retrievalConfiguration": {"vectorSearchConfiguration": {"numberOfResults": 6}},
                 "generationConfiguration": {"promptTemplate": {"textPromptTemplate": bedrock.PROMPT_TEMPLATE}},
             }}},
    )
    stubber.activate()
    resp = handler.lambda_handler(_event({"message": "What did he use?"}), None)
    stubber.deactivate()

    assert resp["statusCode"] == 200
    assert resp["headers"]["Access-Control-Allow-Origin"] == "*"
    body = json.loads(resp["body"])
    assert body["answer"] == "He used Axios.[1]"
    assert body["citations"][0]["github_url"].endswith("api.ts")
    assert body["sessionId"] == "sess-9"


def test_missing_message_returns_400():
    resp = handler.lambda_handler(_event({}), None)
    assert resp["statusCode"] == 400


def test_options_preflight_returns_204():
    resp = handler.lambda_handler({"httpMethod": "OPTIONS"}, None)
    assert resp["statusCode"] == 204
