import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_shaep_is_spatial_manifest_not_codec():
    model = read("ShaepManifest.cs")
    docs = read("SHAEP_FORMAT.md")
    assert 'public const string Name = "SHAEP"' in model
    assert 'public const int CurrentVersion = 1' in model
    assert 'public const string FileExtension = ".shaep"' in model
    assert 'application/vnd.shaelvien.shaep+json' in model
    assert "SHAEP is **not a codec**" in docs
    assert "viewer owns the grid" in docs.lower()


def test_shaep_keeps_identity_separate_from_integrity_hash():
    codec = read("ShaepCodec.cs")
    docs = read("SHAEP_FORMAT.md")
    assert 'var id = $"shaep-{Guid.NewGuid():N}"' in codec
    assert "`Sha256` is optional integrity evidence for a payload" in docs
    assert "same checksum without becoming the same object" in docs
    assert "hash.Length != 64" in codec


def test_shaep_spatial_contract_has_rist_depth_and_footprint():
    model = read("ShaepManifest.cs")
    for token in (
        "double X",
        "double Y",
        "int CubeX",
        "int CubeY",
        "int CubeZ",
        "int PlaneIndex",
        "int ZTier",
        "int ZLayer",
        "int WidthCells",
        "int HeightCells",
    ):
        assert token in model


def test_shaep_hot_canonical_is_created_for_user_upload_catalogs():
    user_assets = read("WorldSession.UserAssets.cs")
    codec = read("ShaepCodec.cs")
    assert "EnsureShaepEntriesAsync" in user_assets
    assert "SaveShaepManifestAsync" in user_assets
    assert "ShaepFormat.HotStorageState" in codec
    assert "ShaepFormat.PendingNormalization" in codec
    assert 'return $"uploads/shaep/{safe}/manifest{ShaepFormat.FileExtension}";' in codec


def test_world_placements_preserve_shaep_identity():
    models = read("WorldSession.Models.cs")
    interactions = read("Components/WorldBuilderStudio.Interactions.cs")
    assert len(re.findall(r'string\s+ShaepId\s*=\s*""', models)) >= 2
    assert "ShaepId = Session.ResolveShaepId(tile)" in interactions
    assert "ResolveShaepId(AtlasTile tile)" in read("WorldSession.UserAssets.cs")


def test_runtime_derivatives_are_disposable_and_archive_transition_keeps_identity():
    docs = read("SHAEP_FORMAT.md")
    assert "Runtime thumbnails, resized images, decoded frames, texture atlases and viewer composites" in docs
    assert "storage-class transition does not change SHAEP identity" in docs
