namespace RistWorld;

/// <summary>
/// Canonical world-builder Z helpers. Tier/layer are a storage representation;
/// SceneZ is the navigation and stacking authority.
/// </summary>
public sealed partial class WorldSession
{
    public int MaxGuestSceneZ => (GuestTierCount * LayersPerTier) - 1;

    public static int SceneZOf(int tierIndex, int layerOffset) =>
        checked((tierIndex * LayersPerTier) + Math.Clamp(layerOffset, 0, LayersPerTier - 1));

    public static int SceneZOf(TileItem tile) => SceneZOf(tile.TierIndex, tile.LayerOffset);
    public static int SceneZOf(PieceItem piece) => SceneZOf(piece.TierIndex, piece.LayerOffset);

    public static (int TierIndex, int LayerOffset) SplitSceneZ(int sceneZ)
    {
        var tier = FloorDiv(sceneZ, LayersPerTier);
        var layer = sceneZ - (tier * LayersPerTier);
        return (tier, layer);
    }

    int ClampAccessibleSceneZ(int sceneZ) =>
        IsLoggedIn ? sceneZ : Math.Clamp(sceneZ, 0, MaxGuestSceneZ);

    /// <summary>
    /// Moves continuously through Z. Crossing the top/bottom layer naturally
    /// rolls into the adjacent tier instead of clamping inside the current tier.
    /// </summary>
    public void MoveSceneZ(int delta)
    {
        if (delta == 0) return;
        SetSceneZ(checked(SceneZ + delta));
    }

    public void SetSceneZ(int sceneZ)
    {
        var target = ClampAccessibleSceneZ(sceneZ);
        var (tier, layer) = SplitSceneZ(target);
        if (tier == TierIndex && layer == LayerOffset) return;

        StoreCurrentSpatialPage();
        TierIndex = tier;
        LayerOffset = layer;
        LoadCurrentSpatialPage();
        Notify();
    }

    /// <summary>
    /// Tier navigation preserves the current layer position. It is simply a
    /// LayersPerTier-sized movement along the same Z axis.
    /// </summary>
    public void MoveSceneTier(int delta)
    {
        if (delta == 0) return;
        MoveSceneZ(checked(delta * LayersPerTier));
    }
}
