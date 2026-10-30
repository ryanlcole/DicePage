"""Run in an authorized AWS CloudShell to upgrade the existing private ECS service.

Requires AWS CLI, Docker, git, and the deployment permissions used for relic-host.
Does not print credentials or change network exposure, volumes, or tunnel config.
"""
import argparse
import copy
import json
import re
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path
# Importing deployment helpers must not dirty an otherwise clean checkout.
sys.dont_write_bytecode = True
import standalone_deploy


def aws(*args, payload=None):
    command = ["aws", "--region", REGION, *args, "--output", "json", "--no-cli-pager"]
    # AWS CLI file loaders can require a seekable file; /dev/stdin is a pipe.
    # NamedTemporaryFile is mode 0600 and is removed even on subprocess failure.
    with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8", suffix=".json") as request_file:
        if payload is not None:
            json.dump(payload, request_file)
            request_file.flush()
            command += ["--cli-input-json", "file://" + request_file.name]
        result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode:
        # Redact all submitted string values, including escaped representations,
        # before showing CLI errors that may echo an invalid request.
        values = []
        def collect(value):
            if isinstance(value, str) and value:
                values.extend([value, json.dumps(value)[1:-1]])
            elif isinstance(value, dict):
                for child in value.values(): collect(child)
            elif isinstance(value, list):
                for child in value: collect(child)
        collect(payload)
        detail = result.stderr or "No diagnostic returned"
        for value in sorted(set(values), key=len, reverse=True):
            detail = detail.replace(value, "[REDACTED]")
        raise RuntimeError(f"AWS operation failed: {' '.join(args[:2])}; exit {result.returncode}: {detail[:2000]}")
    return json.loads(result.stdout) if result.stdout.strip() else {}


def prepare_task(task, image, secret_arn):
    task = copy.deepcopy(task)
    if (task.get("runtimePlatform") or {}).get("cpuArchitecture", "X86_64") != "X86_64":
        raise ValueError("deployment image is built for X86_64; inspect task architecture")
    for key in ("taskDefinitionArn", "revision", "status", "requiresAttributes",
                "compatibilities", "registeredAt", "registeredBy", "deregisteredAt"):
        task.pop(key, None)
    containers = {c["name"]: c for c in task["containerDefinitions"]}
    if set(containers) != {"relic-host", "relic-mcp", "relic-tunnel"}:
        raise ValueError("unexpected container set; inspect deployment before proceeding")
    host, mcp = containers["relic-host"], containers["relic-mcp"]
    mounts = {m["containerPath"]: m for m in mcp.get("mountPoints", [])}
    if not mounts.get("/data", {}).get("readOnly"):
        raise ValueError("MCP /data mount must remain read-only")
    if any(s["name"] == "RELIC_WRITE_TOKEN" for s in mcp.get("secrets", [])):
        raise ValueError("MCP must not receive the general writer credential")
    if any(e["name"] in {"RELIC_WRITE_TOKEN", "RELIC_APPEND_TOKEN"} for e in mcp.get("environment", [])):
        raise ValueError("MCP credentials must come from Secrets Manager")
    for c in (host, mcp):
        c["image"] = image
        c["secrets"] = [s for s in c.get("secrets", []) if s["name"] != "RELIC_APPEND_TOKEN"]
        c["secrets"].append({"name": "RELIC_APPEND_TOKEN", "valueFrom": secret_arn})
    def env(c, values):
        c["environment"] = [e for e in c.get("environment", []) if e["name"] not in values]
        c["environment"] += [{"name": k, "value": v} for k, v in values.items()]
    env(host, {"RELIC_APPEND_PROJECTS": "RELIC_CORE,SOURCERORS",
               "RELIC_APPEND_ACTOR": "CHATGPT_PRIVATE_CONNECTOR"})
    env(mcp, {"RELIC_MCP_APPEND_ENABLED": "1"})
    return task


