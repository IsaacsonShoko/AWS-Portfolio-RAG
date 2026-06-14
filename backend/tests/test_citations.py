# backend/tests/test_citations.py
from backend.citations import build_response

SAMPLE = {
    "output": {"text": "He used Axios for API calls and JWT for auth."},
    "sessionId": "sess-123",
    "citations": [
        {
            "generatedResponsePart": {"textResponsePart": {"text": "He used Axios for API calls", "span": {"start": 0, "end": 27}}},
            "retrievedReferences": [
                {"content": {"text": "import axios from 'axios'"},
                 "metadata": {"github_url": "https://github.com/me/repo1/blob/main/src/api.ts", "repo": "repo1", "path": "src/api.ts"}},
            ],
        },
        {
            "generatedResponsePart": {"textResponsePart": {"text": " and JWT for auth.", "span": {"start": 27, "end": 44}}},
            "retrievedReferences": [
                {"content": {"text": "jwt.verify(token, secret)"},
                 "metadata": {"github_url": "https://github.com/me/repo1/blob/main/src/auth.ts", "repo": "repo1", "path": "src/auth.ts"}},
            ],
        },
    ],
}


def test_builds_numbered_citations_and_inline_markers():
    result = build_response(SAMPLE)
    assert result["sessionId"] == "sess-123"
    # two distinct sources -> citations [1], [2]
    assert [c["id"] for c in result["citations"]] == [1, 2]
    assert result["citations"][0]["github_url"].endswith("src/api.ts")
    assert result["citations"][0]["snippet"] == "import axios from 'axios'"
    assert result["citations"][1]["path"] == "src/auth.ts"
    # inline markers inserted at span ends
    assert "[1]" in result["answer"]
    assert "[2]" in result["answer"]


def test_deduplicates_repeated_source():
    dup = {
        "output": {"text": "A and B."},
        "sessionId": "s",
        "citations": [
            {"generatedResponsePart": {"textResponsePart": {"text": "A", "span": {"start": 0, "end": 1}}},
             "retrievedReferences": [{"content": {"text": "x"}, "metadata": {"github_url": "u1", "repo": "r", "path": "p"}}]},
            {"generatedResponsePart": {"textResponsePart": {"text": " and B.", "span": {"start": 1, "end": 8}}},
             "retrievedReferences": [{"content": {"text": "x"}, "metadata": {"github_url": "u1", "repo": "r", "path": "p"}}]},
        ],
    }
    result = build_response(dup)
    assert len(result["citations"]) == 1
    assert result["answer"].count("[1]") >= 1


def test_no_citations_returns_clean_answer():
    empty = {"output": {"text": "I don't have that in the indexed repositories."}, "sessionId": "s", "citations": []}
    result = build_response(empty)
    assert result["citations"] == []
    assert result["answer"] == "I don't have that in the indexed repositories."


def test_drops_references_without_github_url():
    bad = {
        "output": {"text": "Hi."},
        "sessionId": "s",
        "citations": [
            {"generatedResponsePart": {"textResponsePart": {"text": "Hi.", "span": {"start": 0, "end": 3}}},
             "retrievedReferences": [{"content": {"text": "x"}, "metadata": {"repo": "r"}}]},
        ],
    }
    result = build_response(bad)
    assert result["citations"] == []
