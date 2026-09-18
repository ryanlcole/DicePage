using System.Text.Json;

namespace RistWorld;

public sealed partial class WorldSession
{
    public const string UserAssetIndexKey = "uploads/index.json";
    public List<AtlasTile> UserAssetTiles { get; } = [];
    readonly Dictionary<string, string> _shaepByAssetKey = new(StringComparer.Ordinal);

    public void ReplaceUserAssetTiles(IEnumerable<AtlasTile> tiles)
    {
        UserAssetTiles.Clear();
        UserAssetTiles.AddRange(tiles);
        Notify();
    }

    public async Task<UserAssetCatalog> LoadUserAssetCatalogAsync()
    {
        if (!IsLoggedIn) return new UserAssetCatalog([], DateTimeOffset.UtcNow);
        var catalog = await auth.DownloadJsonAsync<UserAssetCatalog>(UserAssetIndexKey)
            ?? new UserAssetCatalog([], DateTimeOffset.UtcNow);

        var sourceItems = (catalog.Items ?? []).ToList();
        if (sourceItems.Count == 0)
        {
            _shaepByAssetKey.Clear();
            return catalog;
        }

        // Pre-SHAEP uploads and v1 manifest-only SHAEP assets are migrated
        // lazily. Native bytes stay where they are and remain the immediate
        // viewer fallback. v2 adds a real archive.shaep conversion target;
        // ShaepId and placement identity remain unchanged.
        if (sourceItems.Any(NeedsShaepUpgrade))
        {
            var migrated = await EnsureShaepEntriesAsync(sourceItems);
            var normalized = new UserAssetCatalog(migrated, DateTimeOffset.UtcNow);
            await WriteUserAssetCatalogAsync(normalized);
            IndexShaepEntries(migrated);
            return normalized;
        }

        IndexShaepEntries(sourceItems);
        return catalog;
    }

    public async Task SaveUserAssetCatalogAsync(UserAssetCatalog catalog)
    {
        if (!IsLoggedIn) return;
        var deduplicated = (catalog.Items ?? [])
            .Where(x => !string.IsNullOrWhiteSpace(x.Key))
            .GroupBy(x => x.Key, StringComparer.Ordinal)
            .Select(g => g.Last())
            .OrderByDescending(x => x.UploadedAtUtc)
            .ToList();

        var items = await EnsureShaepEntriesAsync(deduplicated);
        var normalized = new UserAssetCatalog(items, DateTimeOffset.UtcNow);
        await WriteUserAssetCatalogAsync(normalized);
        IndexShaepEntries(items);
    }

    async Task WriteUserAssetCatalogAsync(UserAssetCatalog catalog)
    {
        await auth.UploadTextAsync(UserAssetIndexKey, JsonSerializer.Serialize(catalog, MapWriteOptions), "application/json");
    }

    async Task<List<UserAssetCatalogEntry>> EnsureShaepEntriesAsync(IEnumerable<UserAssetCatalogEntry> entries)
    {
        var result = new List<UserAssetCatalogEntry>();
        foreach (var entry in entries)
        {
            if (!string.IsNullOrWhiteSpace(entry.ShaepId))
            {
                var normalized = NormalizeExistingShaepEntry(entry);
                if (NeedsShaepUpgrade(normalized))
                {
                    var existing = await LoadShaepManifestAsync(normalized.ShaepId);
                    if (existing is not null)
                    {
                        var current = existing.Version == ShaepFormat.LegacyVersion
                            ? ShaepCodec.UpgradeLegacy(existing)
                            : existing;
                        if (current.Version == ShaepFormat.CurrentVersion)
                        {
                            if (existing.Version != current.Version)
                                await SaveShaepManifestAsync(current);
                            normalized = ApplyShaepManifest(normalized, current);
                        }
                    }
                }
                result.Add(normalized);
                continue;
            }

            var manifest = ShaepCodec.CreateProvisional(
                entry.Name,
                entry.Key,
                ShaepCodec.MediaTypeForObjectKey(entry.Key),
                originalFileName: Path.GetFileName(entry.Key),
                provenanceOrigin: "HUMAN");
            await SaveShaepManifestAsync(manifest);
            result.Add(ApplyShaepManifest(entry, manifest));
        }
        return result;
    }

