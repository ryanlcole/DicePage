from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_endemar_reuses_existing_sumaria_and_prepares_city_without_recreating_region():
    regions = (ROOT / "WorldSession.Regions.cs").read_text(encoding="utf-8")
    mmo = (ROOT / "Components/UniversalInterface.MmoMap.cs").read_text(encoding="utf-8")

    assert 'EndemarRegionDisplayName = "Sumaria"' in regions
    assert 'EndemarCityDisplayName = "The Great City of Atsumaritas"' in regions
    assert "PrepareEndemarThroughCityAsync" in regions
    assert "Existing Endemar Region" in regions
    assert "No replacement Region was created." in regions
    assert "CreateRegionAsync(" not in regions[
        regions.index("public async Task<EndemarHierarchySetupResult> PrepareEndemarThroughCityAsync()"):
        regions.index("public async Task<WorldSpatialNode> CreateSpatialNodeAsync(")
    ]
    assert "ParentNodeId: region.RegionId" in regions
    assert "CityMetadataCreated" in regions
    assert "await Session.PrepareEndemarThroughCityAsync()" in mmo


def test_local_can_continue_directly_inside_old_worldregion_or_legacy_nested_region():
    regions = (ROOT / "WorldSession.Regions.cs").read_text(encoding="utf-8")

    assert 'ActiveSpatialRegion?.NodeId ?? ActiveRegion?.RegionId ?? ""' in regions
    assert '"LOCAL" => authorityRegion.RegionId' in regions
    assert "legacyParentRegion" in regions
    assert "_activeSpatialRegionId = legacyParentRegion?.NodeId ?? "";" in regions


def test_controller_breadcrumb_and_asset_identity_show_endemar_sumaria_city_chain():
    component = (ROOT / "Components/UniversalInterface.razor").read_text(encoding="utf-8")

    assert '"REGION"=>Session.ActiveRegion?.RegionId??""' in component
    assert "Session.ActiveRegion?.RegionId," in component
    assert "if(Session.ActiveRegion is not null)labels.Add(Session.ActiveRegion.Name);" in component
    assert 'CurrentBuilderScope=="LOCAL"&&Session.ActiveLocal is not null' in component
    assert "Session.ActiveLocal.Name" in component


def test_endemar_hierarchy_setup_can_never_block_owner_edit_entry():
    regions = (ROOT / "WorldSession.Regions.cs").read_text(encoding="utf-8")
    mmo = (ROOT / "Components/UniversalInterface.MmoMap.cs").read_text(encoding="utf-8")

    assert "!HasTrustedWorldBuilderAuthority && !OwnsCanonicalGeonaphZone" in regions
    assert "OwnsCanonicalGeonaphZone" in regions[
        regions.index("public bool CanEditRegion"):
        regions.index("static string NormalizeRegionName")
    ]

    method = mmo[
        mmo.index("async Task OpenMmoGameMasterAsync()"):
        mmo.index("async Task EnterMmoInspectSelectionAsync()")
    ]
    catch_start = method.index("catch (Exception ex)")
    catch_end = method.index("}", catch_start)
    catch_body = method[catch_start:catch_end]
    assert "endemarSetupError" in catch_body
    assert "return;" not in catch_body
    assert "World Builder remains editable" in method
