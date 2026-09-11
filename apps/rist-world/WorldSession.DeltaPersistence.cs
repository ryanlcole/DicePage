using System.Text.Json;

namespace RistWorld;

public sealed partial class WorldSession
{
    const int DeltaCheckpointInterval = 12;
    const string DeltaFormat = "RISTDELTA";
    const int DeltaFormatVersion = 1;

    long _worldRevision;
    long _worldBaseRevision;
    string _worldBaseCheckpointKey = "";
    readonly List<string> _worldDeltaKeys = [];

    public string WorldDeltaHeadKey => $"{WorldStoragePrefix}/delta-head.json";
    public string WorldDeltaPrefix => $"{WorldStoragePrefix}/deltas";
    public string WorldCheckpointArchivePrefix => $"{WorldStoragePrefix}/checkpoints";

    string WorldDeltaKey(long revision) => $"{WorldDeltaPrefix}/{revision:D20}.ristdelta";
    string WorldCheckpointArchiveKey(long revision) => $"{WorldCheckpointArchivePrefix}/{revision:D20}.ristmap";

    void ResetDeltaPersistenceState()
    {
        _worldRevision = 0;
        _worldBaseRevision = 0;
        _worldBaseCheckpointKey = "";
        _worldDeltaKeys.Clear();
        _lastPrivateSnapshot = "";
    }

    async Task CommitCheckpointHeadAsync(string checkpointJson)
    {
        var archiveKey = WorldCheckpointArchiveKey(_worldRevision);

        // Immutable checkpoint first, mutable compatibility pointer second, head last.
        // If a later write fails, the prior head remains authoritative.
        await auth.UploadTextAsync(archiveKey, checkpointJson, "application/json");
        await auth.UploadTextAsync(WorldCheckpointKey, checkpointJson, "application/json");

        var head = new WorldDeltaHead
        {
            WorldId = WorldId,
            BaseRevision = _worldRevision,
            LatestRevision = _worldRevision,
            BaseCheckpointKey = archiveKey,
            DeltaKeys = [],
            UpdatedAtUtc = DateTimeOffset.UtcNow
        };
        await auth.UploadTextAsync(WorldDeltaHeadKey, JsonSerializer.Serialize(head, MapWriteOptions), "application/json");

        _worldBaseRevision = _worldRevision;
        _worldBaseCheckpointKey = archiveKey;
        _worldDeltaKeys.Clear();
    }

    async Task EnsureArchivedBaselineAsync()
    {
        if (!string.IsNullOrWhiteSpace(_worldBaseCheckpointKey)) return;
        if (string.IsNullOrWhiteSpace(_lastPrivateSnapshot)) return;

        var archiveKey = WorldCheckpointArchiveKey(_worldRevision);
        await auth.UploadTextAsync(archiveKey, _lastPrivateSnapshot, "application/json");
        _worldBaseRevision = _worldRevision;
        _worldBaseCheckpointKey = archiveKey;
    }

    async Task SavePrivateDeltaAsync(bool showSuccess)
    {
        if (!HasActiveWorld || !IsLoggedIn) return;

        if (string.IsNullOrWhiteSpace(_lastPrivateSnapshot))
        {
            await SavePrivateCheckpointAsync(showSuccess);
            return;
        }

        // Compare at the current canonical revision. Revision itself must not create a change.
        var unchangedCandidate = ExportMapJson(_worldRevision);
        if (string.Equals(unchangedCandidate, _lastPrivateSnapshot, StringComparison.Ordinal))
        {
            if (showSuccess)
            {
                PrivateStorageStatus = $"{WorldDisplayName} is already synced at revision {_worldRevision}.";
                Notify();
            }
            return;
        }

        var previous = JsonSerializer.Deserialize<SavedWorld>(_lastPrivateSnapshot, MapReadOptions);
        if (previous is null || !OwnsSavedWorld(previous) || previous.Revision != _worldRevision)
        {
            // Legacy/unknown baseline: establish a new complete canonical checkpoint rather
            // than guessing at a delta origin.
            await SavePrivateCheckpointAsync(showSuccess);
            return;
        }

        var nextRevision = checked(_worldRevision + 1);
        var currentJson = ExportMapJson(nextRevision);
        var current = JsonSerializer.Deserialize<SavedWorld>(currentJson, MapReadOptions)
            ?? throw new InvalidOperationException("The current world state could not be materialized for delta storage.");

        var patch = BuildWorldDelta(previous, current, _worldRevision, nextRevision);
        await EnsureWorldRelationshipAsync();
        await EnsureArchivedBaselineAsync();

        var deltaKey = WorldDeltaKey(nextRevision);
        await auth.UploadTextAsync(deltaKey, JsonSerializer.Serialize(patch, MapWriteOptions), "application/json");

        var nextKeys = _worldDeltaKeys.Concat([deltaKey]).Distinct(StringComparer.Ordinal).ToList();
        var head = new WorldDeltaHead
        {
            WorldId = WorldId,
            BaseRevision = _worldBaseRevision,
            LatestRevision = nextRevision,
            BaseCheckpointKey = _worldBaseCheckpointKey,
            DeltaKeys = nextKeys,
            UpdatedAtUtc = DateTimeOffset.UtcNow
        };

        // Head is the commit point. The immutable delta is not canonical until the head
        // points at it, so interrupted uploads cannot create a half-applied world state.
        await auth.UploadTextAsync(WorldDeltaHeadKey, JsonSerializer.Serialize(head, MapWriteOptions), "application/json");

        _worldRevision = nextRevision;
        _worldDeltaKeys.Clear();
        _worldDeltaKeys.AddRange(nextKeys);
        _lastPrivateSnapshot = currentJson;
        await js.InvokeVoidAsync("localStorage.setItem", WorldLocalSaveKey, currentJson);

        // Bound materialization cost without deleting history. Old immutable checkpoints
        // and deltas remain as historical truth; only the head advances to a newer base.
        if (_worldDeltaKeys.Count >= DeltaCheckpointInterval)
            await SavePrivateCheckpointAsync(showSuccess: false, snapshot: currentJson);

        if (showSuccess)
        {
            PrivateStorageStatus = $"{WorldDisplayName} synced as canonical revision {_worldRevision}.";
            Notify();
        }
    }

