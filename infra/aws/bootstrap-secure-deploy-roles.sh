#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
CI_ROLE="RIST-GitHub-Deploy"
EXEC_ROLE="ReLiC-CloudFormation-Execution"
ARTIFACT_BUCKET="relic-deploy-artifacts-${ACCOUNT_ID}-${REGION}"
EXEC_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${EXEC_ROLE}"

cat >/tmp/relic-cfn-trust.json <<'JSON'
{
  "Version":"2012-10-17",
  "Statement":[{
    "Effect":"Allow",
    "Principal":{"Service":"cloudformation.amazonaws.com"},
    "Action":"sts:AssumeRole"
  }]
}
JSON

if aws iam get-role --role-name "$EXEC_ROLE" >/dev/null 2>&1; then
  aws iam update-assume-role-policy --role-name "$EXEC_ROLE" --policy-document file:///tmp/relic-cfn-trust.json
else
  aws iam create-role \
    --role-name "$EXEC_ROLE" \
    --assume-role-policy-document file:///tmp/relic-cfn-trust.json \
    --description "CloudFormation execution authority for ReLiC/RIST stacks" >/dev/null
fi

cat >/tmp/relic-cfn-exec-policy.json <<JSON
{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Sid":"ReLiCStorage",
      "Effect":"Allow",
      "Action":["s3:CreateBucket","s3:DeleteBucket","s3:GetBucket*","s3:PutBucket*","s3:DeleteBucketPolicy","s3:PutBucketPolicy","s3:ListBucket","s3:GetObject","s3:PutObject","s3:DeleteObject","s3:TagResource","s3:UntagResource"],
      "Resource":["arn:aws:s3:::rist-*","arn:aws:s3:::rist-*/*","arn:aws:s3:::relic-*","arn:aws:s3:::relic-*/*"]
    },
    {
      "Sid":"ReLiCDynamoDB",
      "Effect":"Allow",
      "Action":["dynamodb:CreateTable","dynamodb:DeleteTable","dynamodb:DescribeTable","dynamodb:UpdateTable","dynamodb:UpdateTimeToLive","dynamodb:DescribeTimeToLive","dynamodb:UpdateContinuousBackups","dynamodb:DescribeContinuousBackups","dynamodb:TagResource","dynamodb:UntagResource"],
      "Resource":["arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/rist-*","arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/relic-*"]
    },
    {
      "Sid":"ReLiCLambda",
      "Effect":"Allow",
      "Action":["lambda:CreateFunction","lambda:DeleteFunction","lambda:GetFunction","lambda:GetFunctionConfiguration","lambda:UpdateFunctionCode","lambda:UpdateFunctionConfiguration","lambda:AddPermission","lambda:RemovePermission","lambda:TagResource","lambda:UntagResource","lambda:PublishVersion","lambda:CreateAlias","lambda:UpdateAlias","lambda:DeleteAlias","lambda:GetAlias"],
      "Resource":["arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:rist-*","arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:relic-*"]
    },
    {
      "Sid":"ReLiCIamManagedRoles",
      "Effect":"Allow",
      "Action":["iam:CreateRole","iam:DeleteRole","iam:GetRole","iam:PutRolePolicy","iam:DeleteRolePolicy","iam:GetRolePolicy","iam:AttachRolePolicy","iam:DetachRolePolicy","iam:TagRole","iam:UntagRole","iam:PassRole"],
      "Resource":["arn:aws:iam::${ACCOUNT_ID}:role/rist-*","arn:aws:iam::${ACCOUNT_ID}:role/relic-*","arn:aws:iam::${ACCOUNT_ID}:role/ReLiC-*"]
    },
    {
      "Sid":"ReLiCKms",
      "Effect":"Allow",
      "Action":["kms:CreateKey","kms:DescribeKey","kms:EnableKeyRotation","kms:GetKeyRotationStatus","kms:CreateAlias","kms:UpdateAlias","kms:DeleteAlias","kms:PutKeyPolicy","kms:GetKeyPolicy","kms:TagResource","kms:UntagResource","kms:ScheduleKeyDeletion","kms:CancelKeyDeletion"],
      "Resource":"*"
    },
    {
      "Sid":"ReLiCApiGateway",
      "Effect":"Allow",
      "Action":["apigateway:*"],
      "Resource":"arn:aws:apigateway:${REGION}::*"
    },
    {
      "Sid":"ReLiCCloudFrontWaf",
      "Effect":"Allow",
      "Action":["cloudfront:CreateDistribution","cloudfront:UpdateDistribution","cloudfront:DeleteDistribution","cloudfront:GetDistribution","cloudfront:GetDistributionConfig","cloudfront:TagResource","cloudfront:UntagResource","cloudfront:CreateOriginAccessControl","cloudfront:UpdateOriginAccessControl","cloudfront:DeleteOriginAccessControl","cloudfront:GetOriginAccessControl","wafv2:CreateWebACL","wafv2:UpdateWebACL","wafv2:DeleteWebACL","wafv2:GetWebACL","wafv2:AssociateWebACL","wafv2:DisassociateWebACL","wafv2:TagResource","wafv2:UntagResource"],
      "Resource":"*"
    },
    {
      "Sid":"ReLiCSES",
      "Effect":"Allow",
      "Action":["ses:CreateReceiptRuleSet","ses:DeleteReceiptRuleSet","ses:CreateReceiptRule","ses:UpdateReceiptRule","ses:DeleteReceiptRule","ses:DescribeReceiptRuleSet","ses:SetActiveReceiptRuleSet","sesv2:CreateEmailIdentity","sesv2:DeleteEmailIdentity","sesv2:GetEmailIdentity","sesv2:PutEmailIdentityDkimAttributes"],
      "Resource":"*"
    },
    {
      "Sid":"ReLiCLogsAndTracing",
      "Effect":"Allow",
      "Action":["logs:CreateLogGroup","logs:DeleteLogGroup","logs:PutRetentionPolicy","logs:TagResource","logs:UntagResource","xray:PutTraceSegments","xray:PutTelemetryRecords"],
      "Resource":"*"
    }
  ]
}
JSON

