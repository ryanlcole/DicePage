#!/usr/bin/env python3
"""Check the existing project database and prepare private transfer encryption."""
import json
import os
from pathlib import Path

import boto3
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

REGION = "us-east-1"
STACK = "rist-platform"
PARTITION = "PROJECT#shaelvien"
KEY_OBJECT = "project-knowledge/transport/import-private-key-v1.pem"
BUCKET = "relic-deploy-artifacts-797661578124-us-east-1"

def main():
    cfn = boto3.client("cloudformation", region_name=REGION)
    stack = cfn.describe_stacks(StackName=STACK)["Stacks"][0]
    outputs = {x["OutputKey"]: x["OutputValue"] for x in stack.get("Outputs", [])}
    table_name = outputs["WorldStateTableName"]
    ddb = boto3.client("dynamodb", region_name=REGION)
    table = ddb.describe_table(TableName=table_name)["Table"]
    expected = [{"AttributeName": "pk", "KeyType": "HASH"}, {"AttributeName": "sk", "KeyType": "RANGE"}]
    if sorted(table["KeySchema"], key=lambda x: x["KeyType"]) != sorted(expected, key=lambda x: x["KeyType"]):
        raise RuntimeError("Refusing an unexpected database schema")
    # Check read access without scanning players, accounts, or world data.
    ddb.get_item(TableName=table_name, Key={"pk": {"S": PARTITION}, "sk": {"S": "KNOWLEDGE-MANIFEST"}}, ConsistentRead=True)
    print(json.dumps({"database": table_name, "status": table["TableStatus"], "partition": PARTITION, "readAccess": True}))
    s3 = boto3.client("s3", region_name=REGION)
    try:
        raw = s3.get_object(Bucket=BUCKET, Key=KEY_OBJECT)["Body"].read()
        key = serialization.load_pem_private_key(raw, password=None)
    except s3.exceptions.NoSuchKey:
        key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
        raw = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
        s3.put_object(Bucket=BUCKET, Key=KEY_OBJECT, Body=raw, ServerSideEncryption="AES256",
                      ContentType="application/x-pem-file", IfNoneMatch="*")
    public = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    Path("project-knowledge-public-key.pem").write_bytes(public)
    # Public material only; the private key is never logged or uploaded to GitHub.
    print(public.decode())
    Path("project-knowledge-preflight.json").write_text(json.dumps({"tableName": table_name, "partition": PARTITION, "readAccess": True}, indent=2) + "\n")

if __name__ == "__main__":
    main()
