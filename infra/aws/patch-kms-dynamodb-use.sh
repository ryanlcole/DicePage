#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
EXEC_ROLE="ReLiC-CloudFormation-Execution"
POLICY_NAME="ReLiCDynamoDbKmsUse"

cat >/tmp/relic-dynamodb-kms-policy.json <<JSON
{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Sid":"AllowDynamoDbKmsDataUse",
      "Effect":"Allow",
      "Action":[
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:DescribeKey"
      ],
      "Resource":"arn:aws:kms:${REGION}:${ACCOUNT_ID}:key/*",
      "Condition":{
        "StringEquals":{
          "kms:ViaService":"dynamodb.${REGION}.amazonaws.com",
          "kms:CallerAccount":"${ACCOUNT_ID}"
        }
      }
    }
  ]
}
JSON

aws iam put-role-policy \
  --role-name "$EXEC_ROLE" \
  --policy-name "$POLICY_NAME" \
  --policy-document file:///tmp/relic-dynamodb-kms-policy.json

for STACK in rist-platform relic-mail-gateway; do
  STATUS=$(aws cloudformation describe-stacks --stack-name "$STACK" --query 'Stacks[0].StackStatus' --output text 2>/dev/null || true)
  if [ "$STATUS" = "ROLLBACK_COMPLETE" ]; then
    echo "$STACK is ROLLBACK_COMPLETE; deleting failed shell before clean redeploy..."
    aws cloudformation delete-stack --stack-name "$STACK"
    aws cloudformation wait stack-delete-complete --stack-name "$STACK"
    echo "$STACK failed shell deleted successfully."
  fi
done

aws iam get-role-policy \
  --role-name "$EXEC_ROLE" \
  --policy-name "$POLICY_NAME" \
  --query 'PolicyDocument.Statement' \
  --output json

printf '\nDynamoDB KMS data-use permission added to ReLiC CloudFormation execution role only.\n'
printf 'Restricted to DynamoDB in %s for account %s.\n' "$REGION" "$ACCOUNT_ID"
printf 'Platform and mail are ready for clean redeploy.\n'
