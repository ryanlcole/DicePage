namespace RistWorld;

public sealed partial class WorldSession
{
    // The original alpha ID/path names remain stable for migration and save compatibility.
    // The canonical MMO world is Shaelvien. Endemar is its protected starting point/origin;
    // Jeyrusal remains the primary continent name carried by existing content.
    public const string LegacyAlphaWorldId = "shaelvien-geonaph-alpha-001";
    public const string GeonaphWorldId = LegacyAlphaWorldId;
    public const string ShaelvienDisplayName = "Shaelvien";
    public const string EndemarStartingPointDisplayName = "Endemar";
    public const string GeonaphDisplayName = ShaelvienDisplayName;
    public const string EndemarContinentDisplayName = "Jeyrusal";
    public const string CurrentWorldId = LegacyAlphaWorldId;

    string _worldId = "";
    string _worldDisplayName = "";

    public bool HasActiveWorld => !string.IsNullOrWhiteSpace(_worldId);
    public string WorldId => _worldId;
    public string WorldDisplayName => string.IsNullOrWhiteSpace(_worldDisplayName) ? MapName : _worldDisplayName;
    public string WorldOwnerAccountId => auth.RistAccountId;
    public bool IsGeonaphWorld => string.Equals(WorldId, GeonaphWorldId, StringComparison.Ordinal);
    public bool IsWorldExtentUnbounded => HasActiveWorld && IsGeonaphWorld;
    public int? WorldTileLimit => IsWorldExtentUnbounded ? null : DefaultWorldWidthKm;
    public int SurfaceWorldWidthPixels => SurfaceWorldPixelLimit ?? DefaultSurfaceWorldWidthPixels;
    public int SurfaceWorldHeightPixels => SurfaceWorldPixelLimit ?? DefaultSurfaceWorldHeightPixels;
    public string WorldExtentLabel => IsGeonaphWorld
        ? $"{DefaultSurfaceWorldWidthPixels}×{DefaultSurfaceWorldHeightPixels} PX STARTING SURFACE · SHAELVIEN DEVELOPER CONTROLLED"
        : $"{SurfaceWorldWidthPixels}×{SurfaceWorldHeightPixels} PX SURFACE ALLOWANCE";

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
        if (string.Equals(worldId, GeonaphWorldId, StringComparison.Ordinal)) displayName = GeonaphDisplayName;
        if (displayName.Length == 0) throw new InvalidOperationException("A World Name is required.");
        _worldId = worldId;
        _worldDisplayName = displayName;
        _activeWorldRelationship = "";
        MapName = displayName;
        _persistedTruth.Clear();
        Notify();
    }

    // Empty WorldId belongs only to the original legacy alpha save. It must never be
    // adopted into a newly created/imported world.
    public bool OwnsSavedWorld(SavedWorld? saved) =>
        saved is not null && HasActiveWorld &&
        (string.Equals(saved.WorldId, WorldId, StringComparison.Ordinal) ||
         (string.IsNullOrWhiteSpace(saved.WorldId) &&
          string.Equals(WorldId, LegacyAlphaWorldId, StringComparison.Ordinal)));
}
