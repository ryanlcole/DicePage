namespace RistWorld;

public sealed partial class WorldSession
{
    // Canonical developer authority for Geonaph's sea-level origin. The world uses
    // sparse terrain storage, so an empty tile collection at this address means the
    // implicit Ocean 071 base rather than an unbuilt layer.
    public const string GeonaphOriginAuthoritySpatialAddress = "p0:c0,0,0:t0:l0";
    public const string GeonaphOriginAuthorityRole = "developer";

    SavedWorld CreateGeonaphOriginSeed() => new()
    {
        WorldId = GeonaphWorldId,
        WorldName = GeonaphDisplayName,
        Reset = OceanResetVersion,
        OperatingMode = "mmo",
        Role = "GM",
        Layer = "WORLD",
        GridStyle = "square",
        DistanceUnit = "km",
        GridDiameter = 48,
        GridDistance = 1,
        GridCalibrationZoom = 1,
        CubeX = 0,
        CubeY = 0,
        CubeZ = 0,
        CubeRole = WorldCubeRole.Developer,
        PlaneIndex = 0,
        TierIndex = 0,
        LayerOffset = 0,
        Pieces = [],
        Tiles = [],
        NpcBoundaryExchanges = []
    };

    // Repair identity/authority without destroying authored terrain. This is safe to
    // run against existing Geonaph saves and turns older GameMaster-labelled origin
    // checkpoints into the canonical Developer-owned origin cube.
    bool EnsureGeonaphOriginLayerInvariant()
    {
        if (!IsGeonaphWorld) return false;

        var changed = false;
        if (!string.Equals(MapId, OriginMapId, StringComparison.Ordinal))
        {
            MapId = OriginMapId;
            changed = true;
        }
        if (!string.Equals(MapName, GeonaphDisplayName, StringComparison.Ordinal))
        {
            MapName = GeonaphDisplayName;
            changed = true;
        }
        if (CubeX == 0 && CubeY == 0 && CubeZ == 0 && CubeRole != WorldCubeRole.Developer)
        {
            CubeRole = WorldCubeRole.Developer;
            changed = true;
        }

        // Prevent the legacy bootstrap from treating a restored sparse world as an
        // uninitialized world and clearing authored content later in the session.
        _originMapApplied = true;
        return changed;
    }
}
