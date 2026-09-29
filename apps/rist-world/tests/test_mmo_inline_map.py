from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_mmo_map_flattens_only_tier_zero_top_surface_per_region_into_its_deed():
    component = text("Components/UniversalInterface.MmoMap.cs")
    interface = text("Components/UniversalInterface.razor")
    css = text("wwwroot/css/universal-interface.css")
    assert 'if (tier != 0) continue;' in component
    assert 'var topByRegion = new Dictionary<string, MmoSurfaceLayer>' in component
    assert 'layer.Layer > current.Layer' in component
    assert '_mmoSurfaceLayers.AddRange(topByRegion.Values' in component
    assert 'string? MmoCellSurfaceUrl(int cellIndex)' in component
    assert 'if (cellIndex == WorldSession.EndemarOriginCell)' in component
    assert 'return MmoCanonicalSurfaceUrl;' in component
    assert 'MmoCellSurfaceUrl(cell)' in interface
    assert 'class="mmo-deed-cell-surface"' in interface
    assert 'class="mmo-inline-map-base"' not in interface
    assert '.mmo-deed-cell-surface{' in css
    assert 'object-fit:contain;' in css


def test_mmo_view_extent_is_driven_by_created_world_and_frontier_without_artificial_margin():
    component = text("Components/UniversalInterface.MmoMap.cs")
    assert ': _mmoMapCells.Min(CellColumn);' in component
    assert ': _mmoMapCells.Max(CellColumn);' in component
    assert ': _mmoMapCells.Min(CellRow);' in component
    assert ': _mmoMapCells.Max(CellRow);' in component
    assert 'MmoBaseImageStyle' not in component
    assert 'MmoSurfaceLayerStyle' not in component


def test_mmo_map_includes_claimed_zones_and_all_open_flat_side_frontier_cells():
    component = text("Components/UniversalInterface.MmoMap.cs")
    land = text("WorldSession.MmoLand.cs")
    assert 'if (Session.IsMmoParcelOpen(cell))' in component
    assert '(0, -1)' in land
    assert '(1, 0)' in land
    assert '(0, 1)' in land
    assert '(-1, 0)' in land
    assert 'HasUnspentMmoWorldToken && IsMmoParcelOpen(cellIndex)' in land


def test_mmo_analog_moves_exactly_one_adjacent_zone_and_never_skips_a_gap():
    component = text("Components/UniversalInterface.MmoMap.cs")
    block = component[
        component.index("void MoveMmoSelection"):
        component.index("void CycleMmoLeftOption")
    ]
    assert 'CellColumn(_mmoSelectedCell) + dx' in block
    assert 'CellRow(_mmoSelectedCell) + dy' in block
    assert 'if (!_mmoMapCells.Contains(nextCell))' in block
    assert 'for (var step' not in block


def test_mmo_explore_actions_match_deed_state_and_token_state():
    component = text("Components/UniversalInterface.MmoMap.cs")
    assert 'return "MANAGE";' in component
    assert 'return "ROLEPLAY";' in component
    assert 'return "REQUEST DEED FROM GM";' in component
    assert 'return Session.HasUnspentMmoWorldToken ? "CLAIM DEED" : "PURCHASE TOKEN AND CLAIM DEED";' in component
    assert 'return $"USE 1/{count} TOKEN' in component
    assert 'return $"BID (CURRENT BID' in component


def test_known_canonical_shaelvien_roleplay_zones_are_not_treated_as_user_deed_management():
    component = text("Components/UniversalInterface.MmoMap.cs")
    assert 'MmoSelectedIsShaelvienRoleplayZone' in component
    assert '"The Sunken Tundra"' in component
    assert '"Sunken Tundra"' in component
    assert 'if (MmoSelectedIsShaelvienRoleplayZone)' in component


def test_mmo_left_rail_and_inspect_controls_match_the_universal_controller_contract():
    component = text("Components/UniversalInterface.MmoMap.cs")
    input_js = text("wwwroot/universal-interface-input.js")
    assert 'new("ENTER COORDINATES", "coordinates")' in component
    assert 'result.Add(new("ENTER USER ID", "user"))' in component
    assert '.Where(parcel => Session.IsMmoParcelOwnedByCurrentUser(parcel.CellIndex))' in component
    assert 'cleanupLeftSlider = bindDisplaySlider(leftSliderElement, "y", "left-slider")' in input_js
    assert 'cleanupRightSlider = bindDisplaySlider(rightSliderElement, "x", "right-slider")' in input_js


def test_endemar_relative_coordinates_put_north_above_and_west_left():
    component = text("Components/UniversalInterface.MmoMap.cs")
    assert 'var x = column - WorldSession.EndemarOriginColumn;' in component
    assert 'var y = WorldSession.EndemarOriginRow - row;' in component
    assert 'var left = (column - MmoViewMinColumn)' in component
    assert 'var top = (row - MmoViewMinRow)' in component


def test_sunken_tundra_seed_is_public_and_prefers_canonical_north_cell():
    seed = text("../../infra/aws/rist-platform-zone-seed/app.py")
    template = text("../../infra/aws/rist-platform.yml")
    assert 'ZONE_MARKER = "sunken-tundra-v4"' in seed
    assert 'parcel["visibility"] = "Public"' in seed
    assert 'int(pair[0].get("column") or 0) == 15' in seed
    assert 'int(pair[0].get("row") or 0) == 14' in seed
    assert 'Revision: sunken-tundra-v2' in template


def test_mmo_roleplay_action_hands_canonical_zone_to_player_workspace():
    component = text("Components/UniversalInterface.MmoMap.cs")
    interface = text("Components/UniversalInterface.razor")
    authenticated = text("Components/AuthenticatedWorld.razor")
    shell = text("Components/PublicAlphaShell.razor")

    assert 'EventCallback<string> OnRoleplay' in interface
    assert 'if (OnRoleplay.HasDelegate)' in component
    assert 'await OnRoleplay.InvokeAsync(MmoSelectedName);' in component
    assert 'OnRoleplay="EnterUniversalRoleplayAsync"' in authenticated
    assert 'EnterRoleplayOnFirstRender="_universalRoleplayPending"' in authenticated
    assert '[Parameter] public bool EnterRoleplayOnFirstRender' in shell
    assert 'if(EnterRoleplayOnFirstRender&&Session.IsGeonaphWorld)' in shell
    assert 'OpenRoleplay();' in shell
