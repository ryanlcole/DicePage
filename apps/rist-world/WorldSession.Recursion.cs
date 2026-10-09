namespace RistWorld;

public sealed partial class WorldSession
{
    // Canonical recursive containment. These are semantic contexts of one editor,
    // never separate editors. Tier/Layer are Z properties of the active context.
    public static readonly string[] RecursionTiers =
    [
        "WORLD",
        "REGION",
        "LOCAL",
        "SITE",
        "ROOM",
        "TACTICAL",
        "OBJECT",
        "CONTAINER",
        "CONTENTS"
    ];

    public static readonly string[] CanonicalMapScopes = RecursionTiers;
    public const string ShaelvienWorldPartitionKind = "ZONE";
    public const bool ShaelvienPartitionsArePerformanceOnly = true;

    // Representation defaults only. Camera state never changes semantic identity.
    public const int WorldDefaultViewDegrees = 0;
    public const int RegionDefaultViewDegrees = 15;
    public const int LocalDefaultViewDegrees = 30;

    // Compatibility alias while callers migrate from the old Layer wording.
    public static IReadOnlyList<string> RecursionLayers => RecursionTiers;

    private Dictionary<string,AtlasTile> _atlasById = new(StringComparer.Ordinal);
    private int _atlasIndexCount = -1;

    public string ViewportLayer { get; private set; } = "WORLD";
    public string ViewportTier => ViewportLayer;

    public void SetViewportTier(string? tier) => SetViewportLayer(tier);

    public void SetViewportLayer(string? layer)
    {
        var normalized = NormalizeRecursionTier(layer);
        if (ViewportLayer == normalized) return;
        ViewportLayer = normalized;
        Notify();
    }

    public static string NormalizeRecursionTier(string? tier)
    {
        var value = (tier ?? "WORLD").Trim().ToUpperInvariant();
        return value switch
        {
            "ZONE" or "CONTINENT" => "REGION",
            "AREA" or "LANDMARK" => "LOCAL",
            "BUILDING" => "SITE",
            "INTERIOR" => "ROOM",
            "ENCOUNTER" or "BATTLE_INSTANCE" or "PLAYER" or "INSTANCE" => "TACTICAL",
            "UNIVERSAL" or "WEATHER" or "" => "WORLD",
            _ when RecursionTiers.Contains(value) => value,
            _ => "WORLD"
        };
    }

    public static string NormalizeRecursionLayer(string? layer) => NormalizeRecursionTier(layer);

    public static int RecursionTierRank(string? tier)
    {
        var normalized = NormalizeRecursionTier(tier);
        var index = Array.IndexOf(RecursionTiers, normalized);
        return index < 0 ? 0 : index;
    }

    public static int RecursionLayerRank(string? layer) => RecursionTierRank(layer);

    public static string? ParentRecursionTier(string? tier)
    {
        var rank = RecursionTierRank(tier);
        return rank <= 0 ? null : RecursionTiers[rank - 1];
    }

    public static string? ChildRecursionTier(string? tier)
    {
        var rank = RecursionTierRank(tier);
        return rank >= RecursionTiers.Length - 1 ? null : RecursionTiers[rank + 1];
    }

    public bool EnterRecursiveChild()
    {
        var child = ChildRecursionTier(ViewportTier);
        if (child is null) return false;
        SetViewportTier(child);
        return true;
    }

    public bool ExitToRecursiveParent()
    {
        var parent = ParentRecursionTier(ViewportTier);
        if (parent is null) return false;
        SetViewportTier(parent);
        return true;
    }

    private AtlasTile? FindAtlasTile(string id)
    {
        if (_atlasIndexCount != AtlasTiles.Count)
        {
            _atlasById = new Dictionary<string,AtlasTile>(AtlasTiles.Count,StringComparer.Ordinal);
            foreach (var tile in AtlasTiles) _atlasById[tile.Id] = tile;
            _atlasIndexCount = AtlasTiles.Count;
        }
        return _atlasById.GetValueOrDefault(id);
    }

    public string NativeLayer(AtlasTile tile)
    {
        if (string.Equals(tile.Layer,"WEATHER",StringComparison.OrdinalIgnoreCase)) return "WEATHER";
        if (string.Equals(tile.Layer,"UNIVERSAL",StringComparison.OrdinalIgnoreCase)) return ViewportTier;
        return NormalizeRecursionTier(tile.Layer);
    }

    public string NativeLayer(StagedAsset staged)
    {
        if (staged.Kind == "tile" && staged.Key.StartsWith("tile:",StringComparison.Ordinal))
        {
            var atlas = FindAtlasTile(staged.Key[5..]);
            if (atlas is not null) return NativeLayer(atlas);
        }
        return staged.Kind switch
        {
            "rolling-stock" => "REGION",
            "mini" => "TACTICAL",
            "pawn" or "pin" => "LOCAL",
            "terrain" => "LOCAL",
            "bit" => "OBJECT",
            _ => ViewportTier
        };
    }

    public string NativeLayer(TileItem tile)
    {
        var atlas = FindAtlasTile(tile.Id);
        if (atlas is not null) return NativeLayer(atlas);
        return ViewportTier;
    }

    public string NativeLayer(PieceItem piece) => piece.Kind switch
    {
        "rolling-stock" => "REGION",
        "mini" => "TACTICAL",
        "pawn" or "pin" => "LOCAL",
        "terrain" => "LOCAL",
        "bit" => "OBJECT",
        _ => ViewportTier
    };

    public bool LayerParticipatesInViewport(string? nativeLayer)
    {
        if (string.Equals(nativeLayer,"WEATHER",StringComparison.OrdinalIgnoreCase))
            return RecursionTierRank(ViewportTier) <= RecursionTierRank("LOCAL");
        return RecursionTierRank(nativeLayer) <= RecursionTierRank(ViewportTier);
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
