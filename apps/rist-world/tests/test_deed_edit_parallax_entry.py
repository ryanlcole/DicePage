from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def text(path):
    return (REPO / path).read_text(encoding="utf-8")


def test_endemar_resolves_platform_owner_before_deed_map():
    mmo = text("apps/rist-world/Components/UniversalInterface.MmoMap.cs")
    assert "await Session.RefreshCommercialEntitlementsAsync();" in mmo
    assert "await Session.RefreshTrustedWorldAuthorityAsync();" in mmo
    assert "Session.TrustedPlatformOwner" in mmo


def test_edit_entry_requests_all_parallax():
    interface = text("apps/rist-world/Components/UniversalInterface.razor")
    assert 'deedEditParallax=access=="edit"' in interface
    assert "&deedEditParallax={deedEditParallax}" in interface


def test_selected_deed_uses_local_full_frame_and_truth_manifest():
    script = text("apps/rist-world/wwwroot/prototype/prototype.js")
    assert "DEED_EDIT_PARALLAX_START" in script
    assert "selectedDeedTruthManifestUrl" in script
    assert "applyDeedEditEntryView" in script
    assert "viewerTier='all';" in script
    assert "viewerLayer=9;" in script
    assert "isDeedLocalFullItem" in script
    assert "item.tier+(item.layer/10)" in script
    assert "truthMode?'truth-manifest':DEED_ZONE_ID" in script
    assert "const editableLayers=userLayers.filter(item=>!item.sourceLocked);" in script
