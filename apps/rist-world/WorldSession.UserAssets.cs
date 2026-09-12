using System.Text.Json;

namespace RistWorld;

public sealed partial class WorldSession
{
    public const string UserAssetIndexKey = "uploads/index.json";
    public List<AtlasTile> UserAssetTiles { get; } = [];

    public void ReplaceUserAssetTiles(IEnumerable<AtlasTile> tiles)
    {
        UserAssetTiles.Clear();
        UserAssetTiles.AddRange(tiles);
        Notify();
    }

    public async Task<UserAssetCatalog> LoadUserAssetCatalogAsync()
    {
        if (!IsLoggedIn) return new UserAssetCatalog([], DateTimeOffset.UtcNow);
        return await auth.DownloadJsonAsync<UserAssetCatalog>(UserAssetIndexKey)
            ?? new UserAssetCatalog([], DateTimeOffset.UtcNow);
    }

    public async Task SaveUserAssetCatalogAsync(UserAssetCatalog catalog)
    {
        if (!IsLoggedIn) return;
        var normalized = new UserAssetCatalog(
            (catalog.Items ?? [])
                .Where(x => !string.IsNullOrWhiteSpace(x.Key))
                .GroupBy(x => x.Key, StringComparer.Ordinal)
                .Select(g => g.Last())
                .OrderByDescending(x => x.UploadedAtUtc)
                .ToList(),
            DateTimeOffset.UtcNow);
        await auth.UploadTextAsync(UserAssetIndexKey, JsonSerializer.Serialize(normalized, MapWriteOptions), "application/json");
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
    DateTimeOffset UploadedAtUtc);
