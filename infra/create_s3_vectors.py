#!/usr/bin/env python3
"""Create the S3 Vectors bucket + index used by the Bedrock Knowledge Base.
Mirrors the Console steps in infra/docs/console-walkthrough.md. Idempotent."""
import os
import boto3
from botocore.exceptions import ClientError

REGION = os.environ["AWS_REGION"]
BUCKET = os.environ["VECTOR_BUCKET_NAME"]
INDEX = os.environ["VECTOR_INDEX_NAME"]
DIMENSION = int(os.environ.get("EMBEDDING_DIMENSION", "1024"))

# Keep big strings out of the filterable metadata budget; still returned at query time.
NON_FILTERABLE = ["github_url", "AMAZON_BEDROCK_TEXT_CHUNK"]

s3v = boto3.client("s3vectors", region_name=REGION)


def ensure_bucket() -> None:
    try:
        s3v.create_vector_bucket(vectorBucketName=BUCKET)
        print(f"created vector bucket {BUCKET}")
    except ClientError as e:
        if e.response["Error"]["Code"] in ("ConflictException", "BucketAlreadyOwnedByYou"):
            print(f"vector bucket {BUCKET} already exists")
        else:
            raise


def ensure_index() -> None:
    try:
        s3v.create_index(
            vectorBucketName=BUCKET,
            indexName=INDEX,
            dataType="float32",
            dimension=DIMENSION,
            distanceMetric="cosine",
            metadataConfiguration={"nonFilterableMetadataKeys": NON_FILTERABLE},
        )
        print(f"created index {INDEX} (dim={DIMENSION}, cosine)")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConflictException":
            print(f"index {INDEX} already exists")
        else:
            raise


if __name__ == "__main__":
    ensure_bucket()
    ensure_index()
