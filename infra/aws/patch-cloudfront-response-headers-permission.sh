#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
EXEC_ROLE="ReLiC-CloudFormation-Execution"
EXEC_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${EXEC_ROLE}"
POLICY_NAME="ReLiCCloudFrontResponseHeadersPolicy"
FRONTEND_STACK="rist-frontend"

cat >/tmp/relic-cloudfront-response-headers-policy.json <<'JSON'
{
  "Version":"2012-10-17",
  "Statement":[{
    "Sid":"AllowManagedFrontendResponseHeadersPolicy",
    "Effect":"Allow",
    "Action":[
      "cloudfront:CreateResponseHeadersPolicy",
      "cloudfront:GetResponseHeadersPolicy",
      "cloudfront:GetResponseHeadersPolicyConfig",
      "cloudfront:UpdateResponseHeadersPolicy",
      "cloudfront:DeleteResponseHeadersPolicy"
    ],
    "Resource":"*"
  }]
}
JSON

aws iam put-role-policy \
  --role-name "$EXEC_ROLE" \
  --policy-name "$POLICY_NAME" \
  --policy-document file:///tmp/relic-cloudfront-response-headers-policy.json

aws iam get-role-policy \
  --role-name "$EXEC_ROLE" \
  --policy-name "$POLICY_NAME" \
  --query 'PolicyDocument.Statement' \
  --output json

STATUS=$(aws cloudformation describe-stacks \
  --stack-name "$FRONTEND_STACK" \
  --region "$REGION" \
  --query 'Stacks[0].StackStatus' \
  --output text 2>/dev/null || true)

if [ "$STATUS" = "ROLLBACK_COMPLETE" ]; then
  printf '\nFrontend stack is ROLLBACK_COMPLETE; deleting failed shell before clean redeploy...\n'
  aws cloudformation delete-stack \
    --stack-name "$FRONTEND_STACK" \
    --region "$REGION" \
    --role-arn "$EXEC_ARN"
  aws cloudformation wait stack-delete-complete \
    --stack-name "$FRONTEND_STACK" \
    --region "$REGION"
  printf 'Failed frontend stack shell deleted successfully.\n'
fi

printf '\nCloudFront response headers policy permissions added to ReLiC CloudFormation execution role only.\n'
printf 'Frontend is ready for a clean CloudFormation redeploy.\n'
