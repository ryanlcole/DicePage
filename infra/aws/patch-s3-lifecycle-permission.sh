#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
EXEC_ROLE="ReLiC-CloudFormation-Execution"
POLICY_NAME="ReLiCCloudFormationExecution"
STACK_NAME="rist-frontend"

aws iam get-role-policy \
  --role-name "$EXEC_ROLE" \
  --policy-name "$POLICY_NAME" \
  --query PolicyDocument \
  --output json > /tmp/relic-cfn-policy.json

python3 - <<'PY'
import json
from pathlib import Path
p = Path('/tmp/relic-cfn-policy.json')
doc = json.loads(p.read_text())
changed = False
for stmt in doc.get('Statement', []):
    if stmt.get('Sid') == 'ReLiCStorage':
        actions = stmt.setdefault('Action', [])
        if isinstance(actions, str):
            actions = [actions]
            stmt['Action'] = actions
        for action in ('s3:PutLifecycleConfiguration', 's3:GetLifecycleConfiguration'):
            if action not in actions:
                actions.append(action)
                changed = True
        break
else:
    raise SystemExit('ReLiCStorage statement not found; refusing to broaden an unknown policy')
p.write_text(json.dumps(doc, separators=(',', ':')))
print('Lifecycle permission update prepared.' if changed else 'Lifecycle permissions already present.')
PY

aws iam put-role-policy \
  --role-name "$EXEC_ROLE" \
  --policy-name "$POLICY_NAME" \
  --policy-document file:///tmp/relic-cfn-policy.json

STATUS=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query 'Stacks[0].StackStatus' \
  --output text 2>/dev/null || true)

if [ "$STATUS" = "ROLLBACK_COMPLETE" ]; then
  echo "$STACK_NAME is ROLLBACK_COMPLETE; deleting failed shell before clean redeploy..."
  aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$REGION"
  aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$REGION"
  echo "Failed frontend stack shell deleted successfully."
fi

echo
echo "S3 lifecycle configuration permission added to ReLiC CloudFormation execution role only."
echo "Frontend is ready for a clean custom-domain redeploy."
