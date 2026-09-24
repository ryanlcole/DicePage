namespace RistWorld;

/// <summary>
/// Canonical nested vertical address for a point/object as it descends through
/// WORLD → REGION → LOCAL → INSTANCE. Parent coordinates are retained when a
/// child scale is entered; child tier/layer pairs do not overwrite parent Z.
/// </summary>
public sealed record RistHierarchicalAddress(
    int WorldTier = 0,
    int WorldLayer = 0,
    int RegionTier = 0,
    int RegionLayer = 0,
    int LocalTier = 0,
    int LocalLayer = 0,
    int InstanceTier = 0,
    int InstanceLayer = 0)
{
    public RistHierarchicalAddress Normalized() => this with
    {
        WorldTier = Math.Max(0, WorldTier),
        WorldLayer = Math.Clamp(WorldLayer, 0, 9),
        RegionTier = Math.Max(0, RegionTier),
        RegionLayer = Math.Clamp(RegionLayer, 0, 9),
        LocalTier = Math.Max(0, LocalTier),
        LocalLayer = Math.Clamp(LocalLayer, 0, 9),
        InstanceTier = Math.Max(0, InstanceTier),
        InstanceLayer = Math.Clamp(InstanceLayer, 0, 9)
    };

    public override string ToString()
        => $"W T{WorldTier}:L{WorldLayer} · R T{RegionTier}:L{RegionLayer} · L T{LocalTier}:L{LocalLayer} · I T{InstanceTier}:L{InstanceLayer}";
}
