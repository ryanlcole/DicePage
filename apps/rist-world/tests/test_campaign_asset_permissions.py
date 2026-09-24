from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_every_placed_asset_persists_stable_authority_resource_identity():
    player = read("wwwroot/prototype/prototype.js")
    assert "function assetAuthorityResourceId(item)" in player
    assert "item.authorityResourceId=`asset:${id}`" in player
    assert "authorityResourceId:assetAuthorityResourceId(item)" in player
    assert "authorityResourceId:String(raw.authorityResourceId||'')" in player


def test_campaign_is_the_asset_permission_management_surface():
    campaign = read("Components/CampaignWorkspace.razor")
    assert "ASSET PERMISSIONS" in campaign
    assert "ALLY" in campaign
    assert "Waiting for GM" in campaign
    assert "GetResourcePermissionsAsync" in campaign
    assert "SetResourcePermissionAsync" in campaign
    assert "LoadWorldBuilderSourceAsync" in campaign
    assert "LoadRegionSourceAsync" in campaign
    assert "LoadLocalMapAsync" in campaign


def test_authority_client_exposes_resource_acl_endpoints():
    client = read("AwsAuthorityClient.cs")
    assert '"/world/resources/permissions?worldId="' in client
    assert '"/world/resources/permissions"' in client
    assert "ResourcePermission" in client
    assert "ResourcePermissionUpdate" in client


def test_resource_permissions_are_server_authoritative_and_connection_scoped():
    authority = (ROOT.parents[1] / "infra" / "aws" / "rist-platform-authority" / "app.py").read_text(encoding="utf-8")
    assert 'path == "/world/resources/permissions"' in authority
    assert "RESOURCE_PERMISSION_VALUES" in authority
    assert 'RESOURCE_PUBLIC_PRINCIPAL = "EVERYONE"' in authority
    assert "active_collaboration_connection" in authority
    assert "GameMaster permission authority required" in authority
    assert "Campaign → Allies" in authority
    assert '"resource.permission"' in authority
