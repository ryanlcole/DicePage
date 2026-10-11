"""Private AWS ingestion bridge for ReLiC Observatory.

Invoked through AWS IAM (normally GitHub OIDC). No public HTTP endpoint is
created. The bridge re-validates OBSERVATION-only evidence, discovers the
highest running relic-host task revision, retrieves the existing write
credential inside AWS, and appends to the private ReLiC host.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

try:
    from .validation import validate_envelope
except ImportError:  # AWS Lambda packages these modules at the function root.
    from validation import validate_envelope

_TASK_REVISION_RE = re.compile(r":(?P<revision>\d+)$")


def _task_revision(task_definition_arn: str) -> int:
    match = _TASK_REVISION_RE.search(task_definition_arn or "")
    return int(match.group("revision")) if match else -1


def _private_ipv4(task: dict[str, Any]) -> str:
    for attachment in task.get("attachments") or []:
        if attachment.get("type") != "ElasticNetworkInterface":
            continue
        for detail in attachment.get("details") or []:
            if detail.get("name") == "privateIPv4Address" and detail.get("value"):
                return str(detail["value"])
    raise RuntimeError("running relic-host task has no private IPv4 address")


def discover_host(ecs: Any, *, cluster: str, family: str) -> tuple[str, str]:
    response = ecs.list_tasks(cluster=cluster, family=family, desiredStatus="RUNNING")
    task_arns = response.get("taskArns") or []
    if not task_arns:
        raise RuntimeError("no running relic-host tasks found")

    described = ecs.describe_tasks(cluster=cluster, tasks=task_arns)
    failures = described.get("failures") or []
    if failures:
        reasons = ", ".join(str(item.get("reason") or "unknown") for item in failures)
        raise RuntimeError(f"ECS task discovery returned failures: {reasons}")

    tasks = [task for task in (described.get("tasks") or [])
             if task.get("lastStatus") == "RUNNING" and task.get("taskDefinitionArn")]
    if not tasks:
        raise RuntimeError("no describable RUNNING relic-host task found")

    tasks.sort(key=lambda task: (
        _task_revision(str(task.get("taskDefinitionArn") or "")),
        str(task.get("startedAt") or ""),
    ), reverse=True)
    chosen = tasks[0]
    return _private_ipv4(chosen), str(chosen["taskDefinitionArn"])


def load_write_token(secretsmanager: Any, secret_arn: str) -> str:
    response = secretsmanager.get_secret_value(SecretId=secret_arn)
    token = response.get("SecretString")
    if not token:
        raise RuntimeError("ReLiC write token secret has no SecretString")
    return str(token)


def append_private(host: str, port: int, token: str, event: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        f"http://{host}:{port}/v1/events",
        data=json.dumps(event, sort_keys=True).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"private ReLiC append failed with HTTP {exc.code}: {detail}") from exc


def ingest_document(document: dict[str, Any], *, ecs: Any, secretsmanager: Any,
                    cluster: str, family: str, secret_arn: str, port: int = 8080) -> dict[str, Any]:
    event = validate_envelope(document)
    host, task_definition_arn = discover_host(ecs, cluster=cluster, family=family)
    token = load_write_token(secretsmanager, secret_arn)
    stored = append_private(host, port, token, event)
    return {
        "stored": True,
        "id": stored.get("id"),
        "payload_hash": stored.get("payload_hash"),
        "task_definition_arn": task_definition_arn,
        "observation_status": event["status"],
        "canon_promoted": False,
    }


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    import boto3  # provided by the AWS Lambda Python runtime

    result = ingest_document(
        event,
        ecs=boto3.client("ecs"),
        secretsmanager=boto3.client("secretsmanager"),
        cluster=os.environ["RELIC_CLUSTER"],
        family=os.environ.get("RELIC_TASK_FAMILY", "relic-host"),
        secret_arn=os.environ["RELIC_WRITE_TOKEN_SECRET_ARN"],
        port=int(os.environ.get("RELIC_HOST_PORT", "8080")),
    )
    return result
