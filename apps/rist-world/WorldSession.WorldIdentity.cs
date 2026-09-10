namespace RistWorld;

public sealed partial class WorldSession
{
    // Single-world alpha authority. Multi-world support should select another WorldId,
    // not redefine the runtime hierarchy or storage model.
    public const string CurrentWorldId = "shaelvien-geonaph-alpha-001";

    public string WorldId => CurrentWorldId;
    public string WorldDisplayName => MapName;
    public string WorldOwnerAccountId => auth.RistAccountId;
    public string WorldStoragePrefix => $"worlds/{WorldId}";
    public string WorldCheckpointKey => $"{WorldStoragePrefix}/current.ristmap";

    // World-owned spatial content always resolves beneath the world root.
    // Regions will attach below this boundary when Region authority is introduced.
    public string CurrentSpatialNodeId =>
        $"{WorldId}:plane:{PlaneIndex}:cube:{CubeX}:{CubeY}:{CubeZ}:tier:{TierIndex}:layer:{LayerOffset}";

    public bool OwnsSavedWorld(SavedWorld? saved) =>
        saved is not null &&
        (string.IsNullOrWhiteSpace(saved.WorldId) ||
         string.Equals(saved.WorldId, WorldId, StringComparison.Ordinal));
}
