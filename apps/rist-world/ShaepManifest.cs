namespace RistWorld;

/// <summary>
/// SHAEP is Shaelvien's persistent spatial-asset contract. It is deliberately
/// not a media codec: payload bytes remain in established media formats while
/// this manifest supplies identity, integrity, provenance, time and space.
/// </summary>
public static class ShaepFormat
{
    public const string Name = "SHAEP";
    public const int CurrentVersion = 1;
    public const string FileExtension = ".shaep";
    public const string ManifestMediaType = "application/vnd.shaelvien.shaep+json";
    public const string HotStorageState = "hot";
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
    DateTimeOffset UpdatedAtUtc);

/// <summary>
/// A payload is an object reference, never embedded media. Source and Canonical
/// may point to the same hot object until a preservation normalizer replaces
/// the canonical pointer. SHA-256 is integrity evidence, not object identity.
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
