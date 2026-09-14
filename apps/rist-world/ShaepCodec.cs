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
        var safe = SafeIdentity(shaepId);
        if (string.IsNullOrWhiteSpace(safe)) throw new ArgumentException("SHAEP identity is required.", nameof(shaepId));
        return $"uploads/shaep/{safe}/manifest{ShaepFormat.FileExtension}";
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
        var payload = new ShaepPayload(
            objectKey,
            string.IsNullOrWhiteSpace(mediaType) ? "application/octet-stream" : mediaType.Trim(),
            NormalizeHash(sha256),
            Math.Max(0, bytes),
            Math.Max(0, pixelWidth),
            Math.Max(0, pixelHeight),
            originalFileName ?? "");

        return new ShaepManifest(
            ShaepFormat.Name,
            ShaepFormat.CurrentVersion,
            id,
            string.IsNullOrWhiteSpace(name) ? id : name.Trim(),
            payload,
            payload,
            new ShaepSpatialContract(),
            null,
            new ShaepProvenance(
                string.IsNullOrWhiteSpace(provenanceOrigin) ? "UNKNOWN" : provenanceOrigin.Trim().ToUpperInvariant(),
                author?.Trim() ?? ""),
            ShaepFormat.HotStorageState,
            ShaepFormat.PendingNormalization,
            now,
            now);
    }

    public static void Validate(ShaepManifest manifest)
    {
        ArgumentNullException.ThrowIfNull(manifest);
        if (!string.Equals(manifest.Format, ShaepFormat.Name, StringComparison.Ordinal))
            throw new InvalidDataException($"Unsupported SHAEP format '{manifest.Format}'.");
        if (manifest.Version != ShaepFormat.CurrentVersion)
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
    }

    public static string MediaTypeForObjectKey(string? objectKey)
    {
        return Path.GetExtension(objectKey ?? "").ToLowerInvariant() switch
        {
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

    static string SafeIdentity(string value)
    {
        var chars = value.Trim().ToLowerInvariant().Select(c =>
            c is >= 'a' and <= 'z' or >= '0' and <= '9' or '-' ? c : '-').ToArray();
        var safe = new string(chars);
        while (safe.Contains("--", StringComparison.Ordinal)) safe = safe.Replace("--", "-", StringComparison.Ordinal);
        return safe.Trim('-');
    }
}
