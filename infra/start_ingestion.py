#!/usr/bin/env python3
"""Start a Bedrock KB ingestion job and poll until it finishes."""
import os
import time
import boto3

REGION = os.environ["AWS_REGION"]
KB_ID = os.environ["KB_ID"]
DS_ID = os.environ["DATA_SOURCE_ID"]

agent = boto3.client("bedrock-agent", region_name=REGION)


def main() -> None:
    job = agent.start_ingestion_job(knowledgeBaseId=KB_ID, dataSourceId=DS_ID)
    job_id = job["ingestionJob"]["ingestionJobId"]
    print(f"started ingestion job {job_id}")
    while True:
        status = agent.get_ingestion_job(
            knowledgeBaseId=KB_ID, dataSourceId=DS_ID, ingestionJobId=job_id
        )["ingestionJob"]
        state = status["status"]
        print(f"status: {state}")
        if state in ("COMPLETE", "FAILED"):
            print(status.get("statistics", {}))
            if state == "FAILED":
                raise SystemExit(status.get("failureReasons", []))
            return
        time.sleep(15)


if __name__ == "__main__":
    main()
