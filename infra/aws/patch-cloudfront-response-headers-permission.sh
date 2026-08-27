#!/usr/bin/env bash
set -euo pipefail

EXEC_ROLE="ReLiC-CloudFormation-Execution"
POLICY_NAME="ReLiCCloudFrontResponseHeadersPolicy"

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

printf '\nCloudFront response headers policy permissions added to ReLiC CloudFormation execution role only.\n'
