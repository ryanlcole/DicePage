using Microsoft.JSInterop;

namespace RistWorld.Components;

public partial class WorldBuilderStudio
{
    const string AssetKeyboardWidthAttribute = "placement.width.cells";
    const string AssetKeyboardHeightAttribute = "placement.height.cells";

    internal static WorldBuilderStudio? ActiveAssetKeyboardInstance { get; private set; }

    protected override void OnInitialized()
    {
        base.OnInitialized();
        ActiveAssetKeyboardInstance = this;
    }

    [JSInvokable]
    public Task<WorldBuilderAssetKeyboardItem[]> GetAssetKeyboardCatalog()
    {
        var items = Session.AtlasTiles
            .Where(asset => !string.IsNullOrWhiteSpace(asset.Id) && !string.IsNullOrWhiteSpace(asset.Image))
            .OrderBy(asset => asset.Layer, StringComparer.OrdinalIgnoreCase)
            .ThenBy(asset => asset.Directory, StringComparer.OrdinalIgnoreCase)
            .ThenBy(asset => asset.Folder, StringComparer.OrdinalIgnoreCase)
            .ThenBy(asset => asset.Name, StringComparer.OrdinalIgnoreCase)
            .Take(5000)
            .Select(asset => new WorldBuilderAssetKeyboardItem(
                asset.Id,
                asset.Name,
                asset.Image,
                asset.Layer,
                asset.Directory,
                asset.Folder,
                asset.AssetKind,
                asset.Author,
                Math.Max(1, asset.DefaultFootprint)))
            .ToArray();
        return Task.FromResult(items);
    }

    static int AssetKeyboardDimension(TileItem tile, string key, int fallback)
    {
        if (tile.Metadata?.Attributes is { } attributes &&
            attributes.TryGetValue(key, out var raw) &&
            int.TryParse(raw, out var parsed))
            return Math.Clamp(parsed, 1, WorldSession.GridColumns);
        return Math.Clamp(fallback, 1, WorldSession.GridColumns);
    }

    static (int Width, int Height) AssetKeyboardFootprint(TileItem tile)
    {
        var legacy = Math.Clamp((int)Math.Round(FootprintFor(tile)), 1, WorldSession.GridColumns);
        var width = AssetKeyboardDimension(tile, AssetKeyboardWidthAttribute, legacy);
        var height = AssetKeyboardDimension(tile, AssetKeyboardHeightAttribute, legacy);
        if ((tile.RotationQuarterTurns & 1) != 0) (width, height) = (height, width);
        return (width, height);
    }

    [JSInvokable]
    public Task<WorldBuilderAssetKeyboardFootprint[]> GetAssetKeyboardFootprints()
    {
        var result = Session.PlacedTiles.Select((tile, index) =>
        {
            var footprint = AssetKeyboardFootprint(tile);
            return new WorldBuilderAssetKeyboardFootprint(index, footprint.Width, footprint.Height);
        }).ToArray();
        return Task.FromResult(result);
    }

    [JSInvokable]
    public async Task<int> PlaceAssetKeyboardItemFromJs(string assetId, double worldX, double worldY, int widthCells, int heightCells)
    {
        EnsureWorldBuilderHistory();
        if (!Session.CanEditTiles || !double.IsFinite(worldX) || !double.IsFinite(worldY)) return -1;

        var asset = FindAsset(assetId);
        if (asset is null) return -1;

        widthCells = Math.Clamp(widthCells, 1, WorldSession.GridColumns);
        heightCells = Math.Clamp(heightCells, 1, WorldSession.GridRows);
        worldX = Math.Clamp(worldX, 0, 1);
        worldY = Math.Clamp(worldY, 0, 1);

        // X/Y from the keyboard represent the desired center under the finger.
        // Canonical TileItem coordinates remain the top-left grid anchor.
        var column = Math.Clamp(
            (int)Math.Floor(worldX * WorldSession.GridColumns - widthCells / 2.0),
            0,
            Math.Max(0, WorldSession.GridColumns - widthCells));
        var row = Math.Clamp(
            (int)Math.Floor(worldY * WorldSession.GridRows - heightCells / 2.0),
            0,
            Math.Max(0, WorldSession.GridRows - heightCells));

        PlacementChoice choice;
        try { choice = await JS.InvokeAsync<PlacementChoice>("ristPlacement.consume"); }
        catch { choice = new(false, false, "normal"); }

        var placed = CreateViewerTile(asset, column, row, widthCells, NormalizeTreatment(choice.Treatment));
        var attributes = new Dictionary<string, string>(StringComparer.Ordinal)
        {
            [AssetKeyboardWidthAttribute] = widthCells.ToString(System.Globalization.CultureInfo.InvariantCulture),
            [AssetKeyboardHeightAttribute] = heightCells.ToString(System.Globalization.CultureInfo.InvariantCulture),
            ["asset.id"] = asset.Id,
            ["asset.author"] = asset.Author,
            ["asset.layer"] = asset.Layer,
            ["placement.source"] = "asset-keyboard"
        };
        placed = placed with
        {
            TypeId = asset.TypeId,
            GroupId = asset.GroupId,
            Metadata = new AssetByMetadata(
                string.IsNullOrWhiteSpace(asset.TypeId) ? asset.AssetKind : asset.TypeId,
                Description: asset.Name,
                Provenance: "UNKNOWN",
                Attributes: attributes),
            ShaepId = Session.ResolveShaepId(asset)
        };

        if (choice.UpperTier)
            placed = placed with { TierIndex = Session.TierIndex + 1, LayerOffset = 0 };

        // UpperLayer no longer moves Z. It becomes an explicit composition
        // request when the recursive WORLD placement is registered below.
        PushWorldBuilderUndo();
        ClearWorldBuilderSelection();
        Session.AddPlacedTileAtGridDepth(placed);

        var index = Session.PlacedTiles.FindIndex(item =>
            string.Equals(item.PlacementId, placed.PlacementId, StringComparison.Ordinal));
        if (index >= 0)
            Session.RegisterNewWorldTilePlacement(index, forceFront: choice.UpperLayer);

        Session.Notify();
        await PersistWorldBuilderAsync();
        return index;
    }
}

public sealed record WorldBuilderAssetKeyboardItem(
    string Id,
    string Name,
    string Image,
    string Layer,
    string Directory,
    string Folder,
    string AssetKind,
    string Author,
    int DefaultFootprint);

public sealed record WorldBuilderAssetKeyboardFootprint(int Index, int WidthCells, int HeightCells);
