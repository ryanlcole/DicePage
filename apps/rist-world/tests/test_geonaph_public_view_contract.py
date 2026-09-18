from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_geonaph_is_always_discoverable_as_viewer_or_owner():
    relationships = (ROOT / "WorldSession.WorldRelationships.cs").read_text(encoding="utf-8")
    assert "Geonaph is the shared MMO world." in relationships
    assert 'ownsGeonaph ? "owner" : "viewer"' in relationships


def test_endemar_worldbuilder_reference_is_viewable_but_mutations_require_trusted_authority():
    authority = (ROOT / "WorldSession.WorldAuthority.cs").read_text(encoding="utf-8")
    shell = (ROOT / "Components" / "PublicAlphaShell.razor").read_text(encoding="utf-8")
    host = (ROOT / "Components" / "WorldBuilderGeonaphHost.razor").read_text(encoding="utf-8")
    prototype = (ROOT / "wwwroot" / "prototype" / "prototype.js").read_text(encoding="utf-8")
    regions = (ROOT / "WorldSession.Regions.cs").read_text(encoding="utf-8")
    region_ui = (ROOT / "Components" / "RegionDefinerWorkspace.razor").read_text(encoding="utf-8")

    assert 'string.Equals(role, "GM", StringComparison.OrdinalIgnoreCase)' in authority
    assert 'string.Equals(role, "owner", StringComparison.OrdinalIgnoreCase)' in authority
    assert "bool CanBuildWorld=>WorldReady&&Session.HasTrustedWorldBuilderAuthority;" in shell
    assert "bool CanOpenWorldBuilder=>CanBuildWorld||(WorldReady&&Session.IsGeonaphWorld);" in shell
    assert "void OpenWorldbuilding(){if(!CanOpenWorldBuilder)return;" in shell
    assert "void OpenGameMaster(){if(!CanBuildWorld)return;" in shell

    assert 'var access=Session.HasTrustedWorldBuilderAuthority?"edit":"view";' in host
    assert "&access={access}" in host
    assert "const READ_ONLY=ACCESS_MODE!=='edit';" in prototype
    assert "if(READ_ONLY){announce('Endemar reference mode is view only.');return false;}" in prototype

    assert 'if (!HasTrustedWorldBuilderAuthority) throw new UnauthorizedAccessException("World Builder authority is required to define regions.");' in regions
    assert 'if (!HasTrustedWorldBuilderAuthority) throw new UnauthorizedAccessException("World Builder authority is required to save regions.");' in regions
    assert "bool CanEditRegion=>Session.HasTrustedWorldBuilderAuthority;" in region_ui