    async Task<SavedWorld> LoadPrivateDeltaChainAsync(SavedWorld currentPointer)
    {
        var head = await auth.DownloadJsonAsync<WorldDeltaHead>(WorldDeltaHeadKey);
        if (head is null)
        {
            _worldRevision = Math.Max(0, currentPointer.Revision);
            _worldBaseRevision = _worldRevision;
            _worldBaseCheckpointKey = "";
            _worldDeltaKeys.Clear();
            return currentPointer;
        }

        if (!string.Equals(head.WorldId, WorldId, StringComparison.Ordinal))
            throw new InvalidOperationException("Delta head identity does not match the active world.");
        if (head.BaseRevision < 0 || head.LatestRevision < head.BaseRevision)
            throw new InvalidOperationException("Delta head revision range is invalid.");

        var baseWorld = currentPointer;
        if (baseWorld.Revision != head.BaseRevision)
        {
            // A newer complete pointer makes an older head harmless (for example, an
            // interrupted compaction after the full checkpoint was committed).
            if (baseWorld.Revision >= head.LatestRevision)
            {
                _worldRevision = baseWorld.Revision;
                _worldBaseRevision = baseWorld.Revision;
                _worldBaseCheckpointKey = WorldCheckpointArchiveKey(baseWorld.Revision);
                _worldDeltaKeys.Clear();
                return baseWorld;
            }

            if (string.IsNullOrWhiteSpace(head.BaseCheckpointKey))
                throw new InvalidOperationException("Delta history is missing its canonical base checkpoint.");

            baseWorld = await auth.DownloadJsonAsync<SavedWorld>(head.BaseCheckpointKey)
                ?? throw new InvalidOperationException("The canonical delta base checkpoint could not be loaded.");
            if (!OwnsSavedWorld(baseWorld) || baseWorld.Revision != head.BaseRevision)
                throw new InvalidOperationException("The canonical delta base checkpoint does not match the delta head.");
        }

        if (head.LatestRevision == head.BaseRevision)
        {
            _worldRevision = head.LatestRevision;
            _worldBaseRevision = head.BaseRevision;
            _worldBaseCheckpointKey = head.BaseCheckpointKey;
            _worldDeltaKeys.Clear();
            return baseWorld;
        }

        var keys = (head.DeltaKeys ?? [])
            .Where(key => !string.IsNullOrWhiteSpace(key))
            .Distinct(StringComparer.Ordinal)
            .ToArray();
        if (keys.Length == 0)
            throw new InvalidOperationException("Delta head names a newer revision but contains no delta keys.");

        var patches = await Task.WhenAll(keys.Select(key => auth.DownloadJsonAsync<WorldDeltaPatch>(key)));
        if (patches.Any(patch => patch is null))
            throw new InvalidOperationException("One or more canonical world deltas could not be loaded.");

        var ordered = patches.Cast<WorldDeltaPatch>().OrderBy(patch => patch.ToRevision).ToArray();
        var materialized = CloneSavedWorld(baseWorld);
        var expected = head.BaseRevision;
        foreach (var patch in ordered)
        {
            if (!string.Equals(patch.Format, DeltaFormat, StringComparison.Ordinal) || patch.Version != DeltaFormatVersion)
                throw new InvalidOperationException("World delta format is not supported.");
            if (!string.Equals(patch.WorldId, WorldId, StringComparison.Ordinal))
                throw new InvalidOperationException("World delta identity does not match the active world.");
            if (patch.FromRevision != expected || patch.ToRevision != expected + 1)
                throw new InvalidOperationException("World delta history is not contiguous.");
            if (!string.Equals(WorldDeltaKey(patch.ToRevision), keys.FirstOrDefault(key => key.EndsWith($"/{patch.ToRevision:D20}.ristdelta", StringComparison.Ordinal)), StringComparison.Ordinal))
                throw new InvalidOperationException("World delta key does not match its revision.");

            materialized = ApplyWorldDelta(materialized, patch);
            expected = patch.ToRevision;
        }

        if (expected != head.LatestRevision)
            throw new InvalidOperationException("World delta history does not reach the canonical head revision.");

        _worldRevision = head.LatestRevision;
        _worldBaseRevision = head.BaseRevision;
        _worldBaseCheckpointKey = head.BaseCheckpointKey;
        _worldDeltaKeys.Clear();
        _worldDeltaKeys.AddRange(keys);
        return materialized;
    }

