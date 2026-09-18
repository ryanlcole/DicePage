#!/usr/bin/env python3
"""Report actual AWS access without changing IAM or exposing project records."""
import json
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

def main():
    region = 'us-east-1'
    stack = boto3.client('cloudformation', region_name=region).describe_stacks(StackName='rist-platform')['Stacks'][0]
    outputs = {x['OutputKey']: x['OutputValue'] for x in stack.get('Outputs', [])}
    table_name = outputs['WorldStateTableName']
    ddb = boto3.client('dynamodb', region_name=region)
    table = ddb.describe_table(TableName=table_name)['Table']
    if not table_name.startswith('rist-platform-WorldStateTable-'):
        raise ValueError('Unexpected database target')
    result = {'database': table_name, 'status': table['TableStatus'], 'partition': 'PROJECT#shaelvien',
              'importPerformed': False, 'keySchema': table['KeySchema']}
    try:
        ddb.get_item(TableName=table_name, Key={'pk': {'S': result['partition']},
                     'sk': {'S': 'KNOWLEDGE-MANIFEST'}}, ConsistentRead=True)
        result['readAccess'] = True
    except ClientError as exc:
        if exc.response['Error']['Code'] != 'AccessDeniedException':
            raise
        result.update(readAccess=False, blocker='Existing deployment role lacks dynamodb:GetItem; live import was not performed.')
    policy = {'Version': '2012-10-17', 'Statement': [
        {'Sid': 'DescribeProjectKnowledgeTable', 'Effect': 'Allow', 'Action': ['dynamodb:DescribeTable'],
         'Resource': table['TableArn']},
        {'Sid': 'OnlyShaelvienProjectKnowledge', 'Effect': 'Allow',
         'Action': ['dynamodb:GetItem', 'dynamodb:PutItem'], 'Resource': table['TableArn'],
         'Condition': {'ForAllValues:StringEquals': {'dynamodb:LeadingKeys': ['PROJECT#shaelvien']}}},
    ]}
    key_arn = (table.get('SSEDescription') or {}).get('KMSMasterKeyArn')
    if key_arn:
        policy['Statement'].append({'Sid': 'ProjectTableEncryptionOnly', 'Effect': 'Allow',
            'Action': ['kms:Decrypt', 'kms:Encrypt', 'kms:GenerateDataKey', 'kms:DescribeKey'],
            'Resource': key_arn, 'Condition': {'StringEquals': {'kms:ViaService': 'dynamodb.' + region + '.amazonaws.com'}}})
    Path('project-knowledge-preflight.json').write_text(json.dumps(result, indent=2) + '\n')
    Path('project-knowledge-required-access.json').write_text(json.dumps(policy, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))
    print('Proposed access policy (not applied): ' + json.dumps(policy, sort_keys=True))

if __name__ == '__main__':
    main()
