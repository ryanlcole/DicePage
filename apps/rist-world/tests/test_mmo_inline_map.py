from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_mmo_map_flattens_only_tier_zero_top_surface_per_region():
    component = text("Components/UniversalInterface.MmoMap.cs")
    assert 'if (tier != 0) continue;' in component
    assert 'var topByRegion = new Dictionary<string, MmoSurfaceLayer>' in component
    assert 'layer.Layer > current.Layer' in component
    assert '_mmoSurfaceLayers.AddRange(topByRegion.Values' in component


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
    assert 'ZONE_MARKER = "sunken-tundra-v2"' in seed
    assert 'parcel["visibility"] = "Public"' in seed
    assert 'int(pair[0].get("column") or 0) == 15' in seed
    assert 'int(pair[0].get("row") or 0) == 14' in seed
    assert 'Revision: sunken-tundra-v2' in template