    static SavedWorld CloneSavedWorld(SavedWorld source) =>
        JsonSerializer.Deserialize<SavedWorld>(JsonSerializer.Serialize(source, MapWriteOptions), MapReadOptions)
        ?? throw new InvalidOperationException("World state could not be cloned.");

    static WorldDeltaPatch BuildWorldDelta(SavedWorld previous, SavedWorld current, long fromRevision, long toRevision)
    {
        var previousTiles = GroupTiles(previous.Tiles);
        var currentTiles = GroupTiles(current.Tiles);
        var tilePages = new List<WorldDeltaTilePage>();
        foreach (var address in previousTiles.Keys.Union(currentTiles.Keys).Order())
        {
            previousTiles.TryGetValue(address, out var before);
            currentTiles.TryGetValue(address, out var after);
            before ??= [];
            after ??= [];
            if (!before.SequenceEqual(after)) tilePages.Add(new WorldDeltaTilePage(address, after.ToList()));
        }

        var previousPieces = GroupPieces(previous.Pieces);
        var currentPieces = GroupPieces(current.Pieces);
        var piecePages = new List<WorldDeltaPiecePage>();
        foreach (var address in previousPieces.Keys.Union(currentPieces.Keys).Order())
        {
            previousPieces.TryGetValue(address, out var before);
            currentPieces.TryGetValue(address, out var after);
            before ??= [];
            after ??= [];
            if (!before.SequenceEqual(after)) piecePages.Add(new WorldDeltaPiecePage(address, after.ToList()));
        }

        return new WorldDeltaPatch
        {
            Format = DeltaFormat,
            Version = DeltaFormatVersion,
            WorldId = current.WorldId,
            FromRevision = fromRevision,
            ToRevision = toRevision,
            CreatedAtUtc = DateTimeOffset.UtcNow,
            Header = HeaderOnly(current),
            TilePages = tilePages,
            PiecePages = piecePages,
            NpcBoundaryExchanges = previous.NpcBoundaryExchanges.SequenceEqual(current.NpcBoundaryExchanges)
                ? null
                : current.NpcBoundaryExchanges.ToList()
        };
    }

    static SavedWorld ApplyWorldDelta(SavedWorld source, WorldDeltaPatch patch)
    {
        var next = CloneSavedWorld(source);
        ApplyHeader(next, patch.Header);

        var tiles = GroupTiles(next.Tiles);
        foreach (var page in patch.TilePages ?? [])
        {
            if (page.Items.Count == 0) tiles.Remove(page.Address);
            else tiles[page.Address] = page.Items.ToList();
        }
        next.Tiles = FlattenTiles(tiles);

        var pieces = GroupPieces(next.Pieces);
        foreach (var page in patch.PiecePages ?? [])
        {
            if (page.Items.Count == 0) pieces.Remove(page.Address);
            else pieces[page.Address] = page.Items.ToList();
        }
        next.Pieces = FlattenPieces(pieces);

        if (patch.NpcBoundaryExchanges is not null)
            next.NpcBoundaryExchanges = patch.NpcBoundaryExchanges.ToList();

        next.Revision = patch.ToRevision;
        return next;
    }

