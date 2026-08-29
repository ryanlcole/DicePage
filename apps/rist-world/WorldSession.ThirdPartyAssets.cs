using System.Net.Http.Json;
using System.Text.Json.Serialization;

namespace RistWorld;

public sealed partial class WorldSession
{
    public sealed record ThirdPartyPack(
        string Id,
        string Category,
        string Folder,
        string Layer,
        string RemotePath,
        string OriginUrl,
        string LicenseUrl,
        string SupportUrl,
        string Creator = "Kenney");

    private sealed record GitHubAssetEntry(
        [property: JsonPropertyName("name")] string Name,
        [property: JsonPropertyName("path")] string Path,
        [property: JsonPropertyName("type")] string Type,
        [property: JsonPropertyName("download_url")] string? DownloadUrl);

    public IReadOnlyList<ThirdPartyPack> ThirdPartyStarterPacks { get; } =
    [
        new("kenney-toon-minis", "Miniatures (Minis)", "Kenney · Character Minis", "LOCAL", "kenney_tooncharacters1/PNG", "https://kenney.nl/assets/toon-characters", "https://creativecommons.org/publicdomain/zero/1.0/", "https://kenney.nl/support"),
        new("kenney-isometric-vehicles", "Rolling Stock & Locomotives", "Kenney · Isometric Vehicles", "REGION", "isometricvehicles/PNG", "https://kenney.nl/assets/isometric-tiles-vehicles", "https://creativecommons.org/publicdomain/zero/1.0/", "https://kenney.nl/support"),
        new("kenney-board-pieces", "Pawns & Meeples", "Kenney · Black Board Pieces", "ENCOUNTER", "boardgamepack/PNG/Pieces (Black)", "https://kenney.nl/assets/boardgame-pack", "https://creativecommons.org/publicdomain/zero/1.0/", "https://kenney.nl/support"),
        new("kenney-runes-grey", "Tokens & Chits", "Kenney · Grey Runes", "ENCOUNTER", "kenney_runepack/PNG/Grey", "https://kenney.nl/assets/rune-pack", "https://creativecommons.org/publicdomain/zero/1.0/", "https://kenney.nl/support"),
        new("kenney-hex-tiles", "Tiles", "Kenney · Hexagon Tiles", "WORLD", "hexagontiles/Tiles", "https://kenney.nl/assets/hexagon-pack", "https://creativecommons.org/publicdomain/zero/1.0/", "https://kenney.nl/support"),
        new("kenney-isometric-landscape", "Scenery & Terrain", "Kenney · Isometric Landscape", "LOCAL", "isometriclandscape/PNG", "https://kenney.nl/assets/isometric-tiles-landscape", "https://creativecommons.org/publicdomain/zero/1.0/", "https://kenney.nl/support"),
        new("kenney-generic-items", "Bits", "Kenney · Generic Items", "OBJECT", "generic-items-160-assets/PNG", "https://kenney.nl/assets/generic-items", "https://creativecommons.org/publicdomain/zero/1.0/", "https://kenney.nl/support")
    ];

    public async Task LoadThirdPartyStarterAssetsAsync()
    {
        var existingIds = AtlasTiles.Select(tile => tile.Id).ToHashSet(StringComparer.Ordinal);
        var addedAny = false;
        foreach (var pack in ThirdPartyStarterPacks)
        {
            try
            {
                var url = "https://api.github.com/repos/ETdoFresh/kenney.nl/contents/" + Uri.EscapeDataString(pack.RemotePath).Replace("%2F", "/") + "?ref=master";
                var rows = await http.GetFromJsonAsync<List<GitHubAssetEntry>>(url);
                if (rows is null) continue;
                foreach (var row in rows)
                {
                    if (row.Type != "file" || !IsSupportedImage(row.Name) || string.IsNullOrWhiteSpace(row.DownloadUrl)) continue;
                    var id = $"thirdparty:{pack.Id}:{Slug(row.Name)}";
                    if (!existingIds.Add(id)) continue;
                    var cleanName = Path.GetFileNameWithoutExtension(row.Name).Replace('_', ' ').Replace('-', ' ').Trim();
                    AtlasTiles.Add(new AtlasTile(id, cleanName, row.DownloadUrl!, pack.Layer, pack.Category, pack.Folder, $"{pack.Creator} • {pack.Id}"));
                    addedAny = true;
                }
            }
            catch
            {
                // Third-party starter packs are additive. Never block the tabletop if a remote source is unavailable.
            }
        }
        if (addedAny) Notify();
    }

    public ThirdPartyPack? ThirdPartyPackFor(AtlasTile tile)
    {
        if (!tile.Id.StartsWith("thirdparty:", StringComparison.Ordinal)) return null;
        var parts = tile.Id.Split(':', 3);
        return parts.Length >= 2 ? ThirdPartyStarterPacks.FirstOrDefault(x => x.Id == parts[1]) : null;
    }

    private static bool IsSupportedImage(string name)
        => name.EndsWith(".png", StringComparison.OrdinalIgnoreCase)
        || name.EndsWith(".webp", StringComparison.OrdinalIgnoreCase)
        || name.EndsWith(".jpg", StringComparison.OrdinalIgnoreCase)
        || name.EndsWith(".jpeg", StringComparison.OrdinalIgnoreCase);

    private static string Slug(string value)
        => new(value.ToLowerInvariant().Select(c => char.IsLetterOrDigit(c) ? c : '-').ToArray());
}
