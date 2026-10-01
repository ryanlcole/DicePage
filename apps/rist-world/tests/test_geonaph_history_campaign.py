from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def text(path):
    return (REPO / path).read_text(encoding="utf-8")


def test_history_campaign_starts_at_lomekwi_without_inventing_species_or_language():
    data = json.loads(text("apps/rist-world/wwwroot/data/geonaph/history/campaign-v1.json"))
    region = data["zone"]["region"]
    local = region["local"]
    instance = local["instance"]
    joined = json.dumps(data).lower()

    assert data["canonicalExperience"]["sharedForAllPlayers"] is True
    assert data["canonicalExperience"]["factualMilestonesFixed"] is True
    assert data["canonicalExperience"]["factualOrderFixed"] is True
    assert data["corridor"]["owner"] == "Shaelvien"
    assert data["corridor"]["direction"] == "east"
    assert region["name"] == "West Turkana"
    assert local["name"] == "Lomekwi 3"
    assert "3.3" in local["chronology"]
    assert "taxonomic identity of the toolmakers is not established" in joined
    assert instance["languageContext"]["originalLanguageStatus"] == "UNATTESTED"
    assert instance["languageContext"]["transliteration"] == "NOT AVAILABLE"
    assert instance["languageContext"]["translation"] == "No historical translation exists."
    assert data["spriteSpecification"]["status"] == "EVIDENCE_SAFE_ART_V1"
    assert data["spriteSpecification"]["provenance"] == "RECONSTRUCTION"
    assert data["spriteSpecification"]["assetManifest"] == "data/geonaph/history/assets-v1.json"
    assert "controlled fire as a lomekwi 3 fact" in joined
    assert data["contentProfile"]["matureContent"] == "ALLOWED"
    assert data["contentProfile"]["presentation"] == "HISTORICAL_CONTEXT"
    assert data["contentProfile"]["provenanceIndependent"] is True


def test_history_tasks_only_use_lomekwi_supported_actions_and_keep_bridge_locked():
    data = json.loads(text("apps/rist-world/wwwroot/data/geonaph/history/campaign-v1.json"))
    instance = data["zone"]["region"]["local"]["instance"]
    tasks = instance["tasks"]
    labels = [task["label"] for task in tasks]

    assert "Batter" in labels
    assert "Reduce the core" in labels
    assert len(tasks) == 5
    assert instance["bridge"]["status"] == "LOCKED_UNTIL_NEXT_FACT_NODE_VERIFIED"
    assert instance["classification"] == "FACT"
    assert instance["playableReconstruction"]["classification"] == "RECONSTRUCTION"
    assert all(task["classification"] == "RECONSTRUCTION" for task in tasks)
    assert instance["bridge"]["classification"] == "FICTION"


def test_history_campaign_uses_universal_controller_instead_of_leaving_it():
    interface = text("apps/rist-world/Components/UniversalInterface.razor")
    mmo = text("apps/rist-world/Components/UniversalInterface.MmoMap.cs")
    history = text("apps/rist-world/Components/UniversalInterface.HistoryCampaign.cs")

    assert "Stage.HistoryCampaign" in interface
    assert "<GeonaphHistoryCampaign" in interface
    assert 'Stage.HistoryCampaign=>HistoryOpeningComplete?"Y · RECURSION":"Y · ARRIVAL"' in interface
    assert 'Stage.HistoryCampaign=>HistoryOpeningComplete?"X · TASKS":"X · ARRIVAL"' in interface
    assert "_mmoRoleplayerMode" in mmo
    assert "MmoSelectedIsCanonicalGeanaph" in mmo
    assert "EnterGeonaphHistoryCampaign();" in mmo
    assert "void HistoryApplyX" in history
    assert "void HistoryApplyY" in history
    assert "void HistoryPressLeft" in history
    assert "void HistoryPressRight" in history


def test_geanaph_database_seed_contains_region_local_instance_history_hierarchy():
    seed = text("infra/aws/rist-platform-geanaph-seed/app.py")
    template = text("infra/aws/rist-platform.yml")

    assert 'HISTORY_REGION_NODE_ID = "region-west-turkana"' in seed
    assert 'HISTORY_LOCAL_NODE_ID = "local-lomekwi-3"' in seed
    assert 'HISTORY_INSTANCE_NODE_ID = "instance-lom3-toolmaking-locality"' in seed
    assert '"name": "West Turkana"' in seed
    assert '"name": "Lomekwi 3"' in seed
    assert '"name": "LOM3 Tool-Making Locality"' in seed
    assert '"kind": "REGION"' in seed
    assert '"kind": "LOCAL"' in seed
    assert '"kind": "INSTANCE"' in seed
    assert '"historyHierarchyVerified": True' in seed
    assert '"historyProvenanceVerified": True' in seed
    assert '"historyContentPolicyVerified": True' in seed
    assert 'ZONE_NAME = "Geonaph"' in seed
    assert "is_geonaph_name" in seed
    assert seed.count('"provenance": "FACT"') >= 3
    assert '"matureContentAllowed": True' in seed
    assert '"provenanceIndependentOfRating": True' in seed
    assert "Revision: geonaph-east-v5-rating-provenance" in template


