namespace RistWorld;

/// <summary>
/// SHAEP is Shaelvien's hot audiovisual archive contract. Native uploads remain
/// preserved as source truth, while SHAEP conversion creates a hot, indexed
/// archive representation for immediate viewer/runtime access. ShaepId is the
/// persistent identity and does not change when source or archive bytes move.
/// </summary>
public static class ShaepFormat
{
    public const string Name = "SHAEP";
    public const int LegacyVersion = 1;
    public const int CurrentVersion = 2;
    public const string FileExtension = ".shaep";
    public const string ManifestFileName = "manifest.json";
    public const string ManifestMediaType = "application/vnd.shaelvien.shaep+json";
    public const string ArchiveMediaType = "application/vnd.shaelvien.shaep";
    public const string ArchiveProfile = "shaep-hot-archive-v1";
    public const string ArchiveLayout = "indexed-planes";
    public const string HotStorageState = "hot";
    public const string PendingConversion = "pending-conversion";
    public const string Converting = "converting";
    public const string Ready = "ready";
    public const string Failed = "failed";

    // v1 compatibility only. New v2 manifests use PendingConversion.
    public const string PendingNormalization = "pending-normalization";
}

public sealed record ShaepManifest(
    string Format,
    int Version,
    string ShaepId,
    string Name,
    ShaepPayload Source,
    ShaepPayload Canonical,
    ShaepSpatialContract Spatial,
    ShaepTemporalContract? Temporal,
    ShaepProvenance Provenance,
    string StorageState,
    string IngestStatus,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc,
    ShaepHotArchiveContract? Archive = null);

/// <summary>
/// A payload is an object reference, never implicit identity. Source is the
/// preserved native upload. Canonical is the best currently usable payload:
/// source while conversion is pending/failed, then the .shaep hot archive once
/// conversion succeeds. SHA-256 is integrity evidence, not object identity.
/// </summary>
public sealed record ShaepPayload(
    string ObjectKey,
    string MediaType,
    string Sha256 = "",
    long Bytes = 0,
    int PixelWidth = 0,
    int PixelHeight = 0,
    string OriginalFileName = "");

/// <summary>
/// v2 conversion target. The archive is intentionally described independently
/// from any specific encoder implementation. The profile requires an indexed,
/// hot/random-access plane layout capable of representing still image, video,
/// audio, or combined audiovisual source material without changing ShaepId.
/// </summary>
public sealed record ShaepHotArchiveContract(
    string ObjectKey,
    string MediaType = ShaepFormat.ArchiveMediaType,
    string Profile = ShaepFormat.ArchiveProfile,
    string Layout = ShaepFormat.ArchiveLayout,
    string ConversionStatus = ShaepFormat.PendingConversion,
    string SourceMediaType = "",
    string IndexObjectKey = "",
    int ChunkCount = 0,
    long Bytes = 0,
    string Sha256 = "",
    DateTimeOffset? ConvertedAtUtc = null,
    string Error = "");

/// <summary>
/// Spatial defaults carried by the asset itself. A world placement may bind or
/// override these values without changing ShaepId. ZTier and ZLayer are the
/// authored depth axes used by the RIST viewer-owned grid.
/// </summary>
public sealed record ShaepSpatialContract(
    double X = 0,
    double Y = 0,
    int CubeX = 0,
    int CubeY = 0,
    int CubeZ = 0,
    int PlaneIndex = 0,
    int ZTier = 0,
    int ZLayer = 0,
    int WidthCells = 1,
    int HeightCells = 1);

public sealed record ShaepTemporalContract(
    int FrameCount = 1,
    double FramesPerSecond = 0,
    double DurationSeconds = 0,
    bool Loop = true);

/// <summary>
/// Origin is persistent provenance. Authenticated direct user uploads begin as
/// HUMAN. Derived material must preserve ancestry rather than silently becoming
/// purely human-made.
/// </summary>
public sealed record ShaepProvenance(
    string Origin = "UNKNOWN",
    string Author = "",
    string SourceApplication = "",
    DateTimeOffset? SourceCreatedAtUtc = null,
    IReadOnlyDictionary<string, string>? Metadata = null);
