from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_geonaph_is_always_discoverable_as_viewer_or_owner():
    relationships = (ROOT / "WorldSession.WorldRelationships.cs").read_text(encoding="utf-8")
    assert "Geonaph is the shared MMO world." in relationships
    assert 'ownsGeonaph ? "owner" : "viewer"' in relationships


def test_worldbuilder_still_requires_trusted_gm_or_owner_authority():
    authority = (ROOT / "WorldSession.WorldAuthority.cs").read_text(encoding="utf-8")
    shell = (ROOT / "Components" / "PublicAlphaShell.razor").read_text(encoding="utf-8")
    assert 'string.Equals(role, "GM", StringComparison.OrdinalIgnoreCase)' in authority
    assert 'string.Equals(role, "owner", StringComparison.OrdinalIgnoreCase)' in authority
    assert "bool CanBuildWorld=>WorldReady&&Session.HasTrustedWorldBuilderAuthority;" in shell
    assert "void OpenWorldbuilding(){if(!CanBuildWorld)return;" in shell
    assert "void OpenGameMaster(){if(!CanBuildWorld)return;" in shell
