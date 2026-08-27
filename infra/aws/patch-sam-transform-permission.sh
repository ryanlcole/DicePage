#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
EXEC_ROLE="ReLiC-CloudFormation-Execution"
POLICY_NAME="ReLiCCloudFormationExecution"
TRANSFORM_ARN="arn:aws:cloudformation:${REGION}:aws:transform/Serverless-2016-10-31"

aws iam get-role-policy \
  --role-name "$EXEC_ROLE" \
  --policy-name "$POLICY_NAME" \
  --query PolicyDocument \
  --output json > /tmp/relic-cfn-exec-policy-current.json

python3 - <<PY
import json
from pathlib import Path
p = Path('/tmp/relic-cfn-exec-policy-current.json')
doc = json.loads(p.read_text())
statements = doc.setdefault('Statement', [])
sid = 'AllowSamTransformExpansion'
statements[:] = [s for s in statements if s.get('Sid') != sid]
statements.append({
    'Sid': sid,
    'Effect': 'Allow',
    'Action': 'cloudformation:CreateChangeSet',
    'Resource': '${TRANSFORM_ARN}'
})
Path('/tmp/relic-cfn-exec-policy-patched.json').write_text(json.dumps(doc, separators=(',', ':')))
PY

aws iam put-role-policy \
  --role-name "$EXEC_ROLE" \
  --policy-name "$POLICY_NAME" \
  --policy-document file:///tmp/relic-cfn-exec-policy-patched.json

aws iam get-role-policy \
  --role-name "$EXEC_ROLE" \
  --policy-name "$POLICY_NAME" \
  --query "PolicyDocument.Statement[?Sid=='AllowSamTransformExpansion']" \
  --output json

echo "SAM transform permission added to ReLiC CloudFormation execution role only."