def main():
    global REGION
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--cluster", default="relic-host")
    parser.add_argument("--service", default="relic-host")
    parser.add_argument("--task", help="Replace this existing standalone task instead of an ECS service")
    parser.add_argument("--private-tunnel-confirmed", action="store_true",
                        help="Operator verified this is the existing private owner-scoped tunnel, not a public/shared MCP")
    args = parser.parse_args()
    REGION = args.region
    if not args.private_tunnel_confirmed:
        parser.error("verify the existing tunnel's private owner scope, then use --private-tunnel-confirmed")
    if aws("sts", "get-caller-identity")["Account"] != "797661578124":
        raise RuntimeError("wrong AWS account")
    root = Path(__file__).resolve().parent
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip():
        raise RuntimeError("deploy only a clean committed checkout")
    if args.task:
        old, network = standalone_deploy.inspect_standalone(aws, args.cluster, args.task)
        old_arn = old["taskDefinitionArn"]
        print("Standalone task and security-group checks passed; preparing replacement.", flush=True)
    else:
        services = aws("ecs", "describe-services", "--cluster", args.cluster, "--services", args.service)
        if services.get("failures") or len(services.get("services", [])) != 1:
            raise RuntimeError("existing ECS service not found; no infrastructure created")
        service = services["services"][0]
        if service["desiredCount"] != 1 or service.get("loadBalancers"):
            raise RuntimeError("expected one private task with no load balancer")
        old_arn = service["taskDefinition"]
    task = aws("ecs", "describe-task-definition", "--task-definition", old_arn)["taskDefinition"]
    # Validate the existing boundary before creating any cloud resources.
    prepare_task(task, "validation-only", "validation-only")
    repo = aws("ecr", "describe-repositories", "--repository-names", "relic-host")["repositories"][0]["repositoryUri"]
    tag = "continuity-" + revision
    image = repo + ":" + tag
    subprocess.run(["docker", "build", "--platform", "linux/amd64", "-t", image, str(root)], check=True)
    subprocess.run(["docker", "run", "--rm", "--entrypoint", "python", image,
                    "-c", "import app,mcp_server; app.init(); print('Container imports and isolated database initialization PASS')"], check=True)
    login = subprocess.run(["aws", "--region", REGION, "ecr", "get-login-password"], capture_output=True, check=True)
    subprocess.run(["docker", "login", "--username", "AWS", "--password-stdin", repo.split("/")[0]], input=login.stdout, check=True)
    subprocess.run(["docker", "push", image], check=True)
    digest = aws("ecr", "describe-images", "--repository-name", "relic-host", "--image-ids", "imageTag=" + tag)["imageDetails"][0]["imageDigest"]
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise RuntimeError("invalid image digest")
    # A separate capability secret; the legacy/general token is never fetched.
    secret_name = "relic/mcp-continuity-append"
    known = aws("secretsmanager", "list-secrets", "--filters", "Key=name,Values=" + secret_name)
    exact = [s for s in known.get("SecretList", []) if s["Name"] == secret_name]
    if exact:
        secret_arn = exact[0]["ARN"]
    else:
        secret_arn = aws("secretsmanager", "create-secret", payload={
            "Name": secret_name, "SecretString": secrets.token_urlsafe(48),
            "Description": "Private MCP continuity append only; not the general ReLiC writer",
        })["ARN"]
    role = task["executionRoleArn"].split("/")[-1]
    aws("iam", "put-role-policy", payload={"RoleName": role,
        "PolicyName": "ReLiCMcpContinuitySecret", "PolicyDocument": json.dumps({
            "Version": "2012-10-17", "Statement": [{"Effect": "Allow",
            "Action": "secretsmanager:GetSecretValue", "Resource": secret_arn}]})})
    new_task = prepare_task(task, repo + "@" + digest, secret_arn)
    new_arn = aws("ecs", "register-task-definition", payload=new_task)["taskDefinition"]["taskDefinitionArn"]
    print(json.dumps({"previous_task_definition": old_arn, "new_task_definition": new_arn,
                      "source_commit": revision, "image_digest": digest}))
    if args.task:
        standalone_deploy.rollout(aws, args.cluster, old, network, new_arn, REGION)
        print("Refresh MCP tools; verify append, retry, and retrieval before claiming end-to-end persistence.")
        return
    aws("ecs", "update-service", "--cluster", args.cluster, "--service", args.service,
        "--task-definition", new_arn, "--deployment-configuration",
        "minimumHealthyPercent=0,maximumPercent=100,deploymentCircuitBreaker={enable=true,rollback=true}")
    aws("ecs", "wait", "services-stable", "--cluster", args.cluster, "--services", args.service)
    live = aws("ecs", "describe-services", "--cluster", args.cluster, "--services", args.service)["services"][0]
    if live["taskDefinition"] != new_arn or live["runningCount"] != 1 or live["pendingCount"]:
        raise RuntimeError("deployment did not stabilize on requested revision; inspect ECS events")
    print("ECS rollout complete. Refresh MCP tools and verify append, exact retry, and get_event before claiming end-to-end success.")


if __name__ == "__main__":
    main()
