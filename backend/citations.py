"""Turn a Bedrock RetrieveAndGenerate response into {answer, citations, sessionId}.

- Deduplicate sources by github_url, numbering them [1], [2], ... in first-seen order.
- Insert the inline numbered marker at the end of each cited span.
- Drop any retrieved reference that lacks a github_url (never fabricate a link).
"""
from __future__ import annotations

from typing import Any


def build_response(rag: dict[str, Any]) -> dict[str, Any]:
    answer_text = rag.get("output", {}).get("text", "")
    session_id = rag.get("sessionId", "")
    raw_citations = rag.get("citations", [])

    url_to_id: dict[str, int] = {}
    citations: list[dict[str, Any]] = []
    # (span_end, marker_text) insertions, applied right-to-left so offsets stay valid.
    insertions: list[tuple[int, str]] = []

    for cite in raw_citations:
        part = cite.get("generatedResponsePart", {}).get("textResponsePart", {})
        span = part.get("span", {})
        end = span.get("end")
        marker_ids: list[int] = []

        for ref in cite.get("retrievedReferences", []):
            md = ref.get("metadata", {})
            url = md.get("github_url")
            if not url:
                continue  # never invent a link
            if url not in url_to_id:
                cid = len(citations) + 1
                url_to_id[url] = cid
                citations.append({
                    "id": cid,
                    "github_url": url,
                    "repo": md.get("repo"),
                    "path": md.get("path"),
                    "language": md.get("language"),
                    "snippet": ref.get("content", {}).get("text", ""),
                })
            marker_ids.append(url_to_id[url])

        if end is not None and marker_ids:
            marker = "".join(f"[{i}]" for i in sorted(set(marker_ids)))
            insertions.append((end, marker))

    answer = answer_text
    for end, marker in sorted(insertions, key=lambda t: t[0], reverse=True):
        end = max(0, min(end, len(answer)))
        answer = answer[:end] + marker + answer[end:]

    return {"answer": answer, "citations": citations, "sessionId": session_id}
