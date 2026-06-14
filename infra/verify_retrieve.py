#!/usr/bin/env python3
"""Smoke-test the KB: retrieve chunks for a sample question and print github_url + score."""
import os
import sys
import boto3

REGION = os.environ["AWS_REGION"]
KB_ID = os.environ["KB_ID"]

rt = boto3.client("bedrock-agent-runtime", region_name=REGION)


def main(question: str) -> None:
    resp = rt.retrieve(
        knowledgeBaseId=KB_ID,
        retrievalQuery={"text": question},
        retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 5}},
    )
    results = resp.get("retrievalResults", [])
    print(f"{len(results)} results for: {question!r}\n")
    for r in results:
        md = r.get("metadata", {})
        print(f"  score={r.get('score'):.3f}  repo={md.get('repo')}  url={md.get('github_url')}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "What frameworks were used for API calls?")
