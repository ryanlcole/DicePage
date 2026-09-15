import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_shaep_v2_is_converted_hot_av_archive_contract():
    model = read("ShaepManifest.cs")
    docs = read("SHAEP_FORMAT.md")
    assert 'public const string Name = "SHAEP"' in model
    assert 'public const int LegacyVersion = 1' in model
    assert 'public const int CurrentVersion = 2' in model
    assert 'public const string FileExtension = ".shaep"' in model
    assert 'application/vnd.shaelvien.shaep"' in model
    assert 'application/vnd.shaelvien.shaep+json' in model
    assert 'public sealed record ShaepHotArchiveContract' in model
    assert "converted hot audiovisual archive format" in docs
    assert "not merely a manifest" in docs
    assert "server stores truth; the viewer produces perception" in docs.lower()


def test_shaep_archive_has_separate_metadata_and_binary_targets():
    codec = read("ShaepCodec.cs")
    docs = read("SHAEP_FORMAT.md")
    assert 'return $"uploads/shaep/{safe}/{ShaepFormat.ManifestFileName}";' in codec
    assert 'return $"uploads/shaep/{safe}/archive{ShaepFormat.FileExtension}";' in codec
    assert 'return $"uploads/shaep/{safe}/archive.index.json";' in codec
    assert "manifest.json" in docs
    assert "archive.shaep" in docs
    assert "archive.index.json" in docs


def test_shaep_keeps_identity_separate_from_integrity_hash():
    codec = read("ShaepCodec.cs")
    docs = read("SHAEP_FORMAT.md")
    assert 'var id = $"shaep-{Guid.NewGuid():N}"' in codec
    assert "`Sha256` is optional integrity evidence" in docs
    assert "without becoming the same object" in docs
    assert "hash.Length != 64" in codec


def test_shaep_conversion_lifecycle_preserves_native_fallback_until_ready():
    codec = read("ShaepCodec.cs")
    model = read("ShaepManifest.cs")
    for token in (
        'public const string PendingConversion = "pending-conversion"',
        'public const string Converting = "converting"',
        'public const string Ready = "ready"',
        'public const string Failed = "failed"',
    ):
        assert token in model
    assert "CreateProvisional" in codec
    assert "MarkConverting" in codec
    assert "CompleteConversion" in codec
    assert "FailConversion" in codec
    assert "Canonical = manifest.Source" in codec
    assert "Canonical = canonical" in codec
    assert "ShaepFormat.ArchiveMediaType" in codec


def test_shaep_v1_manifests_upgrade_without_changing_identity():
    codec = read("ShaepCodec.cs")
    user_assets = read("WorldSession.UserAssets.cs")
    docs = read("SHAEP_FORMAT.md")
    assert "UpgradeLegacy" in codec
    assert "Version = ShaepFormat.CurrentVersion" in codec
    assert "ArchiveObjectKey(manifest.ShaepId)" in codec
    assert "LoadShaepManifestAsync" in user_assets
    assert "LegacyManifestObjectKey" in user_assets
    assert "ShaepCodec.UpgradeLegacy(existing)" in user_assets
    assert "without changing `ShaepId`" in docs


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


def test_user_asset_catalog_tracks_archive_conversion_state():
    user_assets = read("WorldSession.UserAssets.cs")
    assert "EnsureShaepEntriesAsync" in user_assets
    assert "SaveShaepManifestAsync" in user_assets
    assert "ArchiveMediaType" in user_assets
    assert "ArchiveObjectKey" in user_assets
    assert "ConversionStatus" in user_assets
    assert "ShaepFormat.PendingConversion" in user_assets
    assert "NeedsShaepUpgrade" in user_assets


def test_world_placements_preserve_shaep_identity():
    models = read("WorldSession.Models.cs")
    interactions = read("Components/WorldBuilderStudio.Interactions.cs")
    assert len(re.findall(r'string\s+ShaepId\s*=\s*""', models)) >= 2
    assert "ShaepId = Session.ResolveShaepId(tile)" in interactions
    assert "ResolveShaepId(AtlasTile tile)" in read("WorldSession.UserAssets.cs")


def test_runtime_derivatives_are_disposable_and_archive_transition_keeps_identity():
    docs = read("SHAEP_FORMAT.md")
    assert "Runtime thumbnails, resized previews, decoded GPU textures, viewer composites" in docs
    assert "storage-class transition does not change SHAEP identity" in docs
