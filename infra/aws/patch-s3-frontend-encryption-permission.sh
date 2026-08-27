#!/usr/bin/env bash
set -euo pipefail

EXEC_ROLE="ReLiC-CloudFormation-Execution"
POLICY_NAME="ReLiCFrontendS3Encryption"

cat >/tmp/relic-frontend-s3-encryption.json <<'JSON'
{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Sid":"AllowFrontendBucketEncryptionConfiguration",
      "Effect":"Allow",
      "Action":[
        "s3:PutEncryptionConfiguration",
        "s3:GetEncryptionConfiguration"
      ],
      "Resource":[
        "arn:aws:s3:::rist-*",
        "arn:aws:s3:::relic-*"
      ]
    }
  ]
}
JSON

aws iam put-role-policy \
  --role-name "$EXEC_ROLE" \
  --policy-name "$POLICY_NAME" \
  --policy-document file:///tmp/relic-frontend-s3-encryption.json

if STATUS=$(aws cloudformation describe-stacks --stack-name rist-frontend --query 'Stacks[0].StackStatus' --output text 2>/dev/null); then
  if [ "$STATUS" = "ROLLBACK_COMPLETE" ]; then
    echo "Frontend stack is ROLLBACK_COMPLETE; deleting failed shell before clean redeploy..."
    aws cloudformation delete-stack --stack-name rist-frontend
    aws cloudformation wait stack-delete-complete --stack-name rist-frontend
    echo "Failed frontend stack shell deleted successfully."
  fi
fi

echo
echo "Frontend S3 encryption permissions added to ReLiC CloudFormation execution role only."
echo "Frontend is ready for a clean redeploy."
