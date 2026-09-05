#!/usr/bin/env bash
set -euo pipefail

# One-shot repair for the already-created CloudFormation execution role.
# Run from AWS CloudShell at the repository root if the GitHub deploy role
# cannot change IAM itself. The full canonical policy remains in
# bootstrap-secure-deploy-roles.sh.

REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
ROLE="ReLiC-CloudFormation-Execution"
POLICY="ReLiCCloudFormationExecution"

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

aws iam get-role-policy \
  --role-name "$ROLE" \
  --policy-name "$POLICY" \
  --query PolicyDocument \
  --output json >"$TMP"

python - "$TMP" "$REGION" "$ACCOUNT_ID" <<'PY'
import json, sys
path, region, account = sys.argv[1:]
with open(path, encoding='utf-8') as f:
    policy = json.load(f)

def statement(sid):
    for item in policy.setdefault('Statement', []):
        if item.get('Sid') == sid:
            return item
    item = {'Sid': sid, 'Effect': 'Allow', 'Action': [], 'Resource': '*'}
    policy['Statement'].append(item)
    return item

def add_actions(sid, actions):
    item = statement(sid)
    current = item.get('Action', [])
    if isinstance(current, str):
        current = [current]
    item['Action'] = sorted(set(current) | set(actions))
    return item

lam = add_actions('ReLiCLambda', [
    'lambda:GetPolicy', 'lambda:ListVersionsByFunction',
    'lambda:EnableReplication*', 'lambda:DisableReplication*'
])
resources = lam.get('Resource', [])
if isinstance(resources, str): resources = [resources]
resources += [
    f'arn:aws:lambda:{region}:{account}:function:rist-*:*',
    f'arn:aws:lambda:{region}:{account}:function:relic-*:*'
]
lam['Resource'] = sorted(set(resources))

add_actions('ReLiCCloudFrontWaf', [
    'cloudfront:ListDistributions', 'cloudfront:ListOriginAccessControls',
    'cloudfront:CreateFunction', 'cloudfront:UpdateFunction',
    'cloudfront:DeleteFunction', 'cloudfront:DescribeFunction',
    'cloudfront:GetFunction', 'cloudfront:ListFunctions',
    'cloudfront:PublishFunction', 'cloudfront:CreateResponseHeadersPolicy',
    'cloudfront:UpdateResponseHeadersPolicy', 'cloudfront:DeleteResponseHeadersPolicy',
    'cloudfront:GetResponseHeadersPolicy', 'cloudfront:ListResponseHeadersPolicies'
])

slr = statement('ReLiCServiceLinkedRoles')
slr['Effect'] = 'Allow'
slr['Action'] = ['iam:CreateServiceLinkedRole', 'iam:GetServiceLinkedRoleDeletionStatus']
slr['Resource'] = '*'

with open(path, 'w', encoding='utf-8') as f:
    json.dump(policy, f, separators=(',', ':'))
PY

aws iam put-role-policy \
  --role-name "$ROLE" \
  --policy-name "$POLICY" \
  --policy-document "file://$TMP"

aws iam get-role-policy \
  --role-name "$ROLE" \
  --policy-name "$POLICY" \
  --query 'PolicyDocument.Statement[?Sid==`ReLiCLambda` || Sid==`ReLiCCloudFrontWaf` || Sid==`ReLiCServiceLinkedRoles`].[Sid,Action]' \
  --output json

echo "Edge-auth IAM repair applied to $ROLE."
