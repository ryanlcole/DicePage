using System.Net;
using System.Text;
using System.Text.Json;

namespace RistWorld;

public sealed partial class WorldSession
{
    const string MapCardFormat = "RISTMAPCARD";
    const int MapCardVersion = 2;
    readonly List<string> _activeMapCardQuickSlotTileIds = [];

    public string ActiveMapCardId => $"{WorldId}-truth-map-001";
    public string ActiveMapCardPrivateKey => $"{WorldStoragePrefix}/cards/{ActiveMapCardId}.json";
    public string ActiveMapCardPublishedKey => $"{WorldStoragePrefix}/published-cards/{ActiveMapCardId}.json";
    public string ActiveMapCardLocalKey => $"rist.mapcard.{ActiveMapCardId}";
    public IReadOnlyList<string> ActiveMapCardQuickSlotTileIds => _activeMapCardQuickSlotTileIds;
    public bool ActiveMapCardPublished { get; private set; }

    MapCardDocument BuildActiveMapCard(bool? published = null)
    {
        var isPublished = published ?? ActiveMapCardPublished;
        var tiles = PlacedTiles.ToList();
        var requiredAssets = tiles.Select(x => x.Id)
            .Concat(_activeMapCardQuickSlotTileIds)
            .Where(x => !string.IsNullOrWhiteSpace(x))
            .Distinct(StringComparer.Ordinal)
            .ToList();
        var card = new MapCardDocument
        {
            Format = MapCardFormat,
            Version = MapCardVersion,
            CardId = ActiveMapCardId,
            OwnerAccountId = WorldOwnerAccountId,
            WorldId = WorldId,
            MapName = WorldDisplayName,
            Cartographer = string.IsNullOrWhiteSpace(DiscordDisplayName) ? "GameMaster" : DiscordDisplayName,
            InGameCreationDate = "",
            Visibility = isPublished ? "published" : "private",
            Published = isPublished,
            UpdatedAtUtc = DateTimeOffset.UtcNow,
            Tiles = tiles,
            QuickSlotTileIds = _activeMapCardQuickSlotTileIds.ToList(),
            RequiredAssetIds = requiredAssets,
            PreviewSvg = BuildMapCardPreviewSvg(tiles)
        };
        card.ManifestHash = ComputeCardManifestHash(new
        {
            card.CardId, card.WorldId, card.MapName, card.Cartographer, card.Published,
            card.Tiles, card.QuickSlotTileIds, card.RequiredAssetIds, card.AssetPackIds
        });
        card.ArtDataMark = ComputeArtDataMark(card.CardId, RistCardType.World, card.ManifestHash);
        return card;
    }

    string BuildMapCardPreviewSvg(IReadOnlyList<TileItem> tiles)
    {
        const double size = 320;
        var sb = new StringBuilder();
        sb.Append("<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 320 320\">");
        sb.Append("<rect width=\"320\" height=\"320\" fill=\"#071015\"/>");
        foreach (var tile in tiles)
        {
            var footprint = Math.Clamp(1.0 / Math.Max(tile.PlacementZoom, 0.000001), 0.001, GridColumns);
            var x = Math.Clamp(tile.X, 0, 1) * size;
            var y = Math.Clamp(tile.Y, 0, 1) * size;
            var w = Math.Min(size - x, footprint / GridColumns * size);
            var h = Math.Min(size - y, footprint / GridRows * size);
            var href = WebUtility.HtmlEncode(tile.Image ?? "");
            if (!string.IsNullOrWhiteSpace(href))
                sb.Append($"<image href=\"{href}\" x=\"{x:0.##}\" y=\"{y:0.##}\" width=\"{w:0.##}\" height=\"{h:0.##}\" preserveAspectRatio=\"none\"/>");
        }
        sb.Append("</svg>");
        return sb.ToString();
    }

    public string ExportActiveMapCardJson() => JsonSerializer.Serialize(BuildActiveMapCard(), MapWriteOptions);

