namespace RistWorld;

public sealed partial class WorldSession
{
    // Canonical developer authority for Geonaph's sea-level origin. Terrain storage
    // is explicit: an empty tile collection means an unbuilt layer, never implicit ocean.
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

    // Repair identity/authority without destroying manually authored terrain. Legacy
    // auto-generated Geonaph terrain is removed so restored worlds follow manual-build canon.
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

        var tileCount = PlacedTiles.Count;
        ClearGeneratedGeonaphPackagePlacements();
        if (PlacedTiles.Count != tileCount) changed = true;

        // Prevent the legacy bootstrap from treating a restored sparse world as an
        // uninitialized world and changing authored content later in the session.
        _originMapApplied = true;
        return changed;
    }
}
