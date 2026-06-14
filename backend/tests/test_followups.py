import backend.bedrock as bedrock
from botocore.stub import Stubber


def test_generate_followups_parses_and_cleans(monkeypatch):
    monkeypatch.setattr(bedrock, "MODEL_ARN", "arn:profile")
    monkeypatch.setattr(bedrock, "_rt_client", None)
    client = bedrock._bedrock_runtime()
    stub = Stubber(client)
    stub.add_response(
        "converse",
        {"output": {"message": {"role": "assistant",
                                "content": [{"text": "1. What database did he use?\n- How is it deployed?\nWhy that framework?"}]}},
         "stopReason": "end_turn",
         "usage": {"inputTokens": 10, "outputTokens": 12, "totalTokens": 22},
         "metrics": {"latencyMs": 100}},
        {"modelId": "arn:profile",
         "messages": [{"role": "user",
                       "content": [{"text": bedrock.FOLLOWUP_PROMPT.format(question="Q", answer="A")}]}],
         "inferenceConfig": {"maxTokens": 120, "temperature": 0.5}},
    )
    stub.activate()
    out = bedrock.generate_followups("Q", "A")
    stub.deactivate()
    assert out == ["What database did he use?", "How is it deployed?", "Why that framework?"]


def test_generate_followups_caps_at_three(monkeypatch):
    monkeypatch.setattr(bedrock, "MODEL_ARN", "arn:profile")
    monkeypatch.setattr(bedrock, "_rt_client", None)
    client = bedrock._bedrock_runtime()
    stub = Stubber(client)
    stub.add_response(
        "converse",
        {"output": {"message": {"role": "assistant", "content": [{"text": "a?\nb?\nc?\nd?\ne?"}]}},
         "stopReason": "end_turn",
         "usage": {"inputTokens": 1, "outputTokens": 1, "totalTokens": 2},
         "metrics": {"latencyMs": 1}},
        {"modelId": "arn:profile",
         "messages": [{"role": "user",
                       "content": [{"text": bedrock.FOLLOWUP_PROMPT.format(question="Q", answer="A")}]}],
         "inferenceConfig": {"maxTokens": 120, "temperature": 0.5}},
    )
    stub.activate()
    out = bedrock.generate_followups("Q", "A")
    stub.deactivate()
    assert out == ["a?", "b?", "c?"]


def test_generate_followups_empty_without_model(monkeypatch):
    monkeypatch.setattr(bedrock, "MODEL_ARN", "")
    assert bedrock.generate_followups("Q", "A") == []
