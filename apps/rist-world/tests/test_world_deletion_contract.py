from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_world_delete_requires_exact_user_phrase_and_owner():
    source = read("WorldSession.WorldDeletion.cs")
    phrase = "I Approve The Loss Of All Data For This World."
    assert phrase in source
    assert 'StringComparison.Ordinal' in source
    assert 'world.Relationship, "owner"' in source
    assert 'GeonaphWorldId' in source
    assert 'POST' not in source or 'HttpMethod.Post' in source
    assert '"/world/delete"' in source


def test_world_gate_exposes_delete_only_through_confirmation_dialog():
    source = read("Components/WorldGate.razor")
    assert "Session.CanDeleteWorld(world)" in source
    assert "WorldSession.WorldDeletionConfirmationPhrase" in source
    assert "DeleteApprovalMatches" in source
    assert "DELETE WORLD" in source
    assert "PERMANENT WORLD DELETION" in source


def test_backend_purges_versioned_world_prefix_and_fails_closed():
    source = (REPO / "infra/aws/rist-world-lifecycle.yml").read_text(encoding="utf-8")
    assert "POST /world/delete" in source
    assert "s3:ListBucketVersions" in source
    assert "s3:DeleteObjectVersion" in source
    assert "list_object_versions" in source
    assert 'relationship_of(target) != "owner"' in source
    assert 'world_id == GEONAPH_WORLD_ID' in source
    assert 'confirmation != CONFIRMATION' in source
    assert 'Authentication required' in source
