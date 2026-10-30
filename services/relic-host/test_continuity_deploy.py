import copy
import pytest
from deploy_continuity import prepare_task


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
