namespace RistWorld;

public sealed partial class WorldSession
{
    /// <summary>Builder-facing layer identity is 1..10; storage remains 0..9.</summary>
    public int BuilderLayer => RecursiveWorldBuilderTopology.BuilderLayerFromOffset(LayerOffset);

    public RecursiveLayerIdentity ActiveLayerIdentity =>
        RecursiveWorldBuilderTopology.Identify(TierIndex, LayerOffset);

    public bool IsParallaxLayer => ActiveLayerIdentity.IsParallaxLayer;

    public int? ParallaxTierIdentifier => ActiveLayerIdentity.ParallaxTierIdentifier;

    public string RecursiveSpatialLabel =>
        $"{ViewportTier} • Cube {CubeX},{CubeY},{CubeZ} • Plane {PlaneIndex} • Tier {TierIndex} • Layer {BuilderLayer} • z={SceneZ}";

    public RecursiveViewerSnapshot RecursiveViewerState => new(
        ViewportTier,
        CubeX,
        CubeY,
        CubeZ,
        PlaneIndex,
        TierIndex,
        BuilderLayer,
        LayerOffset,
        SceneZ,
        IsParallaxLayer,
        ParallaxTierIdentifier,
        CompositeZView);
}

/// <summary>
/// Read-only projection consumed by viewer representations. Mutations remain in
/// WorldSession authorities; the viewer must not become a second source of truth.
/// </summary>
public sealed record RecursiveViewerSnapshot(
    string ActiveShaep,
    int CubeX,
    int CubeY,
    int CubeZ,
    int PlaneIndex,
    int TierIndex,
    int BuilderLayer,
    int StorageLayerOffset,
    int SceneZ,
    bool IsParallaxLayer,
    int? ParallaxTierIdentifier,
    bool CompositeZView);