    static bool NeedsShaepUpgrade(UserAssetCatalogEntry entry)
    {
        if (string.IsNullOrWhiteSpace(entry.ShaepId)) return true;
        if (string.IsNullOrWhiteSpace(entry.ArchiveObjectKey)) return true;
        if (string.IsNullOrWhiteSpace(entry.ConversionStatus)) return true;
        if (entry.ShaepManifestKey.EndsWith($"manifest{ShaepFormat.FileExtension}", StringComparison.OrdinalIgnoreCase)) return true;
        return string.Equals(entry.IngestStatus, ShaepFormat.PendingNormalization, StringComparison.OrdinalIgnoreCase);
    }

    static UserAssetCatalogEntry NormalizeExistingShaepEntry(UserAssetCatalogEntry entry)
    {
        var mediaType = string.IsNullOrWhiteSpace(entry.CanonicalMediaType)
            ? ShaepCodec.MediaTypeForObjectKey(string.IsNullOrWhiteSpace(entry.CanonicalObjectKey) ? entry.Key : entry.CanonicalObjectKey)
            : entry.CanonicalMediaType;
        var canonicalKey = string.IsNullOrWhiteSpace(entry.CanonicalObjectKey) ? entry.Key : entry.CanonicalObjectKey;
        var legacy = string.Equals(entry.IngestStatus, ShaepFormat.PendingNormalization, StringComparison.OrdinalIgnoreCase)
            || entry.ShaepManifestKey.EndsWith($"manifest{ShaepFormat.FileExtension}", StringComparison.OrdinalIgnoreCase);
        var manifestKey = string.IsNullOrWhiteSpace(entry.ShaepManifestKey)
            ? (legacy ? ShaepCodec.LegacyManifestObjectKey(entry.ShaepId) : ShaepCodec.ManifestObjectKey(entry.ShaepId))
            : entry.ShaepManifestKey;
        return entry with
        {
            ShaepManifestKey = manifestKey,
            CanonicalMediaType = mediaType,
            CanonicalObjectKey = canonicalKey,
            ArchiveMediaType = string.IsNullOrWhiteSpace(entry.ArchiveMediaType) ? ShaepFormat.ArchiveMediaType : entry.ArchiveMediaType,
            ArchiveObjectKey = string.IsNullOrWhiteSpace(entry.ArchiveObjectKey) ? ShaepCodec.ArchiveObjectKey(entry.ShaepId) : entry.ArchiveObjectKey,
            ConversionStatus = string.IsNullOrWhiteSpace(entry.ConversionStatus)
                ? (legacy ? ShaepFormat.PendingConversion : entry.IngestStatus)
                : entry.ConversionStatus,
            StorageState = string.IsNullOrWhiteSpace(entry.StorageState) ? ShaepFormat.HotStorageState : entry.StorageState,
            IngestStatus = string.IsNullOrWhiteSpace(entry.IngestStatus)
                ? ShaepFormat.PendingConversion
                : entry.IngestStatus
        };
    }

    static UserAssetCatalogEntry ApplyShaepManifest(UserAssetCatalogEntry entry, ShaepManifest manifest)
    {
        return entry with
        {
            ShaepId = manifest.ShaepId,
            ShaepManifestKey = manifest.Version == ShaepFormat.LegacyVersion
                ? ShaepCodec.LegacyManifestObjectKey(manifest.ShaepId)
                : ShaepCodec.ManifestObjectKey(manifest.ShaepId),
            CanonicalMediaType = manifest.Canonical.MediaType,
            CanonicalObjectKey = manifest.Canonical.ObjectKey,
            ArchiveMediaType = manifest.Archive?.MediaType ?? "",
            ArchiveObjectKey = manifest.Archive?.ObjectKey ?? "",
            ConversionStatus = manifest.Archive?.ConversionStatus ?? manifest.IngestStatus,
            Sha256 = manifest.Canonical.Sha256,
            IngestStatus = manifest.IngestStatus,
            StorageState = manifest.StorageState
        };
    }

    void IndexShaepEntries(IEnumerable<UserAssetCatalogEntry> entries)
    {
        _shaepByAssetKey.Clear();
        foreach (var entry in entries)
        {
            if (!string.IsNullOrWhiteSpace(entry.Key) && !string.IsNullOrWhiteSpace(entry.ShaepId))
                _shaepByAssetKey[entry.Key] = entry.ShaepId;
        }
    }

    public string ResolveShaepId(AtlasTile tile)
    {
        if (!string.IsNullOrWhiteSpace(tile.ShaepId)) return tile.ShaepId;
        const string privatePrefix = "private:";
        if (tile.Id.StartsWith(privatePrefix, StringComparison.Ordinal))
        {
            var key = tile.Id[privatePrefix.Length..];
            if (_shaepByAssetKey.TryGetValue(key, out var shaepId)) return shaepId;
        }
        return "";
    }

