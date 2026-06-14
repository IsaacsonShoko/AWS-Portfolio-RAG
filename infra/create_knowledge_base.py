#!/usr/bin/env python3
"""Create the Bedrock Knowledge Base (S3 data source + S3 Vectors store).
Mirrors infra/docs/console-walkthrough.md. Prints KB_ID / DATA_SOURCE_ID to paste into config.env."""
import os
import boto3
from botocore.exceptions import ClientError

REGION = os.environ["AWS_REGION"]
ACCOUNT = os.environ["AWS_ACCOUNT_ID"]
ROLE_ARN = os.environ["KB_ROLE_ARN"]
KB_BUCKET = os.environ["KB_S3_BUCKET"]
VEC_BUCKET = os.environ["VECTOR_BUCKET_NAME"]
VEC_INDEX = os.environ["VECTOR_INDEX_NAME"]
EMB_MODEL = os.environ["EMBEDDING_MODEL_ID"]
DIM = int(os.environ.get("EMBEDDING_DIMENSION", "1024"))

agent = boto3.client("bedrock-agent", region_name=REGION)

emb_arn = f"arn:aws:bedrock:{REGION}::foundation-model/{EMB_MODEL}"
index_arn = f"arn:aws:s3vectors:{REGION}:{ACCOUNT}:bucket/{VEC_BUCKET}/index/{VEC_INDEX}"


def create_kb() -> str:
    resp = agent.create_knowledge_base(
        name="fourd-portfolio-kb",
        roleArn=ROLE_ARN,
        knowledgeBaseConfiguration={
            "type": "VECTOR",
            "vectorKnowledgeBaseConfiguration": {
                "embeddingModelArn": emb_arn,
                "embeddingModelConfiguration": {
                    "bedrockEmbeddingModelConfiguration": {"dimensions": DIM}
                },
            },
        },
        storageConfiguration={
            "type": "S3_VECTORS",
            "s3VectorsConfiguration": {"indexArn": index_arn},
        },
    )
    kb_id = resp["knowledgeBase"]["knowledgeBaseId"]
    print(f"KB_ID={kb_id}")
    return kb_id


def create_data_source(kb_id: str) -> str:
    resp = agent.create_data_source(
        knowledgeBaseId=kb_id,
        name="github-repos",
        dataSourceConfiguration={
            "type": "S3",
            "s3Configuration": {
                "bucketArn": f"arn:aws:s3:::{KB_BUCKET}",
                "inclusionPrefixes": ["repos/"],
            },
        },
    )
    ds_id = resp["dataSource"]["dataSourceId"]
    print(f"DATA_SOURCE_ID={ds_id}")
    return ds_id


if __name__ == "__main__":
    try:
        kb = create_kb()
        ds = create_data_source(kb)
        print("\nPaste into config.env:")
        print(f'export KB_ID="{kb}"')
        print(f'export DATA_SOURCE_ID="{ds}"')
    except ClientError as e:
        raise SystemExit(f"create failed: {e}")
