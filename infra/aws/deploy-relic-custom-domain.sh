#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
STACK="rist-frontend"
DOMAIN="relicgamemaster.com"
CERT_ARN="arn:aws:acm:us-east-1:797661578124:certificate/e25800ef-28bc-43e3-8b75-aaefc0528375"
EXEC_ROLE="arn:aws:iam::797661578124:role/ReLiC-CloudFormation-Execution"
TEMPLATE_URL="https://raw.githubusercontent.com/ryanlcole/DicePage/live-alpha-rist-blazor-world/infra/aws/rist-frontend.yml"
TEMPLATE_FILE="/tmp/rist-frontend.yml"

STATUS=$(aws acm describe-certificate --certificate-arn "$CERT_ARN" --query 'Certificate.Status' --output text)
if [[ "$STATUS" != "ISSUED" ]]; then
  echo "Certificate is not ISSUED yet: $STATUS" >&2
  exit 1
fi

curl -fsSL "$TEMPLATE_URL" -o "$TEMPLATE_FILE"
aws cloudformation validate-template --template-body "file://$TEMPLATE_FILE" >/dev/null

if aws cloudformation describe-stacks --stack-name "$STACK" >/dev/null 2>&1; then
  STACK_STATUS=$(aws cloudformation describe-stacks --stack-name "$STACK" --query 'Stacks[0].StackStatus' --output text)
  if [[ "$STACK_STATUS" == "ROLLBACK_COMPLETE" ]]; then
    echo "Deleting failed $STACK stack shell..."
    aws cloudformation delete-stack --stack-name "$STACK"
    aws cloudformation wait stack-delete-complete --stack-name "$STACK"
  fi
fi

aws cloudformation deploy \
  --template-file "$TEMPLATE_FILE" \
  --stack-name "$STACK" \
  --region "$REGION" \
  --role-arn "$EXEC_ROLE" \
  --parameter-overrides \
    DomainName="$DOMAIN" \
    CertificateArn="$CERT_ARN" \
  --no-fail-on-empty-changeset

DIST_ID=$(aws cloudformation describe-stacks --stack-name "$STACK" --query "Stacks[0].Outputs[?OutputKey=='FrontendDistributionId'].OutputValue" --output text)
DIST_DOMAIN=$(aws cloudformation describe-stacks --stack-name "$STACK" --query "Stacks[0].Outputs[?OutputKey=='FrontendDistributionDomainName'].OutputValue" --output text)
BUCKET=$(aws cloudformation describe-stacks --stack-name "$STACK" --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" --output text)

cat <<EOF

ReLiC custom-domain frontend stack deployed.
Distribution ID: $DIST_ID
CloudFront domain: $DIST_DOMAIN
Frontend bucket: $BUCKET

GoDaddy DNS cutover targets:
  Apex (@): point to $DIST_DOMAIN using ALIAS/ANAME if available.
  www: create CNAME -> $DIST_DOMAIN

Keep the ACM validation CNAME permanently.
EOF