    public async Task SaveShaepManifestAsync(ShaepManifest manifest)
    {
        if (!IsLoggedIn) return;
        ShaepCodec.Validate(manifest);
        var key = manifest.Version == ShaepFormat.LegacyVersion
            ? ShaepCodec.LegacyManifestObjectKey(manifest.ShaepId)
            : ShaepCodec.ManifestObjectKey(manifest.ShaepId);
        // Manifest JSON is metadata beside archive.shaep. The archive itself is
        // binary hot media and is written by the conversion engine/service.
        await auth.UploadTextAsync(key, ShaepCodec.Serialize(manifest), "application/json");
    }

    public async Task<ShaepManifest?> LoadShaepManifestAsync(string shaepId)
    {
        if (!IsLoggedIn || string.IsNullOrWhiteSpace(shaepId)) return null;
        var manifest = await auth.DownloadJsonAsync<ShaepManifest>(ShaepCodec.ManifestObjectKey(shaepId));
        manifest ??= await auth.DownloadJsonAsync<ShaepManifest>(ShaepCodec.LegacyManifestObjectKey(shaepId));
        if (manifest is null) return null;
        ShaepCodec.Validate(manifest);
        return manifest;
    }

    public async Task RenameUserAssetFolderAsync(string category, string oldFolder, string newFolder)
    {
        category = NormalizeAssetCategory(category);
        oldFolder = NormalizeAssetFolder(oldFolder);
        newFolder = NormalizeAssetFolder(newFolder);
        var catalog = await LoadUserAssetCatalogAsync();
        var changed = false;
        var items = catalog.Items.Select(item =>
        {
            if (!string.Equals(item.Category, category, StringComparison.OrdinalIgnoreCase) ||
                !string.Equals(item.Folder, oldFolder, StringComparison.OrdinalIgnoreCase)) return item;
            changed = true;
            return item with { Folder = newFolder };
        }).ToList();
        if (changed) await SaveUserAssetCatalogAsync(new UserAssetCatalog(items, DateTimeOffset.UtcNow));
    }

    public static string NormalizeAssetCategory(string? category)
    {
        var value = (category ?? "").Trim();
        return value switch
        {
            "Tiles" => "Tiles",
            "Tokens & Chits" or "Tokens" => "Tokens & Chits",
            "Miniatures" or "Minis" => "Miniatures",
            "Scenery & Terrain" or "Scenery" => "Scenery & Terrain",
            "Pawns & Meeples" or "Pawns" => "Pawns & Meeples",
            "Rolling Stock" or "Rolling Stock & Locomotives" => "Rolling Stock",
            "Bits" => "Bits",
            "Sprites" => "Sprites",
            "Images" or "Image" => "Images",
            _ => "Tiles"
        };
    }

    public static string NormalizeAssetFolder(string? folder)
    {
        var value = (folder ?? "").Trim();
        if (value.Length == 0) value = "Custom";
        if (value.Length > 48) value = value[..48].Trim();
        return value;
    }

    public static string AssetPathSegment(string value)
    {
        var chars = value.ToLowerInvariant().Select(c => c is >= 'a' and <= 'z' or >= '0' and <= '9' ? c : '-').ToArray();
        var segment = new string(chars);
        while (segment.Contains("--", StringComparison.Ordinal)) segment = segment.Replace("--", "-", StringComparison.Ordinal);
        segment = segment.Trim('-');
        return string.IsNullOrWhiteSpace(segment) ? "custom" : segment;
    }
}

public sealed record UserAssetCatalog(List<UserAssetCatalogEntry> Items, DateTimeOffset UpdatedAtUtc);
public sealed record UserAssetCatalogEntry(
    string Key,
    string Name,
    string Category,
    string Folder,
    DateTimeOffset UploadedAtUtc,
    string ShaepId = "",
    string ShaepManifestKey = "",
    string CanonicalMediaType = "",
    string CanonicalObjectKey = "",
    string Sha256 = "",
    string IngestStatus = "",
    string StorageState = "hot",
    string ArchiveMediaType = "",
    string ArchiveObjectKey = "",
    string ConversionStatus = "",
    string AssetKind = "image",
    int SpriteColumns = 1,
    int SpriteRows = 1,
    int FrameCount = 1,
    double FramesPerSecond = 0,
    int SourceWidth = 0,
    int SourceHeight = 0,
    int CropX = 0,
    int CropY = 0,
    int CropWidth = 0,
    int CropHeight = 0,
    bool WhiteTransparent = false);
