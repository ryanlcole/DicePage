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

        // Older uploads predate SHAEP. Migrate them lazily the first time their
        // catalog is read: no media bytes are duplicated, and the current hot
        // object becomes both source and provisional canonical preservation
        // payload until a normalizer supplies a replacement canonical object.
        if (sourceItems.Any(x => string.IsNullOrWhiteSpace(x.ShaepId)))
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
                result.Add(entry with
                {
                    ShaepManifestKey = string.IsNullOrWhiteSpace(entry.ShaepManifestKey)
                        ? ShaepCodec.ManifestObjectKey(entry.ShaepId)
                        : entry.ShaepManifestKey,
                    CanonicalMediaType = string.IsNullOrWhiteSpace(entry.CanonicalMediaType)
                        ? ShaepCodec.MediaTypeForObjectKey(entry.Key)
                        : entry.CanonicalMediaType,
                    CanonicalObjectKey = string.IsNullOrWhiteSpace(entry.CanonicalObjectKey)
                        ? entry.Key
                        : entry.CanonicalObjectKey,
                    StorageState = string.IsNullOrWhiteSpace(entry.StorageState)
                        ? ShaepFormat.HotStorageState
                        : entry.StorageState,
                    IngestStatus = string.IsNullOrWhiteSpace(entry.IngestStatus)
                        ? ShaepFormat.PendingNormalization
                        : entry.IngestStatus
                });
                continue;
            }

            var manifest = ShaepCodec.CreateProvisional(
                entry.Name,
                entry.Key,
                ShaepCodec.MediaTypeForObjectKey(entry.Key),
                originalFileName: Path.GetFileName(entry.Key),
                provenanceOrigin: "HUMAN");
            await SaveShaepManifestAsync(manifest);
            result.Add(entry with
            {
                ShaepId = manifest.ShaepId,
                ShaepManifestKey = ShaepCodec.ManifestObjectKey(manifest.ShaepId),
                CanonicalMediaType = manifest.Canonical.MediaType,
                CanonicalObjectKey = manifest.Canonical.ObjectKey,
                Sha256 = manifest.Canonical.Sha256,
                IngestStatus = manifest.IngestStatus,
                StorageState = manifest.StorageState
            });
        }
        return result;
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
        await auth.UploadTextAsync(
            ShaepCodec.ManifestObjectKey(manifest.ShaepId),
            ShaepCodec.Serialize(manifest),
            ShaepFormat.ManifestMediaType);
    }

    public async Task<ShaepManifest?> LoadShaepManifestAsync(string shaepId)
    {
        if (!IsLoggedIn || string.IsNullOrWhiteSpace(shaepId)) return null;
        var manifest = await auth.DownloadJsonAsync<ShaepManifest>(ShaepCodec.ManifestObjectKey(shaepId));
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
    string StorageState = "hot");
