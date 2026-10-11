import pytest

import observatory_ingest_lambda as bridge
from observatory import code_change


class FakeEcs:
    def __init__(self, tasks):
        self.tasks = tasks

    def list_tasks(self, **kwargs):
        assert kwargs["cluster"] == "relic-host"
        assert kwargs["family"] == "relic-host"
        assert kwargs["desiredStatus"] == "RUNNING"
        return {"taskArns": [task["taskArn"] for task in self.tasks]}

    def describe_tasks(self, **kwargs):
        return {"tasks": self.tasks, "failures": []}


class FakeSecrets:
    def __init__(self, token="test-write-token"):
        self.token = token
        self.requested = None

    def get_secret_value(self, **kwargs):
        self.requested = kwargs["SecretId"]
        return {"SecretString": self.token}


def envelope():
    item = code_change(
        repository="ryanlcole/DicePage",
        ref="refs/heads/relic-independent-service",
        commit="abc123",
        changed_paths=["services/relic-host/app.py"],
        actor="ryanlcole",
    )
    return {"fingerprint": item.fingerprint(), "event": item.event_payload()}


def task(task_id, revision, ip, started_at):
    return {
        "taskArn": f"arn:aws:ecs:us-east-1:797661578124:task/relic-host/{task_id}",
        "taskDefinitionArn": f"arn:aws:ecs:us-east-1:797661578124:task-definition/relic-host:{revision}",
        "lastStatus": "RUNNING",
        "startedAt": started_at,
        "attachments": [
            {
                "type": "ElasticNetworkInterface",
                "details": [
                    {"name": "privateIPv4Address", "value": ip},
                ],
            }
        ],
    }


def test_discovers_highest_running_task_revision():
    ecs = FakeEcs(
        [
            task("old", 6, "172.31.0.60", "2026-10-10T23:00:00Z"),
            task("current", 7, "172.31.0.82", "2026-10-11T00:00:00Z"),
            task("older", 4, "172.31.0.40", "2026-10-11T01:00:00Z"),
        ]
    )
    ip, arn = bridge.discover_host(ecs, cluster="relic-host", family="relic-host")
    assert ip == "172.31.0.82"
    assert arn.endswith("relic-host:7")


def test_no_running_task_is_rejected():
    ecs = FakeEcs([])
    with pytest.raises(RuntimeError, match="no running relic-host tasks"):
        bridge.discover_host(ecs, cluster="relic-host", family="relic-host")


def test_ingestion_revalidates_observation_and_keeps_canon_false(monkeypatch):
    ecs = FakeEcs([task("current", 7, "172.31.0.82", "2026-10-11T00:00:00Z")])
    secrets = FakeSecrets()

    captured = {}

    def fake_append(host, port, token, event):
        captured.update(host=host, port=port, token=token, event=event)
        return {"id": "event-1", "payload_hash": "hash-1", "append_only": True}

    monkeypatch.setattr(bridge, "append_private", fake_append)

    result = bridge.ingest_document(
        envelope(),
        ecs=ecs,
        secretsmanager=secrets,
        cluster="relic-host",
        family="relic-host",
        secret_arn="arn:aws:secretsmanager:us-east-1:797661578124:secret:relic/write-token-test",
    )

    assert captured["host"] == "172.31.0.82"
    assert captured["port"] == 8080
    assert captured["token"] == "test-write-token"
    assert captured["event"]["status"] == "OBSERVATION"
    assert result["stored"] is True
    assert result["observation_status"] == "OBSERVATION"
    assert result["canon_promoted"] is False


def test_canon_payload_is_rejected_before_secret_access(monkeypatch):
    document = envelope()
    document["event"]["status"] = "CANON"

    ecs = FakeEcs([task("current", 7, "172.31.0.82", "2026-10-11T00:00:00Z")])
    secrets = FakeSecrets()

    called = False

    def fake_append(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("append must not run")

    monkeypatch.setattr(bridge, "append_private", fake_append)

    with pytest.raises(ValueError, match="OBSERVATION"):
        bridge.ingest_document(
            document,
            ecs=ecs,
            secretsmanager=secrets,
            cluster="relic-host",
            family="relic-host",
            secret_arn="secret",
        )

    assert secrets.requested is None
    assert called is False


def test_missing_private_ip_is_rejected():
    broken = task("current", 7, "172.31.0.82", "2026-10-11T00:00:00Z")
    broken["attachments"][0]["details"] = []
    ecs = FakeEcs([broken])

    with pytest.raises(RuntimeError, match="private IPv4"):
        bridge.discover_host(ecs, cluster="relic-host", family="relic-host")
