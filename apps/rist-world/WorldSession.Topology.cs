namespace RistWorld;

public sealed partial class WorldSession
{
    public const int LayersPerTier = 5;

    public int CubeX { get; private set; }
    public int CubeY { get; private set; }
    public int CubeZ { get; private set; }
    public WorldCubeRole CubeRole { get; private set; } = WorldCubeRole.GameMaster;
    public int PlaneIndex { get; private set; }
    public int TierIndex { get; private set; }
    public int LayerOffset { get; private set; }
    public int LocalZ => checked((TierIndex * LayersPerTier) + LayerOffset);
    public bool IsSeaLevel => LocalZ == 0;
    public bool IsGianaph => CubeX == 0 && CubeY == 0 && CubeZ == 0;
    public string WorldCoordinateLabel => $"Cube {CubeX},{CubeY},{CubeZ} • Plane {PlaneIndex} • Tier {TierIndex} • z={LocalZ}";

    public List<NpcBoundaryExchange> NpcBoundaryExchanges { get; private set; } = [];

    public void MoveTier(int delta)
    {
        if (delta == 0) return;
        TierIndex = checked(TierIndex + delta);
        LayerOffset = 0;
        Notify();
    }

    public void MovePlane(int delta)
    {
        if (delta == 0) return;
        PlaneIndex = checked(PlaneIndex + delta);
        Notify();
    }

    public void MoveLayer(int delta)
    {
        if (delta == 0) return;

        var targetZ = checked(LocalZ + delta);
        TierIndex = FloorDiv(targetZ, LayersPerTier);
        LayerOffset = targetZ - (TierIndex * LayersPerTier);
        Notify();
    }

    public void SetLayerOffset(int offset)
    {
        LayerOffset = Math.Clamp(offset, 0, LayersPerTier - 1);
        Notify();
    }

    public void SetWorldCube(int x, int y, int z, WorldCubeRole role)
    {
        CubeX = x;
        CubeY = y;
        CubeZ = z;
        CubeRole = role;
        Notify();
    }

    public bool TryExchangeNpcAcrossBoundary(
        string incomingNpcId,
        string outgoingNpcId,
        int fromCubeX,
        int fromCubeY,
        int fromCubeZ,
        int toCubeX,
        int toCubeY,
        int toCubeZ)
    {
        if (string.IsNullOrWhiteSpace(incomingNpcId) || string.IsNullOrWhiteSpace(outgoingNpcId)) return false;
        if (string.Equals(incomingNpcId, outgoingNpcId, StringComparison.Ordinal)) return false;

        NpcBoundaryExchanges.Add(new NpcBoundaryExchange(
            Guid.NewGuid().ToString("N"),
            incomingNpcId.Trim(),
            outgoingNpcId.Trim(),
            fromCubeX,
            fromCubeY,
            fromCubeZ,
            toCubeX,
            toCubeY,
            toCubeZ,
            DateTimeOffset.UtcNow));
        Notify();
        return true;
    }

    void ResetTopologyToCanonicalOrigin()
    {
        CubeX = 0;
        CubeY = 0;
        CubeZ = 0;
        CubeRole = WorldCubeRole.GameMaster;
        PlaneIndex = 0;
        TierIndex = 0;
        LayerOffset = 0;
        NpcBoundaryExchanges = [];
    }

    static int FloorDiv(int value, int divisor)
    {
        var quotient = value / divisor;
        var remainder = value % divisor;
        if (remainder != 0 && ((remainder < 0) != (divisor < 0))) quotient--;
        return quotient;
    }
}
