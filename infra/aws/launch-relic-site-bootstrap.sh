#!/usr/bin/env bash
set -euo pipefail

EXEC_ROLE="ReLiC-CloudFormation-Execution"
REGION="us-east-1"
DOMAIN="relicgamemaster.com"

cat >/tmp/relic-frontend-s3-encryption.json <<'JSON'
{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Sid":"AllowFrontendBucketEncryptionConfiguration",
      "Effect":"Allow",
      "Action":["s3:PutEncryptionConfiguration","s3:GetEncryptionConfiguration"],
      "Resource":["arn:aws:s3:::rist-*","arn:aws:s3:::relic-*"]
    }
  ]
}
JSON

aws iam put-role-policy \
  --role-name "$EXEC_ROLE" \
  --policy-name ReLiCFrontendS3Encryption \
  --policy-document file:///tmp/relic-frontend-s3-encryption.json

echo "Frontend S3 encryption permission verified."

if STATUS=$(aws cloudformation describe-stacks --stack-name rist-frontend --query 'Stacks[0].StackStatus' --output text 2>/dev/null); then
  if [ "$STATUS" = "ROLLBACK_COMPLETE" ]; then
    echo "Deleting failed rist-frontend stack shell..."
    aws cloudformation delete-stack --stack-name rist-frontend
    aws cloudformation wait stack-delete-complete --stack-name rist-frontend
    echo "Failed frontend shell deleted."
  fi
fi

CERT_ARN=$(aws acm list-certificates \
  --region "$REGION" \
  --certificate-statuses PENDING_VALIDATION ISSUED \
  --query "CertificateSummaryList[?DomainName=='${DOMAIN}'].CertificateArn | [0]" \
  --output text)

if [ -z "$CERT_ARN" ] || [ "$CERT_ARN" = "None" ]; then
  CERT_ARN=$(aws acm request-certificate \
    --region "$REGION" \
    --domain-name "$DOMAIN" \
    --subject-alternative-names "*.${DOMAIN}" \
    --validation-method DNS \
    --options CertificateTransparencyLoggingPreference=ENABLED \
    --query CertificateArn \
    --output text)
  echo "Requested ACM certificate: $CERT_ARN"
else
  echo "Using existing ACM certificate: $CERT_ARN"
fi

for i in $(seq 1 30); do
  RECORDS=$(aws acm describe-certificate \
    --region "$REGION" \
    --certificate-arn "$CERT_ARN" \
    --query 'Certificate.DomainValidationOptions[?ResourceRecord!=null].ResourceRecord.[Name,Type,Value]' \
    --output text || true)
  [ -n "$RECORDS" ] && break
  sleep 2
done

STATUS=$(aws acm describe-certificate --region "$REGION" --certificate-arn "$CERT_ARN" --query 'Certificate.Status' --output text)

echo
echo "ReLiC site launch bootstrap complete."
echo "Certificate ARN: $CERT_ARN"
echo "Certificate status: $STATUS"
echo
echo "GoDaddy ACM validation record(s):"
aws acm describe-certificate \
  --region "$REGION" \
  --certificate-arn "$CERT_ARN" \
  --query 'Certificate.DomainValidationOptions[?ResourceRecord!=null].ResourceRecord.[Name,Type,Value]' \
  --output table

echo
echo "Keep the validation CNAME record permanently so ACM can auto-renew the certificate."
echo "After DNS validation reaches ISSUED, bind the frontend stack to ${DOMAIN}."
