using System.Text.Json;

namespace RistWorld;

public static class ShaepCodec
{
    static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        PropertyNameCaseInsensitive = true
    };

    public static string ManifestObjectKey(string shaepId)
    {
        var safe = RequireSafeIdentity(shaepId);
        return $"uploads/shaep/{safe}/{ShaepFormat.ManifestFileName}";
    }

    public static string LegacyManifestObjectKey(string shaepId)
    {
        var safe = RequireSafeIdentity(shaepId);
        return $"uploads/shaep/{safe}/manifest{ShaepFormat.FileExtension}";
    }

    public static string ArchiveObjectKey(string shaepId)
    {
        var safe = RequireSafeIdentity(shaepId);
        return $"uploads/shaep/{safe}/archive{ShaepFormat.FileExtension}";
    }

    public static string ArchiveIndexObjectKey(string shaepId)
    {
        var safe = RequireSafeIdentity(shaepId);
        return $"uploads/shaep/{safe}/archive.index.json";
    }

    public static string Serialize(ShaepManifest manifest)
    {
        Validate(manifest);
        return JsonSerializer.Serialize(manifest, JsonOptions);
    }

    public static ShaepManifest Deserialize(string json)
    {
        var manifest = JsonSerializer.Deserialize<ShaepManifest>(json, JsonOptions)
            ?? throw new InvalidDataException("SHAEP manifest was empty.");
        Validate(manifest);
        return manifest;
    }

    /// <summary>
    /// Creates a v2 SHAEP identity and conversion plan. The native object is
    /// immediately usable as Canonical fallback while the .shaep hot archive
    /// is materialized. Completing conversion swaps Canonical to the archive
    /// without changing ShaepId or Source.
    /// </summary>
    public static ShaepManifest CreateProvisional(
        string name,
        string objectKey,
        string mediaType,
        string sha256 = "",
        long bytes = 0,
        int pixelWidth = 0,
        int pixelHeight = 0,
        string originalFileName = "",
        string provenanceOrigin = "HUMAN",
        string author = "")
    {
        var now = DateTimeOffset.UtcNow;
        var id = $"shaep-{Guid.NewGuid():N}";
        var normalizedMediaType = string.IsNullOrWhiteSpace(mediaType) ? "application/octet-stream" : mediaType.Trim();
        var source = new ShaepPayload(
            objectKey,
            normalizedMediaType,
            NormalizeHash(sha256),
            Math.Max(0, bytes),
            Math.Max(0, pixelWidth),
            Math.Max(0, pixelHeight),
            originalFileName ?? "");
        var archive = new ShaepHotArchiveContract(
            ArchiveObjectKey(id),
            SourceMediaType: normalizedMediaType,
            IndexObjectKey: ArchiveIndexObjectKey(id));

        return new ShaepManifest(
            ShaepFormat.Name,
            ShaepFormat.CurrentVersion,
            id,
            string.IsNullOrWhiteSpace(name) ? id : name.Trim(),
            source,
            source,
            new ShaepSpatialContract(),
            null,
            new ShaepProvenance(
                string.IsNullOrWhiteSpace(provenanceOrigin) ? "UNKNOWN" : provenanceOrigin.Trim().ToUpperInvariant(),
                author?.Trim() ?? ""),
            ShaepFormat.HotStorageState,
            ShaepFormat.PendingConversion,
            now,
            now,
            archive);
    }

    /// <summary>
    /// Converts the v1 manifest model to the v2 conversion lifecycle without
    /// touching the original media bytes. The native canonical remains the
    /// runtime fallback until a converter produces archive.shaep.
    /// </summary>
    public static ShaepManifest UpgradeLegacy(ShaepManifest manifest)
    {
        Validate(manifest);
        if (manifest.Version == ShaepFormat.CurrentVersion) return manifest;
        var archive = new ShaepHotArchiveContract(
            ArchiveObjectKey(manifest.ShaepId),
            SourceMediaType: manifest.Source.MediaType,
            IndexObjectKey: ArchiveIndexObjectKey(manifest.ShaepId));
        return manifest with
        {
            Version = ShaepFormat.CurrentVersion,
            Canonical = manifest.Source,
            Archive = archive,
            IngestStatus = ShaepFormat.PendingConversion,
            StorageState = ShaepFormat.HotStorageState,
            UpdatedAtUtc = DateTimeOffset.UtcNow
        };
    }

    public static ShaepManifest MarkConverting(ShaepManifest manifest)
    {
        manifest = UpgradeLegacy(manifest);
        var archive = manifest.Archive! with { ConversionStatus = ShaepFormat.Converting, Error = "" };
        var updated = manifest with
        {
            Archive = archive,
            IngestStatus = ShaepFormat.Converting,
            UpdatedAtUtc = DateTimeOffset.UtcNow
        };
        Validate(updated);
        return updated;
    }

    public static ShaepManifest CompleteConversion(
        ShaepManifest manifest,
        string sha256,
        long bytes,
        int chunkCount = 0,
        string indexObjectKey = "")
    {
        manifest = UpgradeLegacy(manifest);
        var hash = NormalizeHash(sha256);
        var archive = manifest.Archive! with
        {
            ConversionStatus = ShaepFormat.Ready,
            IndexObjectKey = string.IsNullOrWhiteSpace(indexObjectKey) ? ArchiveIndexObjectKey(manifest.ShaepId) : indexObjectKey.Trim(),
            ChunkCount = Math.Max(0, chunkCount),
            Bytes = Math.Max(0, bytes),
            Sha256 = hash,
            ConvertedAtUtc = DateTimeOffset.UtcNow,
            Error = ""
        };
        var canonical = new ShaepPayload(
            archive.ObjectKey,
            ShaepFormat.ArchiveMediaType,
            hash,
            archive.Bytes,
            manifest.Source.PixelWidth,
            manifest.Source.PixelHeight,
            Path.GetFileName(archive.ObjectKey));
        var updated = manifest with
        {
            Canonical = canonical,
            Archive = archive,
            IngestStatus = ShaepFormat.Ready,
            StorageState = ShaepFormat.HotStorageState,
            UpdatedAtUtc = DateTimeOffset.UtcNow
        };
        Validate(updated);
        return updated;
    }

    public static ShaepManifest FailConversion(ShaepManifest manifest, string error)
    {
        manifest = UpgradeLegacy(manifest);
        var archive = manifest.Archive! with
        {
            ConversionStatus = ShaepFormat.Failed,
            Error = (error ?? "").Trim()
        };
        var updated = manifest with
        {
            Canonical = manifest.Source,
            Archive = archive,
            IngestStatus = ShaepFormat.Failed,
            UpdatedAtUtc = DateTimeOffset.UtcNow
        };
        Validate(updated);
        return updated;
    }

    public static void Validate(ShaepManifest manifest)
    {
        ArgumentNullException.ThrowIfNull(manifest);
        if (!string.Equals(manifest.Format, ShaepFormat.Name, StringComparison.Ordinal))
            throw new InvalidDataException($"Unsupported SHAEP format '{manifest.Format}'.");
        if (manifest.Version is not (ShaepFormat.LegacyVersion or ShaepFormat.CurrentVersion))
            throw new InvalidDataException($"Unsupported SHAEP version {manifest.Version}.");
        if (string.IsNullOrWhiteSpace(manifest.ShaepId)) throw new InvalidDataException("SHAEP identity is required.");
        if (string.IsNullOrWhiteSpace(manifest.Name)) throw new InvalidDataException("SHAEP name is required.");
        ValidatePayload(manifest.Source, "source");
        ValidatePayload(manifest.Canonical, "canonical");
        if (manifest.Spatial.WidthCells < 1 || manifest.Spatial.HeightCells < 1)
            throw new InvalidDataException("SHAEP footprint must occupy at least one grid cell.");
        if (manifest.Temporal is { FrameCount: < 1 })
            throw new InvalidDataException("SHAEP temporal frame count must be at least one.");
        if (manifest.Temporal is { FramesPerSecond: < 0 } || manifest.Temporal is { DurationSeconds: < 0 })
            throw new InvalidDataException("SHAEP temporal values cannot be negative.");
        if (string.IsNullOrWhiteSpace(manifest.StorageState)) throw new InvalidDataException("SHAEP storage state is required.");
        if (string.IsNullOrWhiteSpace(manifest.IngestStatus)) throw new InvalidDataException("SHAEP ingest status is required.");

        if (manifest.Version == ShaepFormat.CurrentVersion)
            ValidateArchive(manifest);
    }

    public static string MediaTypeForObjectKey(string? objectKey)
    {
        return Path.GetExtension(objectKey ?? "").ToLowerInvariant() switch
        {
            ".shaep" => ShaepFormat.ArchiveMediaType,
            ".png" => "image/png",
            ".jpg" or ".jpeg" => "image/jpeg",
            ".webp" => "image/webp",
            ".gif" => "image/gif",
            ".tif" or ".tiff" => "image/tiff",
            ".svg" => "image/svg+xml",
            ".mp4" => "video/mp4",
            ".mov" => "video/quicktime",
            ".mkv" => "video/x-matroska",
            ".webm" => "video/webm",
            ".mp3" => "audio/mpeg",
            ".wav" => "audio/wav",
            ".flac" => "audio/flac",
            _ => "application/octet-stream"
        };
    }

    static void ValidateArchive(ShaepManifest manifest)
    {
        var archive = manifest.Archive ?? throw new InvalidDataException("SHAEP v2 hot archive contract is required.");
        if (string.IsNullOrWhiteSpace(archive.ObjectKey) || !archive.ObjectKey.EndsWith(ShaepFormat.FileExtension, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("SHAEP v2 archive object must use the .shaep extension.");
        if (!string.Equals(archive.MediaType, ShaepFormat.ArchiveMediaType, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("SHAEP v2 archive media type is invalid.");
        if (string.IsNullOrWhiteSpace(archive.Profile) || string.IsNullOrWhiteSpace(archive.Layout))
            throw new InvalidDataException("SHAEP v2 archive profile and layout are required.");
        if (archive.ChunkCount < 0 || archive.Bytes < 0)
            throw new InvalidDataException("SHAEP v2 archive counts cannot be negative.");
        _ = NormalizeHash(archive.Sha256);
        var status = archive.ConversionStatus;
        if (status is not (ShaepFormat.PendingConversion or ShaepFormat.Converting or ShaepFormat.Ready or ShaepFormat.Failed))
            throw new InvalidDataException($"Unsupported SHAEP conversion status '{status}'.");
        if (!string.Equals(manifest.IngestStatus, status, StringComparison.Ordinal))
            throw new InvalidDataException("SHAEP ingest and archive conversion status must agree.");
        if (status == ShaepFormat.Ready)
        {
            if (!string.Equals(manifest.Canonical.ObjectKey, archive.ObjectKey, StringComparison.Ordinal))
                throw new InvalidDataException("Ready SHAEP canonical payload must be the hot archive.");
            if (!string.Equals(manifest.Canonical.MediaType, ShaepFormat.ArchiveMediaType, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Ready SHAEP canonical media type must be the SHAEP archive media type.");
        }
    }

    static void ValidatePayload(ShaepPayload payload, string label)
    {
        if (payload is null) throw new InvalidDataException($"SHAEP {label} payload is required.");
        if (string.IsNullOrWhiteSpace(payload.ObjectKey)) throw new InvalidDataException($"SHAEP {label} object key is required.");
        if (string.IsNullOrWhiteSpace(payload.MediaType)) throw new InvalidDataException($"SHAEP {label} media type is required.");
        if (payload.Bytes < 0 || payload.PixelWidth < 0 || payload.PixelHeight < 0)
            throw new InvalidDataException($"SHAEP {label} dimensions cannot be negative.");
        _ = NormalizeHash(payload.Sha256);
    }

    static string NormalizeHash(string? value)
    {
        var hash = (value ?? "").Trim().ToLowerInvariant();
        if (hash.Length == 0) return "";
        if (hash.Length != 64 || hash.Any(c => !Uri.IsHexDigit(c)))
            throw new InvalidDataException("SHAEP SHA-256 must be empty/pending or exactly 64 hexadecimal characters.");
        return hash;
    }

    static string RequireSafeIdentity(string value)
    {
        var safe = SafeIdentity(value);
        if (string.IsNullOrWhiteSpace(safe)) throw new ArgumentException("SHAEP identity is required.", nameof(value));
        return safe;
    }

    static string SafeIdentity(string value)
    {
        var chars = value.Trim().ToLowerInvariant().Select(c =>
            c is >= 'a' and <= 'z' or >= '0' and <= '9' or '-' ? c : '-').ToArray();
        var safe = new string(chars);
        while (safe.Contains("--", StringComparison.Ordinal)) safe = safe.Replace("--", "-", StringComparison.Ordinal);
        return safe.Trim('-');
    }
}