aws iam put-role-policy \
  --role-name "$EXEC_ROLE" \
  --policy-name ReLiCCloudFormationExecution \
  --policy-document file:///tmp/relic-cfn-exec-policy.json

if ! aws s3api head-bucket --bucket "$ARTIFACT_BUCKET" >/dev/null 2>&1; then
  aws s3api create-bucket --bucket "$ARTIFACT_BUCKET" --region "$REGION" >/dev/null
fi
aws s3api put-public-access-block --bucket "$ARTIFACT_BUCKET" --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-encryption --bucket "$ARTIFACT_BUCKET" --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"},"BucketKeyEnabled":false}]}'
aws s3api put-bucket-lifecycle-configuration --bucket "$ARTIFACT_BUCKET" --lifecycle-configuration \
  '{"Rules":[{"ID":"ExpireDeploymentArtifacts","Status":"Enabled","Filter":{"Prefix":""},"Expiration":{"Days":30},"AbortIncompleteMultipartUpload":{"DaysAfterInitiation":1}}]}'

cat >/tmp/relic-github-ci-policy.json <<JSON
{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Sid":"CloudFormationControlPlane",
      "Effect":"Allow",
      "Action":["cloudformation:CreateStack","cloudformation:UpdateStack","cloudformation:DeleteStack","cloudformation:CreateChangeSet","cloudformation:ExecuteChangeSet","cloudformation:DeleteChangeSet","cloudformation:DescribeChangeSet","cloudformation:DescribeStacks","cloudformation:DescribeStackEvents","cloudformation:DescribeStackResources","cloudformation:DescribeStackResource","cloudformation:GetTemplate","cloudformation:GetTemplateSummary","cloudformation:ValidateTemplate"],
      "Resource":"*"
    },
    {
      "Sid":"PassOnlyReLiCExecutionRoleToCloudFormation",
      "Effect":"Allow",
      "Action":"iam:PassRole",
      "Resource":"${EXEC_ARN}",
      "Condition":{"StringEquals":{"iam:PassedToService":"cloudformation.amazonaws.com"}}
    },
    {
      "Sid":"DeploymentArtifacts",
      "Effect":"Allow",
      "Action":["s3:ListBucket","s3:GetBucketLocation"],
      "Resource":"arn:aws:s3:::${ARTIFACT_BUCKET}"
    },
    {
      "Sid":"DeploymentArtifactObjects",
      "Effect":"Allow",
      "Action":["s3:GetObject","s3:PutObject","s3:DeleteObject"],
      "Resource":"arn:aws:s3:::${ARTIFACT_BUCKET}/*"
    },
    {
      "Sid":"RuntimeAssetPublishing",
      "Effect":"Allow",
      "Action":["s3:ListBucket","s3:GetBucketLocation","s3:GetBucketEncryption","s3:GetLifecycleConfiguration"],
      "Resource":["arn:aws:s3:::rist-*","arn:aws:s3:::relic-*"]
    },
    {
      "Sid":"RuntimeAssetObjects",
      "Effect":"Allow",
      "Action":["s3:GetObject","s3:PutObject","s3:DeleteObject"],
      "Resource":["arn:aws:s3:::rist-*/*","arn:aws:s3:::relic-*/*"]
    },
    {
      "Sid":"DeploymentVerification",
      "Effect":"Allow",
      "Action":["cloudfront:CreateInvalidation","cloudfront:GetInvalidation","dynamodb:DescribeTable","dynamodb:DescribeTimeToLive","lambda:GetFunction","ses:DescribeActiveReceiptRuleSet","ses:SetActiveReceiptRuleSet","sesv2:GetEmailIdentity","sesv2:GetAccount"],
      "Resource":"*"
    }
  ]
}
JSON

aws iam put-role-policy \
  --role-name "$CI_ROLE" \
  --policy-name ReLiCDeploymentControlPlane \
  --policy-document file:///tmp/relic-github-ci-policy.json

printf '\nSecure ReLiC deployment bootstrap complete.\n'
printf 'Execution role: %s\n' "$EXEC_ARN"
printf 'Artifact bucket: %s\n' "$ARTIFACT_BUCKET"
printf 'GitHub role: %s\n' "$CI_ROLE"
printf 'CloudFormation now owns infrastructure execution; GitHub only controls deployments.\n'
