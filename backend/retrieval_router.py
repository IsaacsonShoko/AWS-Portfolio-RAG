import json
import os
import boto3
from typing import Any

REGION = os.environ.get("AWS_REGION", "us-east-1")
KB_ID = os.environ.get("KB_ID", "")
NUM_RESULTS = int(os.environ.get("NUM_RESULTS", "6"))

_agent_client = None

def _get_agent_client():
    global _agent_client
    if _agent_client is None:
        _agent_client = boto3.client("bedrock-agent-runtime", region_name=REGION)
    return _agent_client

def load_project_profiles() -> list[dict[str, Any]]:
    profiles_path = os.path.join(os.path.dirname(__file__), "project_profiles.json")
    try:
        with open(profiles_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("profiles", [])
    except Exception as exc:
        print(f"Error loading project profiles: {exc}")
        return []

def search_project_profiles(queries: list[str], repo: str | None = None) -> list[dict[str, Any]]:
    """A simple keyword/semantic search over the loaded profiles."""
    profiles = load_project_profiles()
    if not profiles:
        return []
    
    if repo:
        # Exact match for the requested repo
        matched = [p for p in profiles if p.get("repo", "").lower() == repo.lower()]
        if matched:
            return matched
            
    # Basic keyword scoring (a real implementation might use embeddings here, 
    # but for a small set, keyword intersection on lowercased fields works reasonably well)
    scored_profiles = []
    combined_query = " ".join(queries).lower()
    query_words = set(combined_query.split())
    
    for p in profiles:
        score = 0
        text_to_search = (
            p.get("title", "") + " " + 
            p.get("summary", "") + " " + 
            p.get("business_problem", "") + " " + 
            " ".join(p.get("strongest_engineering_signals", [])) + " " +
            " ".join(p.get("domains", [])) + " " +
            " ".join(p.get("best_for", [])) + " " +
            " ".join(p.get("technical_keywords", []))
        ).lower()
        
        text_words = set(text_to_search.split())
        score = len(query_words.intersection(text_words))
        
        if score > 0:
            scored_profiles.append((score, p))
            
    # Sort by score descending and return top 3
    scored_profiles.sort(key=lambda x: x[0], reverse=True)
    return [p for score, p in scored_profiles[:3]]

def retrieve_code_evidence(queries: list[str], repo: str | None = None) -> list[dict[str, Any]]:
    """Hit the Bedrock Knowledge Base to retrieve code and doc chunks."""
    if not KB_ID:
        return []
        
    client = _get_agent_client()
    all_results = []
    seen_urls = set()
    
    # We'll just take the first query or combine them. Let's run retrieve for each subquery
    # and deduplicate. To keep latency low, we can just use the combined query.
    combined_query = " ".join(queries)
    
    retrieval_query = {"text": combined_query}
    vector_config: dict[str, Any] = {"numberOfResults": NUM_RESULTS}
    if repo:
        vector_config["filter"] = {"equals": {"key": "repo", "value": repo}}
        
    try:
        response = client.retrieve(
            knowledgeBaseId=KB_ID,
            retrievalQuery=retrieval_query,
            retrievalConfiguration={"vectorSearchConfiguration": vector_config}
        )
        
        for res in response.get("retrievalResults", []):
            content = res.get("content", {}).get("text", "")
            md = res.get("metadata", {})
            url = md.get("github_url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_results.append({
                    "content": content,
                    "metadata": md
                })
                
    except Exception as exc:
        print(f"Code evidence retrieval error: {exc}")
        
    return all_results
