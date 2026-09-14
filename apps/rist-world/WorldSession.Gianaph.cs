namespace RistWorld;

public sealed partial class WorldSession
{
    // Legacy Geonaph metadata remains for save compatibility and authored layer labels.
    // It is not a terrain generator: Geonaph is built manually from Library assets.
    public const int GianaphStateColumns = 20;
    public const int GianaphStateRows = 13;
    public const int GianaphStatesAcross = 4;
    public const int GianaphStatesDown = 4;
    public const int GianaphTierStride = 5;
    public const int GianaphTierGap = 4;

    public List<GianaphCell> GianaphCells { get; } = [];
    public IReadOnlyList<GianaphLayerSpec> GianaphLayers { get; } =
    [
        new(-1, 1, -5, "Ocean floor"),
        new( 1, 1,  0, "Ocean surface"),
        new( 1, 2,  1, "Beach / shore"),
        new( 2, 1,  5, "Land"),
        new( 2, 2,  6, "Raised land / hills"),
        new( 2, 3,  7, "Mountains / high terrain")
    ];

    public static int GianaphLayerZ(int tier, int layer)
    {
        if (layer < 1) throw new ArgumentOutOfRangeException(nameof(layer));
        var tierBase = tier < 0 ? tier * GianaphTierStride : (tier - 1) * GianaphTierStride;
        return tierBase + layer - 1;
    }

    // Legacy callers may still invoke this method. It intentionally creates no terrain.
    // Authored tiles already present are preserved; an empty Geonaph remains empty.
    void BuildGianaphWorld()
    {
        MapName = GeonaphDisplayName;
        GianaphCells.Clear();
        MapLocked = true;
    }
}

public sealed record GianaphLayerSpec(int Tier, int Layer, int Z, string Name);
public sealed record GianaphCell(int Column, int Row, int StateColumn, int StateRow, int Tier, int Layer, int Z, string Terrain, string AtlasTileId);
