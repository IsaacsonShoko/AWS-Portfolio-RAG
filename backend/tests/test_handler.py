# backend/tests/test_handler.py
import json
from backend import handler

def _event(body: dict) -> dict:
    return {"httpMethod": "POST", "body": json.dumps(body)}

def test_happy_path_returns_answer_and_citations(monkeypatch):
    # Mock the new pipeline components
    monkeypatch.setattr("backend.handler.classify_intent", lambda m, repo: "general_inquiry")
    monkeypatch.setattr("backend.handler.rewrite_query", lambda m, intent, repo: [m])
    monkeypatch.setattr("backend.handler.search_project_profiles", lambda q, repo: [])
    monkeypatch.setattr("backend.handler.retrieve_code_evidence", lambda q, repo: [])
    monkeypatch.setattr("backend.handler.compose_answer", lambda **kwargs: {
        "answer": "He used Axios.[1]",
        "citations": [{"id": 1, "github_url": "https://github.com/me/r/blob/main/api.ts", "repo": "r", "path": "api.ts", "snippet": "import axios"}]
    })
    monkeypatch.setattr("backend.handler.suggest_follow_ups", lambda intent, hits: [])

    resp = handler.lambda_handler(_event({"message": "What did he use?"}), None)

    assert resp["statusCode"] == 200
    assert resp["headers"]["Access-Control-Allow-Origin"] == "*"
    body = json.loads(resp["body"])
    assert body["answer"] == "He used Axios.[1]"
    assert body["citations"][0]["github_url"].endswith("api.ts")

def test_missing_message_returns_400():
    resp = handler.lambda_handler(_event({}), None)
    assert resp["statusCode"] == 400

def test_options_preflight_returns_204():
    resp = handler.lambda_handler({"httpMethod": "OPTIONS"}, None)
    assert resp["statusCode"] == 204