def test_history_context_keeps_original_translation_reconstruction_and_fiction_separate():
    component = text("apps/rist-world/Components/GeonaphHistoryCampaign.razor")
    data = json.loads(text("apps/rist-world/wwwroot/data/geonaph/history/campaign-v1.json"))
    language = data["zone"]["region"]["local"]["instance"]["languageContext"]

    assert "Original language" in component
    assert "Transliteration" in component
    assert "Translation" in component
    assert "FICTIONAL GAMEPLAY DIALOGUE" in component
    assert "FACT ≠ RECONSTRUCTION ≠ FICTION" in component
    assert language["classification"] == "FACT"
    assert language["originalLanguageStatus"] == "UNATTESTED"
    assert language["original"] == "No written or recorded language survives."
    assert language["fictionalDialogue"]["classification"] == "FICTION"


def test_history_provenance_and_content_policy_allow_only_evidence_safe_values():
    data = json.loads(text("apps/rist-world/wwwroot/data/geonaph/history/campaign-v1.json"))
    instance = data["zone"]["region"]["local"]["instance"]
    allowed = {"FACT", "RECONSTRUCTION", "FICTION"}

    assert data["zone"]["classification"] in allowed
    assert data["zone"]["region"]["classification"] in allowed
    assert data["zone"]["region"]["local"]["classification"] in allowed
    assert instance["classification"] in allowed
    assert instance["playableReconstruction"]["classification"] in allowed
    assert instance["languageContext"]["classification"] in allowed
    assert instance["bridge"]["classification"] in allowed
    assert all(task["classification"] in allowed for task in instance["tasks"])
    assert all(source["classification"] == "FACT" for source in data["sources"])
    assert data["contentProfile"]["ratingStatus"] == "UNRATED"
    assert data["contentProfile"]["matureContent"] == "ALLOWED"
    assert data["contentProfile"]["provenanceIndependent"] is True


def test_act1_scene1_preserves_traveler_backbone_truth_frame_and_physical_boundary():
    data = json.loads(text("apps/rist-world/wwwroot/data/geonaph/history/campaign-v1.json"))
    scene = data["act1"]["scene1"]
    ai = scene["aiRole"]
    backbone = data["playerBackbone"]
    frame = data["epistemicFrame"]
    history = text("apps/rist-world/Components/UniversalInterface.HistoryCampaign.cs")
    character = text("apps/rist-world/WorldSession.GeonaphCharacter.cs")
    access = text("apps/rist-world/ExternalAiAccess.cs")
    policy = json.loads(text("apps/rist-world/wwwroot/.well-known/relic-ai-policy.json"))

    assert data["act1"]["title"] == "Humanity Evolution 1"
    assert scene["title"] == "First Breath"
    assert scene["status"] == "PLAYABLE_V1"
    assert [step["label"] for step in scene["openingSteps"]] == [
        "THE FUTURE", "TRANSFORM", "FORGET", "AWAKEN", "LIVE"
    ]
    assert "immortality" in backbone["origin"].lower()
    assert "matter" in backbone["timeTravel"].lower()
    assert "near-total" in backbone["memory"].lower()
    assert "ends" in backbone["death"].lower()
    assert frame["claimsAbsoluteMetaphysicalTruth"] is False
    assert "perspective of human truth" in frame["rule"].lower()
    assert ai["canAuthorCanon"] is False
    assert ai["canRollDice"] is False
    assert ai["canCreateHistoricalFacts"] is False
    assert "audio/video only" in ai["roboticsBoundary"]
    assert "HistoryOpeningComplete" in history
    assert "PrepareGeonaphTravelerCharacter" in history
    assert "CharacterSpecies = \"\"" in character
    assert "no-robotic-embodiment" in access
    assert policy["physicalEmbodiment"]["roboticEmbodimentAllowed"] is False
    assert policy["physicalEmbodiment"]["physicalActuationAllowed"] is False
    assert policy["physicalEmbodiment"]["permittedExternalOutputs"] == ["audio", "video"]


def test_scene1_does_not_claim_a_species_language_or_future_knowledge():
    data = json.loads(text("apps/rist-world/wwwroot/data/geonaph/history/campaign-v1.json"))
    scene = data["act1"]["scene1"]
    joined = json.dumps(scene).lower()

    assert "taxonomic identity" in joined
    assert "language" in joined
    assert "cannot use unrestricted future knowledge" in joined
    assert scene["historicalAnchor"]["region"] == "West Turkana"
    assert scene["historicalAnchor"]["local"] == "Lomekwi 3"
