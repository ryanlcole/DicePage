#!/usr/bin/env bash
set -euo pipefail

REGION="us-east-1"
DOMAIN="relicgamemaster.com"

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
  if [ -n "$RECORDS" ]; then
    break
  fi
  sleep 2
done

STATUS=$(aws acm describe-certificate --region "$REGION" --certificate-arn "$CERT_ARN" --query 'Certificate.Status' --output text)

echo
echo "ACM certificate status: $STATUS"
echo "Certificate ARN: $CERT_ARN"
echo
echo "Add the following DNS validation CNAME record(s) in GoDaddy:"
aws acm describe-certificate \
  --region "$REGION" \
  --certificate-arn "$CERT_ARN" \
  --query 'Certificate.DomainValidationOptions[?ResourceRecord!=null].ResourceRecord.[Name,Type,Value]' \
  --output table

echo
echo "Do not delete those validation CNAME records after issuance; ACM uses DNS validation for managed renewal."
echo "Once ACM shows ISSUED, the frontend stack can be bound to relicgamemaster.com and www.relicgamemaster.com."