    static SavedWorld HeaderOnly(SavedWorld source) => new()
    {
        Revision = source.Revision,
        WorldId = source.WorldId,
        WorldName = source.WorldName,
        Reset = source.Reset,
        OperatingMode = source.OperatingMode,
        Role = source.Role,
        Layer = source.Layer,
        GridStyle = source.GridStyle,
        DistanceUnit = source.DistanceUnit,
        GridDiameter = source.GridDiameter,
        GridDistance = source.GridDistance,
        GridCalibrationZoom = source.GridCalibrationZoom,
        CubeX = source.CubeX,
        CubeY = source.CubeY,
        CubeZ = source.CubeZ,
        CubeRole = source.CubeRole,
        PlaneIndex = source.PlaneIndex,
        TierIndex = source.TierIndex,
        LayerOffset = source.LayerOffset,
        WorldBuilderQuickTileIds = source.WorldBuilderQuickTileIds.ToList(),
        Pieces = [],
        Tiles = [],
        NpcBoundaryExchanges = []
    };

    static void ApplyHeader(SavedWorld target, SavedWorld header)
    {
        target.Revision = header.Revision;
        target.WorldId = header.WorldId;
        target.WorldName = header.WorldName;
        target.Reset = header.Reset;
        target.OperatingMode = header.OperatingMode;
        target.Role = header.Role;
        target.Layer = header.Layer;
        target.GridStyle = header.GridStyle;
        target.DistanceUnit = header.DistanceUnit;
        target.GridDiameter = header.GridDiameter;
        target.GridDistance = header.GridDistance;
        target.GridCalibrationZoom = header.GridCalibrationZoom;
        target.CubeX = header.CubeX;
        target.CubeY = header.CubeY;
        target.CubeZ = header.CubeZ;
        target.CubeRole = header.CubeRole;
        target.PlaneIndex = header.PlaneIndex;
        target.TierIndex = header.TierIndex;
        target.LayerOffset = header.LayerOffset;
        target.WorldBuilderQuickTileIds = header.WorldBuilderQuickTileIds.ToList();
    }

    static Dictionary<WorldDeltaAddress, List<TileItem>> GroupTiles(IEnumerable<TileItem>? items) =>
        (items ?? []).GroupBy(item => new WorldDeltaAddress(item.CubeX, item.CubeY, item.CubeZ, item.PlaneIndex, item.TierIndex, item.LayerOffset))
            .ToDictionary(group => group.Key, group => group.ToList());

    static Dictionary<WorldDeltaAddress, List<PieceItem>> GroupPieces(IEnumerable<PieceItem>? items) =>
        (items ?? []).GroupBy(item => new WorldDeltaAddress(item.CubeX, item.CubeY, item.CubeZ, item.PlaneIndex, item.TierIndex, item.LayerOffset))
            .ToDictionary(group => group.Key, group => group.ToList());

    static List<TileItem> FlattenTiles(Dictionary<WorldDeltaAddress, List<TileItem>> pages) =>
        pages.OrderBy(pair => pair.Key).SelectMany(pair => pair.Value).ToList();

    static List<PieceItem> FlattenPieces(Dictionary<WorldDeltaAddress, List<PieceItem>> pages) =>
        pages.OrderBy(pair => pair.Key).SelectMany(pair => pair.Value).ToList();
}

public sealed class WorldDeltaHead
{
    public string WorldId { get; set; } = "";
    public long BaseRevision { get; set; }
    public long LatestRevision { get; set; }
    public string BaseCheckpointKey { get; set; } = "";
    public List<string> DeltaKeys { get; set; } = [];
    public DateTimeOffset UpdatedAtUtc { get; set; }
}

public sealed class WorldDeltaPatch
{
    public string Format { get; set; } = "";
    public int Version { get; set; }
    public string WorldId { get; set; } = "";
    public long FromRevision { get; set; }
    public long ToRevision { get; set; }
    public DateTimeOffset CreatedAtUtc { get; set; }
    public SavedWorld Header { get; set; } = new();
    public List<WorldDeltaTilePage> TilePages { get; set; } = [];
    public List<WorldDeltaPiecePage> PiecePages { get; set; } = [];
    public List<NpcBoundaryExchange>? NpcBoundaryExchanges { get; set; }
}

public readonly record struct WorldDeltaAddress(int CubeX, int CubeY, int CubeZ, int PlaneIndex, int TierIndex, int LayerOffset) : IComparable<WorldDeltaAddress>
{
    public int CompareTo(WorldDeltaAddress other)
    {
        var value = CubeX.CompareTo(other.CubeX); if (value != 0) return value;
        value = CubeY.CompareTo(other.CubeY); if (value != 0) return value;
        value = CubeZ.CompareTo(other.CubeZ); if (value != 0) return value;
        value = PlaneIndex.CompareTo(other.PlaneIndex); if (value != 0) return value;
        value = TierIndex.CompareTo(other.TierIndex); if (value != 0) return value;
        return LayerOffset.CompareTo(other.LayerOffset);
    }
}

public sealed record WorldDeltaTilePage(WorldDeltaAddress Address, List<TileItem> Items);
public sealed record WorldDeltaPiecePage(WorldDeltaAddress Address, List<PieceItem> Items);
