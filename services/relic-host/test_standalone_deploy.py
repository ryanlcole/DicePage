import pytest
import standalone_deploy as deploy


def test_preserves_public_ip_assignment_and_private_network():
    eni = {"SubnetId": "subnet-1", "Groups": [{"GroupId": "sg-1"}], "Association": {"PublicIp": "44.201.47.233"}}
    assert deploy.network_from_eni(eni)["awsvpcConfiguration"] == {
        "subnets": ["subnet-1"], "securityGroups": ["sg-1"], "assignPublicIp": "ENABLED"}
    del eni["Association"]
    assert deploy.network_from_eni(eni)["awsvpcConfiguration"]["assignPublicIp"] == "DISABLED"


@pytest.mark.parametrize("rule", [
    {"IpProtocol": "-1", "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
    {"IpProtocol": "tcp", "FromPort": 8080, "ToPort": 8080, "Ipv6Ranges": [{"CidrIpv6": "::/0"}]},
    {"IpProtocol": "tcp", "FromPort": 8000, "ToPort": 8000, "UserIdGroupPairs": [{"GroupId": "sg-source"}]},
    {"IpProtocol": "tcp", "FromPort": 1, "ToPort": 9000, "PrefixListIds": [{"PrefixListId": "pl-1"}]},
])
def test_rejects_exposed_ports(rule):
    with pytest.raises(RuntimeError):
        deploy.check_ingress([{"GroupId": "sg-1", "IpPermissions": [rule]}])


def test_allows_private_host_ingestion_only():
    deploy.check_ingress([{"GroupId": "sg-1", "IpPermissions": [
        {"IpProtocol": "tcp", "FromPort": 8080, "ToPort": 8080,
         "UserIdGroupPairs": [{"GroupId": "sg-private-lambda"}]}]}])


@pytest.mark.parametrize("fail_new", [False, True])
def test_rollout_stops_before_start_and_rolls_back_failures(monkeypatch, tmp_path, fail_new):
    old = {"taskArn": "old-task", "taskDefinitionArn": "rev9", "group": "family:relic-host"}
    network = {"awsvpcConfiguration": {}}
    monkeypatch.setattr(deploy.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(deploy, "inspect_standalone", lambda *args: (old, network))
    calls = []
    def aws(*args, payload=None):
        calls.append((args, payload))
        if args[:2] == ("ecs", "run-task"):
            return {"tasks": [{"taskArn": "new-task" if payload["taskDefinition"] == "rev10" else "restored-task"}]}
        if args[:2] == ("ecs", "list-tasks"):
            return {"taskArns": ["new-task"]}
        if args[:2] == ("ecs", "describe-tasks"):
            return {"tasks": [{"taskDefinitionArn": "rev10", "lastStatus": "RUNNING"}]}
        return {}
    def health(aws, cluster, task):
        if task == "new-task" and fail_new:
            raise RuntimeError("simulated startup failure")
    monkeypatch.setattr(deploy, "wait_healthy", health)
    if fail_new:
        with pytest.raises(RuntimeError, match="previous task definition restored HEALTHY"):
            deploy.rollout(aws, "cluster", old, network, "rev10", "us-east-1")
    else:
        deploy.rollout(aws, "cluster", old, network, "rev10", "us-east-1")
    assert calls[0][0][:2] == ("ecs", "stop-task")
    assert calls[1][0][:3] == ("ecs", "wait", "tasks-stopped")
    runs = [p for a, p in calls if a[:2] == ("ecs", "run-task")]
    assert [p["taskDefinition"] for p in runs] == (["rev10", "rev9"] if fail_new else ["rev10"])
    assert all(p["networkConfiguration"] == network for p in runs)
    assert len(list(tmp_path.glob("relic-rollback-*.json"))) == 1
