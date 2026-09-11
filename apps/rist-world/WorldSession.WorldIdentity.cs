namespace RistWorld;

public sealed partial class WorldSession
{
    // Legacy alpha identity remains available only for migration/discovery. The active
    // world is selected explicitly from the launcher and is never implied by startup.
    public const string LegacyAlphaWorldId = "shaelvien-geonaph-alpha-001";
    public const string CurrentWorldId = LegacyAlphaWorldId;

    string _worldId = "";
    string _worldDisplayName = "";

    public bool HasActiveWorld => !string.IsNullOrWhiteSpace(_worldId);
    public string WorldId => _worldId;
    public string WorldDisplayName => string.IsNullOrWhiteSpace(_worldDisplayName) ? MapName : _worldDisplayName;
    public string WorldOwnerAccountId => auth.RistAccountId;

    // Account storage owns a collection of worlds. Every world-owned cloud artifact
    // resolves beneath this stable root so one account may safely own many worlds.
    public string WorldsStoragePrefix => "worlds";
    public string WorldStoragePrefix => HasActiveWorld ? $"{WorldsStoragePrefix}/{WorldId}" : WorldsStoragePrefix;
    public string WorldCheckpointKey => $"{WorldStoragePrefix}/current.ristmap";

    // Browser persistence is also world-scoped. The legacy unscoped key remains only
    // as a migration source for the original alpha world.
    public string WorldLocalSaveKey => $"{SaveKey}.{WorldId}";
    public string WorldResetMarkerKey => $"{OceanResetMarkerKey}.{WorldId}";

    // World-owned spatial content always resolves beneath the world root.
    public string CurrentSpatialNodeId =>
        $"{WorldId}:plane:{PlaneIndex}:cube:{CubeX}:{CubeY}:{CubeZ}:tier:{TierIndex}:layer:{LayerOffset}";

    internal void SetActiveWorldIdentity(string worldId, string displayName)
    {
        worldId = (worldId ?? "").Trim();
        displayName = (displayName ?? "").Trim();
        if (worldId.Length == 0) throw new InvalidOperationException("A World ID is required.");
        if (displayName.Length == 0) throw new InvalidOperationException("A World Name is required.");
        _worldId = worldId;
        _worldDisplayName = displayName;
        MapName = displayName;
        _lastPrivateSnapshot = "";
        Notify();
    }

    // Empty WorldId is accepted only for legacy alpha saves so they can be adopted
    // into the original alpha world. A save naming another world is never loaded into
    // the currently selected world.
    public bool OwnsSavedWorld(SavedWorld? saved) =>
        saved is not null && HasActiveWorld &&
        (string.IsNullOrWhiteSpace(saved.WorldId) ||
         string.Equals(saved.WorldId, WorldId, StringComparison.Ordinal));
}
