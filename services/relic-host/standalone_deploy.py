"""Replace one standalone Fargate task, preserving its network and rollback path."""
import json
import time
import uuid
from pathlib import Path


def one_task(aws, cluster, task_id):
    result = aws("ecs", "describe-tasks", "--cluster", cluster, "--tasks", task_id)
    if result.get("failures") or len(result.get("tasks", [])) != 1:
        raise RuntimeError("task could not be uniquely resolved")
    return result["tasks"][0]


def network_from_eni(eni):
    return {"awsvpcConfiguration": {
        "subnets": [eni["SubnetId"]],
        "securityGroups": [g["GroupId"] for g in eni["Groups"]],
        "assignPublicIp": "ENABLED" if (eni.get("Association") or {}).get("PublicIp") else "DISABLED",
    }}


def check_ingress(groups):
    # The tunnel shares the task network; MCP must not accept network ingress.
    # Host 8080 may accept trusted SG references for private Observatory ingestion.
    for group in groups:
        for rule in group.get("IpPermissions", []):
            protocol = rule.get("IpProtocol")
            if protocol not in {"-1", "tcp", "6"}:
                continue
            ports = (rule.get("FromPort", 0), rule.get("ToPort", 65535))
            sources = any(rule.get(k) for k in ("IpRanges", "Ipv6Ranges", "PrefixListIds", "UserIdGroupPairs"))
            if sources and (protocol == "-1" or ports[0] <= 8000 <= ports[1]):
                raise RuntimeError("MCP port 8000 permits network ingress; inspect SG " + group["GroupId"])
            if (protocol == "-1" or ports[0] <= 8080 <= ports[1]) and any(
                    rule.get(k) for k in ("IpRanges", "Ipv6Ranges", "PrefixListIds")):
                raise RuntimeError("host port 8080 has CIDR/prefix-list ingress; inspect SG " + group["GroupId"])


def inspect_standalone(aws, cluster, task_id):
    task = one_task(aws, cluster, task_id)
    if (task.get("group") != "family:relic-host" or task.get("launchType") != "FARGATE"
            or task.get("lastStatus") != "RUNNING" or task.get("healthStatus") != "HEALTHY"):
        raise RuntimeError("expected the healthy standalone relic-host Fargate task")
    current = aws("ecs", "list-tasks", "--cluster", cluster, "--family", "relic-host", "--desired-status", "RUNNING")["taskArns"]
    if current != [task["taskArn"]]:
        raise RuntimeError("expected exactly one active relic-host task")
    overrides = task.get("overrides") or {}
    if any(any(k != "name" and v for k, v in c.items()) for c in overrides.get("containerOverrides", [])):
        raise RuntimeError("container overrides require inspection before replacement")
    eni_ids = [d["value"] for a in task.get("attachments", []) for d in a.get("details", [])
               if d["name"] == "networkInterfaceId"]
    if len(eni_ids) != 1:
        raise RuntimeError("expected one task ENI")
    eni = aws("ec2", "describe-network-interfaces", "--network-interface-ids", eni_ids[0])["NetworkInterfaces"][0]
    network = network_from_eni(eni)
    groups = aws("ec2", "describe-security-groups", "--group-ids", *network["awsvpcConfiguration"]["securityGroups"])["SecurityGroups"]
    check_ingress(groups)
    return task, network


def wait_healthy(aws, cluster, task_id, timeout=600):
    deadline = time.monotonic() + timeout
    consecutive = 0
    while time.monotonic() < deadline:
        task = one_task(aws, cluster, task_id)
        if task["lastStatus"] == "STOPPED":
            raise RuntimeError("replacement stopped; inspect ECS task " + task_id)
        good = task["lastStatus"] == "RUNNING" and task.get("healthStatus") == "HEALTHY"
        consecutive = consecutive + 1 if good else 0
        if consecutive >= 3:
            return
        print("Waiting for task health:", task["lastStatus"], task.get("healthStatus", "UNKNOWN"), flush=True)
        time.sleep(10)
    raise RuntimeError("task did not become stably healthy before timeout")


