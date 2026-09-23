"""Regression firewall for duplicate RegionDefiner chooser rows.

Concurrent WorldSession loads previously cleared shared _regions, awaited the
same database and appended matching rows three times. The session must perform
the network read under one gate and commit a canonical snapshot atomically.
"""
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / "WorldSession.Regions.cs").read_text(encoding="utf-8")
START = SOURCE.index("public async Task LoadRegionsAsync()")
END = SOURCE.index("public void SetActiveRegion(", START)
LOAD = SOURCE[START:END]


def test_database_region_load_is_serialized_and_atomic():
    assert "readonly SemaphoreSlim _regionLoadGate = new(1, 1);" in SOURCE
    assert "await _regionLoadGate.WaitAsync();" in LOAD
    assert "_regionLoadGate.Release();" in LOAD
    assert LOAD.index("await _regionLoadGate.WaitAsync();") < LOAD.index("await authority.GetRegionsAsync(requestedWorldId)")
    assert LOAD.index("await authority.GetRegionsAsync(requestedWorldId)") < LOAD.index("_regions.Clear();\n            _regions.AddRange(canonicalRegions);")
    assert "var startingRevision = _regionLocalRevision;" in LOAD
    assert "startingRevision != _regionLocalRevision" in LOAD
    assert "requestedWorldId" in LOAD and "requestedUserId" in LOAD


def test_catalog_cannot_expose_repeated_database_region_ids():
    assert "DefinedRegions => CanonicalRegionRows(_regions).Where(IsDefinedRegion)" in SOURCE
    assert "GroupBy(x => x.RegionId, StringComparer.Ordinal)" in SOURCE
    assert "GroupBy(RegionSlotIdentity, StringComparer.Ordinal)" in SOURCE


def test_repeated_coordinates_in_different_zones_or_owners_remain_distinct():
    anchor = SOURCE[SOURCE.index("static string RegionSlotIdentity("):SOURCE.index("static string NormalizeRegionName(")]
    assert "region.WorldId" in anchor
    assert "region.ParentNodeId" in anchor
    assert "region.OwnerUserId" in anchor
    assert '"parcel:" + region.WorldId + ":" + region.ParcelId.Trim()' in anchor
