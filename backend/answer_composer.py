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

def compose_answer(
    original_question: str, 
    intent: str, 
    semantic_hits: list[dict[str, Any]], 
    code_hits: list[dict[str, Any]]
) -> dict[str, Any]:
    """Generate a structured answer using both semantic profiles and code evidence."""
    
    # 1. Format Semantic Profiles
    semantic_context = ""
    if semantic_hits:
        semantic_context += "### Semantic Project Profiles ###\n"
        for p in semantic_hits:
            semantic_context += f"- Repo: {p.get('repo')}\n"
            semantic_context += f"  Title: {p.get('title')}\n"
            semantic_context += f"  Summary: {p.get('summary')}\n"
            semantic_context += f"  Business Problem: {p.get('business_problem')}\n"
            semantic_context += f"  Strengths: {', '.join(p.get('strongest_engineering_signals', []))}\n"
            semantic_context += f"  Keywords: {', '.join(p.get('technical_keywords', []))}\n\n"

    # 2. Format Code Evidence (and assign citation IDs)
    code_context = ""
    citations = []
    url_to_id = {}
    
    if code_hits:
        code_context += "### Code/Doc Evidence ###\n"
        for idx, hit in enumerate(code_hits):
            md = hit.get("metadata", {})
            url = md.get("github_url", "")
            if not url:
                continue
                
            if url not in url_to_id:
                cid = len(citations) + 1
                url_to_id[url] = cid
                citations.append({
                    "id": cid,
                    "github_url": url,
                    "repo": md.get("repo"),
                    "path": md.get("path"),
                    "language": md.get("language"),
                    "snippet": hit.get("content", "")[:200] # store brief snippet for frontend if needed
                })
            
            cid = url_to_id[url]
            code_context += f"--- Evidence [{cid}] ---\n"
            code_context += f"Repo: {md.get('repo')} | Path: {md.get('path')}\n"
            code_context += f"Content:\n{hit.get('content', '')}\n\n"
            
    prompt = f"""You are an assistant answering recruiters' questions about a software engineer's public GitHub projects.
You have access to Semantic Project Profiles (high-level summaries) and Code/Doc Evidence (actual repo chunks).

Intent of the question: {intent}
User Question: "{original_question}"

{semantic_context}
{code_context}

IMPORTANT INSTRUCTIONS:
1. Provide a direct, structured answer. Use bolding for key skills and project names.
2. Structure your answer with clear sections if applicable: 
   - Direct answer
   - Why these projects / strengths
   - Evidence
3. When using information from the "Code/Doc Evidence" section, you MUST append the corresponding citation marker (e.g., [1] or [2]) at the end of the sentence or claim.
4. If the answer is not supported by the context, state that you do not have that information.
5. Do not invent links, file paths, or citations that are not in the context.

Respond directly with the formatted answer.
"""
    try:
        response = _get_client().converse(
            modelId=MODEL_ARN,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"temperature": 0.2, "maxTokens": 600}
        )
        answer_text = response["output"]["message"]["content"][0]["text"].strip()
    except Exception as exc:
        print(f"Answer composition error: {exc}")
        answer_text = "I encountered an error while formulating the answer. Please try again."
        
    return {
        "answer": answer_text,
        "citations": citations
    }
    
def suggest_follow_ups(intent: str, semantic_hits: list[dict[str, Any]]) -> list[str]:
    """Suggest follow-ups based on the intent and matched profiles."""
    if not semantic_hits:
        return []
        
    # We can use the 'recruiter_questions' from the top hit
    top_hit = semantic_hits[0]
    questions = top_hit.get("recruiter_questions", [])
    
    if questions:
        return questions[:3]
        
    return ["Can you elaborate on the business impact?", "What was the hardest technical challenge here?"]