def rollout(aws, cluster, old, network, new_arn, region):
    # Re-read immediately before stopping: a stale plan must not stop a newer task.
    fresh, fresh_network = inspect_standalone(aws, cluster, old["taskArn"])
    if fresh["taskDefinitionArn"] != old["taskDefinitionArn"] or fresh_network != network:
        raise RuntimeError("running task changed during preparation; nothing stopped")
    request = {"cluster": cluster, "launchType": "FARGATE", "count": 1,
               "networkConfiguration": network, "group": old["group"],
               "platformVersion": old.get("platformVersion", "LATEST"),
               "enableExecuteCommand": old.get("enableExecuteCommand", False)}
    rollback_request = {**request, "taskDefinition": old["taskDefinitionArn"], "clientToken": str(uuid.uuid4())}
    rollback_file = Path.home() / ("relic-rollback-" + str(uuid.uuid4()) + ".json")
    with rollback_file.open("x") as handle:
        json.dump(rollback_request, handle, indent=2)
    rollback_file.chmod(0o600)
    print("Rollback request saved:", rollback_file, flush=True)
    print("Stopping old task before starting replacement; brief continuity downtime begins.", flush=True)
    aws("ecs", "stop-task", "--cluster", cluster, "--task", old["taskArn"], "--reason", "Authorized scoped continuity writer upgrade")
    aws("ecs", "wait", "tasks-stopped", "--cluster", cluster, "--tasks", old["taskArn"])
    replacement_request = {**request, "taskDefinition": new_arn, "clientToken": str(uuid.uuid4())}
    try:
        result = aws("ecs", "run-task", payload=replacement_request)
    except Exception:
        # Retry the same ECS idempotency token to resolve an uncertain response.
        # If AWS is still unreachable, do not risk starting a second writer.
        try:
            result = aws("ecs", "run-task", payload=replacement_request)
        except Exception:
            raise RuntimeError("replacement outcome UNKNOWN; inspect ECS before rollback using " + str(rollback_file)) from None
    replacement = None
    try:
        if len(result.get("tasks", [])) != 1:
            raise RuntimeError("run-task did not return one replacement")
        replacement = result["tasks"][0]["taskArn"]
        print("Replacement task:", replacement, flush=True)
        if result.get("failures"):
            raise RuntimeError("run-task reported failures")
        wait_healthy(aws, cluster, replacement)
    except Exception:
        # Fail closed on ambiguous cleanup instead of starting a second writer.
        active = aws("ecs", "list-tasks", "--cluster", cluster, "--family", "relic-host", "--desired-status", "RUNNING")["taskArns"]
        if replacement and replacement not in active:
            active.append(replacement)
        for task_id in active:
            task = one_task(aws, cluster, task_id)
            if task["taskDefinitionArn"] != new_arn:
                raise RuntimeError("unexpected concurrent task; manual rollback required: " + str(rollback_file))
            if task["lastStatus"] != "STOPPED":
                aws("ecs", "stop-task", "--cluster", cluster, "--task", task_id, "--reason", "Rollback failed continuity upgrade")
                aws("ecs", "wait", "tasks-stopped", "--cluster", cluster, "--tasks", task_id)
        restored = aws("ecs", "run-task", payload=rollback_request)
        if restored.get("failures") or len(restored.get("tasks", [])) != 1:
            raise RuntimeError("automatic rollback failed; request saved at " + str(rollback_file))
        restored_id = restored["tasks"][0]["taskArn"]
        wait_healthy(aws, cluster, restored_id)
        raise RuntimeError("upgrade failed; previous task definition restored HEALTHY: " + restored_id) from None
    print(json.dumps({"status": "HEALTHY", "task": replacement, "task_definition": new_arn,
                      "end_to_end_append_verified": False}), flush=True)
