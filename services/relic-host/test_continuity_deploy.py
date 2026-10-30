import copy
import json
import os
from pathlib import Path
from types import SimpleNamespace
import pytest
import deploy_continuity as deployment
from deploy_continuity import prepare_task


@pytest.mark.parametrize("fail", [False, True])
def test_cli_payload_uses_private_seekable_file_and_cleans_up(monkeypatch, fail):
    monkeypatch.setattr(deployment, "REGION", "us-east-1", raising=False)
    observed = []
    secret = "test-secret-do-not-display"
    def run(command, **kwargs):
        path = Path(command[command.index("--cli-input-json") + 1].removeprefix("file://"))
        observed.append(path)
        assert os.stat(path).st_mode & 0o777 == 0o600
        with path.open() as handle:
            assert handle.seekable()
            assert json.load(handle)["SecretString"] == secret
        assert "input" not in kwargs
        return SimpleNamespace(returncode=252 if fail else 0, stdout='{"ARN":"test-arn"}',
                               stderr="Invalid input: " + secret)
    monkeypatch.setattr(deployment.subprocess, "run", run)
    if fail:
        with pytest.raises(RuntimeError) as exc:
            deployment.aws("secretsmanager", "create-secret", payload={"SecretString": secret})
        assert secret not in str(exc.value)
        assert "[REDACTED]" in str(exc.value)
    else:
        assert deployment.aws("secretsmanager", "create-secret", payload={"SecretString": secret}) == {"ARN": "test-arn"}
    assert not observed[0].exists()


def fixture():
    return {"family": "relic-host", "revision": 8, "networkMode": "awsvpc",
            "volumes": [{"name": "data", "efsVolumeConfiguration": {"fileSystemId": "test"}}],
            "containerDefinitions": [
                {"name": "relic-host", "image": "old", "mountPoints": [{"containerPath": "/data", "readOnly": False}],
                 "secrets": [{"name": "RELIC_WRITE_TOKEN", "valueFrom": "general-secret"}]},
                {"name": "relic-mcp", "image": "old", "mountPoints": [{"containerPath": "/data", "readOnly": True}]},
                {"name": "relic-tunnel", "image": "tunnel", "command": ["unchanged"]}]}


def test_preserves_storage_tunnel_and_general_secret():
    original = fixture(); before = copy.deepcopy(original)
    result = prepare_task(original, "image@sha256:test", "scoped-secret")
    assert original == before
    assert result["volumes"] == original["volumes"]
    assert result["containerDefinitions"][2] == original["containerDefinitions"][2]
    assert result["containerDefinitions"][0]["secrets"][0]["valueFrom"] == "general-secret"
    assert result["containerDefinitions"][1]["mountPoints"][0]["readOnly"]
    assert "revision" not in result


def test_rejects_unsafe_or_unknown_task():
    task = fixture(); task["containerDefinitions"][1]["mountPoints"][0]["readOnly"] = False
    with pytest.raises(ValueError): prepare_task(task, "image", "secret")
    task = fixture(); task["runtimePlatform"] = {"cpuArchitecture": "ARM64"}
    with pytest.raises(ValueError): prepare_task(task, "image", "secret")
    task = fixture(); task["containerDefinitions"][1]["secrets"] = [{"name": "RELIC_WRITE_TOKEN", "valueFrom": "secret"}]
    with pytest.raises(ValueError): prepare_task(task, "image", "secret")
