namespace RistWorld;

/// <summary>
/// Canonical topology vocabulary for the recursive WorldBuilder.
/// This class translates storage representation into builder-facing identity.
/// It does not own persisted world content.
/// </summary>
public static class RecursiveWorldBuilderTopology
{
    public const int LayersPerTier = 10;
    public const int WorldTierCount = 30;
    public const int WorldLayerCount = WorldTierCount * LayersPerTier;
    public const int FirstBuilderLayer = 1;
    public const int LastBuilderLayer = LayersPerTier;
    public const int ParallaxBuilderLayer = 1;

    public static int BuilderLayerFromOffset(int layerOffset)
    {
        if (layerOffset < 0 || layerOffset >= LayersPerTier)
            throw new ArgumentOutOfRangeException(nameof(layerOffset));
        return layerOffset + 1;
    }

    public static int OffsetFromBuilderLayer(int builderLayer)
    {
        if (builderLayer < FirstBuilderLayer || builderLayer > LastBuilderLayer)
            throw new ArgumentOutOfRangeException(nameof(builderLayer));
        return builderLayer - 1;
    }

    public static int SceneZFromAddress(int tierIndex, int layerOffset) =>
        checked((tierIndex * LayersPerTier) + layerOffset);

    public static RecursiveLayerIdentity Identify(int tierIndex, int layerOffset)
    {
        var builderLayer = BuilderLayerFromOffset(layerOffset);
        return new RecursiveLayerIdentity(
            tierIndex,
            builderLayer,
            layerOffset,
            SceneZFromAddress(tierIndex, layerOffset),
            builderLayer == ParallaxBuilderLayer,
            builderLayer == ParallaxBuilderLayer ? tierIndex : null);
    }
}

/// <summary>
/// Layer 1 has two meanings without consuming two layers: it is spatial Layer 1
/// and the parallax layer carrying the tier identifier.
/// </summary>
public sealed record RecursiveLayerIdentity(
    int TierIndex,
    int BuilderLayer,
    int StorageLayerOffset,
    int SceneZ,
    bool IsParallaxLayer,
    int? ParallaxTierIdentifier);

public enum RecursiveWorldBuilderDepth
{
    World,
    Region,
    Local,
    SiteOrBuilding,
    RoomOrInterior,
    TacticalEncounter,
    Object,
    Container,
    Contents
}
