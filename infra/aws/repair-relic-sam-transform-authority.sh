#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
EXEC_ROLE="ReLiC-CloudFormation-Execution"
POLICY_NAME="ReLiCCloudFormationExecution"
TRANSFORM_ARN="arn:aws:cloudformation:${REGION}:aws:transform/Serverless-2016-10-31"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

aws iam get-role-policy \
  --role-name "$EXEC_ROLE" \
  --policy-name "$POLICY_NAME" \
  --query PolicyDocument \
  --output json > "$TMP.current"

python3 - "$TMP.current" "$TMP" "$TRANSFORM_ARN" <<'PY'
import json
import sys

source, dest, transform_arn = sys.argv[1:]
with open(source, "r", encoding="utf-8") as f:
    policy = json.load(f)
statements = policy.setdefault("Statement", [])
statements = [s for s in statements if s.get("Sid") != "ReLiCSamTransform"]
statements.append({
    "Sid": "ReLiCSamTransform",
    "Effect": "Allow",
    "Action": "cloudformation:CreateChangeSet",
    "Resource": transform_arn,
})
policy["Statement"] = statements
with open(dest, "w", encoding="utf-8") as f:
    json.dump(policy, f, separators=(",", ":"))
PY

rm -f "$TMP.current"

aws iam put-role-policy \
  --role-name "$EXEC_ROLE" \
  --policy-name "$POLICY_NAME" \
  --policy-document "file://$TMP"

aws iam get-role-policy \
  --role-name "$EXEC_ROLE" \
  --policy-name "$POLICY_NAME" \
  --query "PolicyDocument.Statement[?Sid=='ReLiCSamTransform']" \
  --output json

printf '\nReLiC SAM transform authority repaired with one scoped permission.\n'
printf 'Role: %s\n' "$EXEC_ROLE"
printf 'Action: cloudformation:CreateChangeSet\n'
printf 'Resource: %s\n' "$TRANSFORM_ARN"