    public async Task SaveActiveMapCardAsync(IEnumerable<string>? quickSlotTileIds = null, bool? published = null)
    {
        if (quickSlotTileIds is not null)
        {
            _activeMapCardQuickSlotTileIds.Clear();
            _activeMapCardQuickSlotTileIds.AddRange(quickSlotTileIds.Where(x => !string.IsNullOrWhiteSpace(x)).Distinct(StringComparer.Ordinal).Take(12));
        }
        if (published.HasValue) ActiveMapCardPublished = published.Value;

        var card = BuildActiveMapCard();
        var json = JsonSerializer.Serialize(card, MapWriteOptions);
        await js.InvokeVoidAsync("localStorage.setItem", ActiveMapCardLocalKey, json);

        if (!IsLoggedIn) return;
        await EnsureWorldRelationshipAsync();
        await auth.UploadTextAsync(ActiveMapCardPrivateKey, json, "application/json");
        if (card.Published)
            await auth.UploadTextAsync(ActiveMapCardPublishedKey, json, "application/json");
    }

    public async Task PublishActiveMapCardAsync(IEnumerable<string>? quickSlotTileIds = null)
    {
        await SaveActiveMapCardAsync(quickSlotTileIds, true);
        var mapCard = BuildActiveMapCard(true);
        var payload = JsonSerializer.SerializeToElement(mapCard, MapWriteOptions);
        await SaveCardEnvelopeAsync(new RistCardEnvelope
        {
            CardId = mapCard.CardId,
            CardType = RistCardType.World,
            OwnerAccountId = mapCard.OwnerAccountId,
            WorldId = mapCard.WorldId,
            Name = mapCard.MapName,
            Visibility = "published",
            Published = true,
            ArtAssetId = mapCard.CardId + ":preview",
            References = mapCard.RequiredAssetIds.Select(id => new RistCardReference(id, "asset")).ToList(),
            AssetPackIds = mapCard.AssetPackIds.ToList(),
            Payload = payload
        });
    }

    public async Task<bool> ImportActiveMapCardJsonAsync(string json)
    {
        try
        {
            var card = JsonSerializer.Deserialize<MapCardDocument>(json, MapReadOptions);
            if (card is null || !string.Equals(card.Format, MapCardFormat, StringComparison.Ordinal) ||
                !string.Equals(card.WorldId, WorldId, StringComparison.Ordinal)) return false;
            ApplyMapCard(card);
            await SaveActiveMapCardAsync(card.QuickSlotTileIds, card.Published);
            return true;
        }
        catch { return false; }
    }

    void ApplyMapCard(MapCardDocument card)
    {
        PlacedTiles.Clear();
        PlacedTiles.AddRange(card.Tiles ?? []);
        _activeMapCardQuickSlotTileIds.Clear();
        _activeMapCardQuickSlotTileIds.AddRange((card.QuickSlotTileIds ?? []).Where(x => !string.IsNullOrWhiteSpace(x)).Distinct(StringComparer.Ordinal).Take(12));
        ActiveMapCardPublished = card.Published;
        Notify();
    }

    public async Task<bool> LoadActiveMapCardAsync()
    {
        MapCardDocument? card = null;
        if (IsLoggedIn)
        {
            try
            {
                await EnsureWorldRelationshipAsync();
                card = await auth.DownloadJsonAsync<MapCardDocument>(ActiveMapCardPrivateKey);
            }
            catch { }
        }

        if (card is null)
        {
            try
            {
                var local = await js.InvokeAsync<string?>("localStorage.getItem", ActiveMapCardLocalKey);
                if (!string.IsNullOrWhiteSpace(local))
                    card = JsonSerializer.Deserialize<MapCardDocument>(local, MapReadOptions);
            }
            catch { }
        }

        if (card is null || !string.Equals(card.Format, MapCardFormat, StringComparison.Ordinal) ||
            !string.Equals(card.WorldId, WorldId, StringComparison.Ordinal)) return false;

        ApplyMapCard(card);
        return true;
    }
}

public sealed class MapCardDocument
{
    public string Format { get; set; } = "RISTMAPCARD";
    public int Version { get; set; } = 2;
    public string CardId { get; set; } = "";
    public string OwnerAccountId { get; set; } = "";
    public string WorldId { get; set; } = "";
    public string MapName { get; set; } = "";
    public string Cartographer { get; set; } = "";
    public string InGameCreationDate { get; set; } = "";
    public string Visibility { get; set; } = "private";
    public bool Published { get; set; }
    public DateTimeOffset UpdatedAtUtc { get; set; }
    public string PreviewSvg { get; set; } = "";
    public string ManifestHash { get; set; } = "";
    public string ArtDataMark { get; set; } = "";
    public List<string> QuickSlotTileIds { get; set; } = [];
    public List<string> RequiredAssetIds { get; set; } = [];
    public List<string> AssetPackIds { get; set; } = [];
    public List<TileItem> Tiles { get; set; } = [];
}
