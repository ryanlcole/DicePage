namespace RistWorld;

public sealed partial class WorldSession
{
    public static readonly string[] RecursionLayers =
    [
        "WORLD","REGION","LOCAL","SITE","ROOM","ENCOUNTER","OBJECT","CONTAINER","CONTENTS","WEATHER"
    ];

    public string ViewportLayer { get; private set; } = "WORLD";

    public void SetViewportLayer(string? layer)
    {
        var normalized = NormalizeRecursionLayer(layer);
        if (ViewportLayer == normalized) return;
        ViewportLayer = normalized;
        Notify();
    }

    public static string NormalizeRecursionLayer(string? layer)
    {
        var value = (layer ?? "WORLD").Trim().ToUpperInvariant();
        return value switch
        {
            "ZONE" or "CONTINENT" => "REGION",
            "AREA" => "LOCAL",
            "TACTICAL" or "INSTANCE" => "ENCOUNTER",
            "UNIVERSAL" or "" => "WORLD",
            _ when RecursionLayers.Contains(value) => value,
            _ => "WORLD"
        };
    }

    public static int RecursionLayerRank(string? layer)
    {
        var normalized = NormalizeRecursionLayer(layer);
        var index = Array.IndexOf(RecursionLayers, normalized);
        return index < 0 ? 0 : index;
    }

    public string NativeLayer(AtlasTile tile)
    {
        if (string.Equals(tile.Layer,"UNIVERSAL",StringComparison.OrdinalIgnoreCase)) return ViewportLayer;
        return NormalizeRecursionLayer(tile.Layer);
    }

    public string NativeLayer(StagedAsset staged)
    {
        if (staged.Kind == "tile" && staged.Key.StartsWith("tile:",StringComparison.Ordinal))
        {
            var id = staged.Key[5..];
            var atlas = AtlasTiles.FirstOrDefault(x => x.Id == id);
            if (atlas is not null) return NativeLayer(atlas);
        }
        return staged.Kind switch
        {
            "rolling-stock" => "REGION",
            "mini" => "ENCOUNTER",
            "pawn" or "pin" => "LOCAL",
            "terrain" => "LOCAL",
            "bit" => "OBJECT",
            _ => ViewportLayer
        };
    }

    public string NativeLayer(TileItem tile)
    {
        var atlas = AtlasTiles.FirstOrDefault(x => x.Id == tile.Id);
        if (atlas is not null) return NativeLayer(atlas);
        return ViewportLayer;
    }

    public string NativeLayer(PieceItem piece) => piece.Kind switch
    {
        "rolling-stock" => "REGION",
        "mini" => "ENCOUNTER",
        "pawn" or "pin" => "LOCAL",
        "terrain" => "LOCAL",
        "bit" => "OBJECT",
        _ => ViewportLayer
    };

    public bool LayerParticipatesInViewport(string? nativeLayer)
    {
        var normalized = NormalizeRecursionLayer(nativeLayer);
        if (normalized == "WEATHER") return RecursionLayerRank(ViewportLayer) <= RecursionLayerRank("ROOM");
        return RecursionLayerRank(normalized) <= RecursionLayerRank(ViewportLayer);
    }

    public bool LooksLikeWeatherBlocker(TileItem tile)
    {
        var name = tile.Name ?? string.Empty;
        return name.Contains("roof",StringComparison.OrdinalIgnoreCase)
            || name.Contains("ceiling",StringComparison.OrdinalIgnoreCase)
            || name.Contains("canopy",StringComparison.OrdinalIgnoreCase)
            || name.Contains("overhang",StringComparison.OrdinalIgnoreCase);
    }
}
