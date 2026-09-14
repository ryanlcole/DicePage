import json
import urllib.request

import boto3

s3 = boto3.client("s3")
NOTIFICATION_ID = "shaep-normalizer-manifest-created"


def _send(event, context, status, data=None, physical_id=None, reason=None):
    body = {
        "Status": status,
        "Reason": reason or f"See CloudWatch Log Stream: {context.log_stream_name}",
        "PhysicalResourceId": physical_id or event.get("PhysicalResourceId") or NOTIFICATION_ID,
        "StackId": event["StackId"],
        "RequestId": event["RequestId"],
        "LogicalResourceId": event["LogicalResourceId"],
        "NoEcho": False,
        "Data": data or {},
    }
    payload = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        event["ResponseURL"],
        data=payload,
        method="PUT",
        headers={"content-type": "", "content-length": str(len(payload))},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        response.read()


def _clean_configuration(raw):
    return {
        key: raw[key]
        for key in (
            "TopicConfigurations",
            "QueueConfigurations",
            "LambdaFunctionConfigurations",
            "EventBridgeConfiguration",
        )
        if key in raw
    }


def handler(event, context):
    props = event.get("ResourceProperties") or {}
    bucket = props.get("BucketName")
    target_arn = props.get("FunctionArn")
    physical_id = f"{NOTIFICATION_ID}:{bucket}"
    try:
        if not bucket:
            raise ValueError("BucketName is required")

        current = _clean_configuration(s3.get_bucket_notification_configuration(Bucket=bucket))
        lambdas = [
            item
            for item in current.get("LambdaFunctionConfigurations", [])
            if item.get("Id") != NOTIFICATION_ID
        ]

        if event.get("RequestType") != "Delete":
            if not target_arn:
                raise ValueError("FunctionArn is required")
            lambdas.append(
                {
                    "Id": NOTIFICATION_ID,
                    "LambdaFunctionArn": target_arn,
                    "Events": ["s3:ObjectCreated:*"],
                    "Filter": {
                        "Key": {
                            "FilterRules": [
                                {"Name": "suffix", "Value": ".shaep"},
                            ]
                        }
                    },
                }
            )

        if lambdas:
            current["LambdaFunctionConfigurations"] = lambdas
        else:
            current.pop("LambdaFunctionConfigurations", None)

        s3.put_bucket_notification_configuration(
            Bucket=bucket,
            NotificationConfiguration=current,
        )
        _send(
            event,
            context,
            "SUCCESS",
            {"BucketName": bucket, "NotificationId": NOTIFICATION_ID},
            physical_id,
        )
    except Exception as exc:
        _send(event, context, "FAILED", physical_id=physical_id, reason=str(exc)[:1000])
        raise
