#!/usr/bin/env python3
"""Package backend/ and create-or-update the chat Lambda. Run from repo root."""
import io
import os
import zipfile
import boto3
from botocore.exceptions import ClientError

REGION = os.environ["AWS_REGION"]
ROLE_ARN = os.environ["LAMBDA_ROLE_ARN"]
FUNC = "fourd-chat"
ENV_KEYS = ["AWS_REGION", "KB_ID", "GEN_MODEL_ARN", "GUARDRAIL_ID", "GUARDRAIL_VERSION", "NUM_RESULTS"]

lam = boto3.client("lambda", region_name=REGION)


def make_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("backend/__init__.py", "")
        for name in ("handler.py", "bedrock.py", "citations.py"):
            z.write(f"backend/{name}", f"backend/{name}")
    return buf.getvalue()


def env_vars() -> dict:
    # AWS_REGION is reserved by the Lambda runtime; never set it explicitly.
    return {k: os.environ.get(k, "") for k in ENV_KEYS if k != "AWS_REGION" and os.environ.get(k)}


def main() -> None:
    code = make_zip()
    cfg = {"Variables": env_vars()}
    try:
        lam.create_function(
            FunctionName=FUNC, Runtime="python3.12", Role=ROLE_ARN,
            Handler="backend.handler.lambda_handler", Code={"ZipFile": code},
            Timeout=30, MemorySize=512, Environment=cfg,
        )
        print(f"created {FUNC}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceConflictException":
            lam.update_function_code(FunctionName=FUNC, ZipFile=code)
            lam.get_waiter("function_updated").wait(FunctionName=FUNC)
            lam.update_function_configuration(FunctionName=FUNC, Environment=cfg)
            print(f"updated {FUNC}")
        else:
            raise


if __name__ == "__main__":
    main()
