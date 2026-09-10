namespace RistWorld;

public sealed partial class WorldSession
{
    // Single-world alpha authority. Multi-world support selects another WorldId;
    // it does not redefine the runtime hierarchy, coordinate system, or storage model.
    public const string CurrentWorldId = "shaelvien-geonaph-alpha-001";

    public string WorldId => CurrentWorldId;
    public string WorldDisplayName => MapName;
    public string WorldOwnerAccountId => auth.RistAccountId;

    // Account storage owns a collection of worlds. Every world-owned cloud artifact
    // resolves beneath this stable root so a future account may safely own many worlds.
    public string WorldsStoragePrefix => "worlds";
    public string WorldStoragePrefix => $"{WorldsStoragePrefix}/{WorldId}";
    public string WorldCheckpointKey => $"{WorldStoragePrefix}/current.ristmap";

    // Browser persistence is also world-scoped. The legacy unscoped key remains only
    // as a one-time migration source for the first alpha world.
    public string WorldLocalSaveKey => $"{SaveKey}.{WorldId}";
    public string WorldResetMarkerKey => $"{OceanResetMarkerKey}.{WorldId}";

    // World-owned spatial content always resolves beneath the world root.
    // Regions will attach below this boundary when Region authority is introduced.
    public string CurrentSpatialNodeId =>
        $"{WorldId}:plane:{PlaneIndex}:cube:{CubeX}:{CubeY}:{CubeZ}:tier:{TierIndex}:layer:{LayerOffset}";

    // Empty WorldId is accepted only for legacy alpha saves so they can be adopted
    // into the current world. A save naming another world is never loaded here.
    public bool OwnsSavedWorld(SavedWorld? saved) =>
        saved is not null &&
        (string.IsNullOrWhiteSpace(saved.WorldId) ||
         string.Equals(saved.WorldId, WorldId, StringComparison.Ordinal));
}
