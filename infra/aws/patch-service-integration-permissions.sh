#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
EXEC_ROLE="ReLiC-CloudFormation-Execution"

cat >/tmp/relic-service-integration-policy.json <<JSON
{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Sid":"AllowAWSServiceKmsGrants",
      "Effect":"Allow",
      "Action":["kms:CreateGrant","kms:ListGrants","kms:RevokeGrant"],
      "Resource":"arn:aws:kms:${REGION}:${ACCOUNT_ID}:key/*",
      "Condition":{"Bool":{"kms:GrantIsForAWSResource":"true"}}
    },
    {
      "Sid":"AllowSesEmailIdentityLifecycle",
      "Effect":"Allow",
      "Action":["ses:CreateEmailIdentity","ses:DeleteEmailIdentity","ses:GetEmailIdentity"],
      "Resource":"arn:aws:ses:${REGION}:${ACCOUNT_ID}:identity/*"
    }
  ]
}
JSON

aws iam put-role-policy \
  --role-name "$EXEC_ROLE" \
  --policy-name ReLiCServiceIntegrationPermissions \
  --policy-document file:///tmp/relic-service-integration-policy.json

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
  --policy-name ReLiCServiceIntegrationPermissions \
  --query 'PolicyDocument.Statement' \
  --output json

printf '\nAWS service integration permissions added to ReLiC CloudFormation execution role only.\n'
printf 'Platform and mail are ready for clean redeploy.\n'
