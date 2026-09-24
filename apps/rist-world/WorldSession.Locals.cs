using System.Text.Json;

namespace RistWorld;

public sealed partial class WorldSession
{
    readonly List<WorldLocal> _locals = [];
    string _activeLocalId = "";

    public IReadOnlyList<WorldLocal> Locals => _locals;
    public IReadOnlyList<WorldLocal> DefinedLocals => CanonicalLocals(_locals
        .Where(local => string.Equals(local.WorldId, WorldId, StringComparison.Ordinal)));
    public WorldLocal? ActiveLocal => _locals.FirstOrDefault(local =>
        string.Equals(local.LocalId, _activeLocalId, StringComparison.Ordinal));

    public string LocalDirectoryKey => $"{WorldStoragePrefix}/locals/index.json";
    public string LocalLocalSaveKey => $"rist.locals.v1.{WorldId}";
    public string LocalMapStorageKey(string localId) => $"{WorldStoragePrefix}/locals/{AssetPathSegment(localId)}/map.json";
    public string LocalMapLocalSaveKey(string localId) => $"rist.local.map.v1.{WorldId}.{localId}";

    public async Task LoadLocalsAsync()
    {
        _locals.Clear();
        if (!HasActiveWorld)
        {
            _activeLocalId = "";
            Notify();
            return;
        }

        WorldLocalCatalog? catalog = null;
        if (IsLoggedIn)
        {
            try { catalog = await auth.DownloadJsonAsync<WorldLocalCatalog>(LocalDirectoryKey); }
            catch { }
        }

        if (catalog is null)
        {
            try
            {
                var raw = await js.InvokeAsync<string?>("localStorage.getItem", LocalLocalSaveKey);
                if (!string.IsNullOrWhiteSpace(raw))
                    catalog = JsonSerializer.Deserialize<WorldLocalCatalog>(raw, MapReadOptions);
            }
            catch { }
        }

        if (catalog is not null && string.Equals(catalog.WorldId, WorldId, StringComparison.Ordinal))
        {
            _locals.AddRange(CanonicalLocals(catalog.Locals ?? []));
        }

        if (!string.IsNullOrWhiteSpace(_activeLocalId)
            && !_locals.Any(local => string.Equals(local.LocalId, _activeLocalId, StringComparison.Ordinal)))
            _activeLocalId = "";

        Notify();
    }

    public void SetActiveLocal(string localId)
    {
        localId = (localId ?? "").Trim();
        if (localId.Length == 0)
        {
            _activeLocalId = "";
            Notify();
            return;
        }

        if (_locals.Any(local => string.Equals(local.LocalId, localId, StringComparison.Ordinal)))
        {
            _activeLocalId = localId;
            Notify();
        }
    }

    public async Task<WorldLocal> CreateLocalAsync(
        string name,
        string regionId,
        string anchorObjectId,
        string anchorAssetId,
        string anchorName,
        string anchorKind,
        double x,
        double y,
        double width,
        double height,
        int tier,
        int layer,
        int regionLayer,
        int z100,
        double rotation,
        int regionTier = 0,
        int localTier = 0,
        int localLayer = 0,
        int instanceTier = 0,
        int instanceLayer = 0)
    {
        if (!HasActiveWorld)
            throw new InvalidOperationException("Choose a world before defining a Local.");

        var region = _regions.FirstOrDefault(item =>
            string.Equals(item.RegionId, (regionId ?? "").Trim(), StringComparison.Ordinal));
        if (region is null || !IsRegionInActiveWorld(region))
            throw new InvalidOperationException("Choose a Region before defining a Local.");
        if (!CanEditRegion(region))
            throw new UnauthorizedAccessException("Region edit authority is required to define a Local.");

        name = NormalizeLocalName(name);
        anchorObjectId = (anchorObjectId ?? "").Trim();
        if (anchorObjectId.Length == 0)
            throw new InvalidOperationException("Select a placed regional object for the Local.");

        var duplicate = CanonicalLocals(_locals).FirstOrDefault(local =>
            string.Equals(local.RegionId, region.RegionId, StringComparison.OrdinalIgnoreCase)
            && string.Equals(local.AnchorObjectId, anchorObjectId, StringComparison.OrdinalIgnoreCase));
        if (duplicate is not null)
        {
            _activeLocalId = duplicate.LocalId;
            return duplicate;
        }

        var now = DateTimeOffset.UtcNow;
        var local = new WorldLocal(
            LocalId: NewLocalId(name),
            WorldId: WorldId,
            RegionId: region.RegionId,
            Name: name,
            AnchorObjectId: anchorObjectId,
            AnchorAssetId: (anchorAssetId ?? "").Trim(),
            AnchorName: string.IsNullOrWhiteSpace(anchorName) ? name : anchorName.Trim(),
            AnchorKind: string.IsNullOrWhiteSpace(anchorKind) ? "image" : anchorKind.Trim().ToLowerInvariant(),
            X: Math.Clamp(x, 0, 1),
            Y: Math.Clamp(y, 0, 1),
            Width: Math.Clamp(width, 0.0001, 1),
            Height: Math.Clamp(height, 0.0001, 1),
            Tier: Math.Clamp(tier, 0, 2),
            Layer: Math.Clamp(layer, 0, 9),
            RegionLayer: Math.Clamp(regionLayer, 0, 9),
            Z100: Math.Max(0, z100),
            Rotation: rotation,
            OwnerUserId: auth.Profile?.UserId?.Trim() ?? "",
            ParentNodeId: $"region:{region.RegionId}",
            CoordinateSpace: "canonical-world-xy+hierarchical-depth-v1",
            CreatedAtUtc: now,
            UpdatedAtUtc: now,
            RegionTier: Math.Max(0, regionTier),
            LocalTier: Math.Max(0, localTier),
            LocalLayer: Math.Clamp(localLayer, 0, 9),
            InstanceTier: Math.Max(0, instanceTier),
            InstanceLayer: Math.Clamp(instanceLayer, 0, 9));

        _locals.Add(local);
        _activeLocalId = local.LocalId;
        await SaveLocalsAsync();
        return local;
    }

    public async Task<WorldLocalMapSource?> LoadLocalMapAsync(string localId)
    {
        localId = (localId ?? "").Trim();
        var local = _locals.FirstOrDefault(item =>
            string.Equals(item.LocalId, localId, StringComparison.Ordinal)
            && string.Equals(item.WorldId, WorldId, StringComparison.Ordinal));
        if (local is null) return null;

        WorldLocalMapSource? source = null;
        if (IsLoggedIn)
        {
            try { source = await auth.DownloadJsonAsync<WorldLocalMapSource>(LocalMapStorageKey(localId)); }
            catch { }
        }

        if (source is null)
        {
            try
            {
                var raw = await js.InvokeAsync<string?>("localStorage.getItem", LocalMapLocalSaveKey(localId));
                if (!string.IsNullOrWhiteSpace(raw))
                    source = JsonSerializer.Deserialize<WorldLocalMapSource>(raw, MapReadOptions);
            }
            catch { }
        }

        if (source is null
            || !string.Equals(source.WorldId, WorldId, StringComparison.Ordinal)
            || !string.Equals(source.RegionId, local.RegionId, StringComparison.Ordinal)
            || !string.Equals(source.LocalId, local.LocalId, StringComparison.Ordinal))
            return null;

        return source;
    }

    public async Task<WorldLocalMapSource> SaveLocalMapAsync(string localId, JsonElement state)
    {
        localId = (localId ?? "").Trim();
        var local = _locals.FirstOrDefault(item =>
            string.Equals(item.LocalId, localId, StringComparison.Ordinal)
            && string.Equals(item.WorldId, WorldId, StringComparison.Ordinal))
            ?? throw new InvalidOperationException("Choose a Local before saving Local content.");

        var region = _regions.FirstOrDefault(item =>
            string.Equals(item.RegionId, local.RegionId, StringComparison.Ordinal))
            ?? throw new InvalidOperationException("The Local parent Region is unavailable.");
        if (!CanEditRegion(region))
            throw new UnauthorizedAccessException("Region edit authority is required to save this Local.");

        var source = new WorldLocalMapSource(
            WorldId,
            local.RegionId,
            local.LocalId,
            local.AnchorObjectId,
            state.Clone(),
            DateTimeOffset.UtcNow);

        var json = JsonSerializer.Serialize(source, MapWriteOptions);
        await js.InvokeVoidAsync("localStorage.setItem", LocalMapLocalSaveKey(localId), json);
        if (IsLoggedIn)
            await auth.UploadTextAsync(LocalMapStorageKey(localId), json, "application/json");
        return source;
    }

    public async Task SaveLocalsAsync()
    {
        if (!HasActiveWorld) return;
        var canonical = CanonicalLocals(_locals);
        _locals.Clear();
        _locals.AddRange(canonical);
        var catalog = new WorldLocalCatalog(WorldId, _locals.ToList(), DateTimeOffset.UtcNow);
        var json = JsonSerializer.Serialize(catalog, MapWriteOptions);
        await js.InvokeVoidAsync("localStorage.setItem", LocalLocalSaveKey, json);

        if (IsLoggedIn)
            await auth.UploadTextAsync(LocalDirectoryKey, json, "application/json");

        Notify();
    }

    static List<WorldLocal> CanonicalLocals(IEnumerable<WorldLocal> locals)
    {
        // Local identity is the parent Region + the placed regional object used
        // as the Local anchor. Older builds could mint more than one LocalId for
        // the same anchor; collapse those aliases deterministically to the most
        // recently updated record while keeping unrelated Locals intact.
        return locals
            .Where(local => local is not null
                && !string.IsNullOrWhiteSpace(local.LocalId)
                && !string.IsNullOrWhiteSpace(local.WorldId))
            .GroupBy(local => local.LocalId.Trim(), StringComparer.OrdinalIgnoreCase)
            .Select(group => group.OrderByDescending(local => local.UpdatedAtUtc).First())
            .GroupBy(local =>
            {
                var regionId = (local.RegionId ?? "").Trim();
                var anchorId = (local.AnchorObjectId ?? "").Trim();
                return anchorId.Length == 0
                    ? $"LOCAL\u001f{local.LocalId.Trim()}"
                    : $"ANCHOR\u001f{regionId}\u001f{anchorId}";
            }, StringComparer.OrdinalIgnoreCase)
            .Select(group => group
                .OrderByDescending(local => local.UpdatedAtUtc)
                .ThenBy(local => local.LocalId, StringComparer.OrdinalIgnoreCase)
                .First())
            .OrderBy(local => local.Name, StringComparer.OrdinalIgnoreCase)
            .ThenBy(local => local.LocalId, StringComparer.OrdinalIgnoreCase)
            .ToList();
    }

    public async Task<int> DeleteLocalAsync(WorldLocal local)
    {
        if (!HasActiveWorld || local is null) return 0;

        var region = _regions.FirstOrDefault(item =>
            string.Equals(item.RegionId, local.RegionId, StringComparison.OrdinalIgnoreCase));
        if (region is null || !IsRegionInActiveWorld(region))
            throw new InvalidOperationException("The Local parent Region is unavailable.");
        if (!CanEditRegion(region))
            throw new UnauthorizedAccessException("Region edit authority is required to delete this Local.");

        var regionId = (local.RegionId ?? "").Trim();
        var anchorId = (local.AnchorObjectId ?? "").Trim();
        var removed = _locals
            .Where(item =>
                string.Equals(item.WorldId, WorldId, StringComparison.OrdinalIgnoreCase)
                && string.Equals(item.RegionId, regionId, StringComparison.OrdinalIgnoreCase)
                && (anchorId.Length > 0
                    ? string.Equals(item.AnchorObjectId, anchorId, StringComparison.OrdinalIgnoreCase)
                    : string.Equals(item.LocalId, local.LocalId, StringComparison.OrdinalIgnoreCase)))
            .ToList();

        if (removed.Count == 0) return 0;

        foreach (var item in removed)
        {
            _locals.Remove(item);
            try { await js.InvokeVoidAsync("localStorage.removeItem", LocalMapLocalSaveKey(item.LocalId)); }
            catch { }
        }

        if (removed.Any(item => string.Equals(item.LocalId, _activeLocalId, StringComparison.OrdinalIgnoreCase)))
            _activeLocalId = "";

        await SaveLocalsAsync();
        return removed.Count;
    }

    static string NormalizeLocalName(string? name)
    {
        var value = (name ?? "").Trim();
        if (value.Length == 0) throw new InvalidOperationException("Enter a Local Name.");
        if (value.Length > 80) throw new InvalidOperationException("Local Name must be 80 characters or fewer.");
        return value;
    }

    static string NewLocalId(string name)
    {
        var segment = AssetPathSegment(name);
        if (segment.Length > 36) segment = segment[..36].TrimEnd('-');
        return $"local-{segment}-{Guid.NewGuid():N}";
    }
}

public sealed record WorldLocalCatalog(string WorldId, List<WorldLocal> Locals, DateTimeOffset UpdatedAtUtc);

public sealed record WorldLocalMapSource(
    string WorldId,
    string RegionId,
    string LocalId,
    string AnchorObjectId,
    JsonElement State,
    DateTimeOffset UpdatedAtUtc);

public sealed record WorldLocal(
    string LocalId,
    string WorldId,
    string RegionId,
    string Name,
    string AnchorObjectId,
    string AnchorAssetId,
    string AnchorName,
    string AnchorKind,
    double X,
    double Y,
    double Width,
    double Height,
    int Tier,
    int Layer,
    int RegionLayer,
    int Z100,
    double Rotation,
    string OwnerUserId,
    string ParentNodeId,
    string CoordinateSpace,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc,
    string Description = "",
    int RegionTier = 0,
    int LocalTier = 0,
    int LocalLayer = 0,
    int InstanceTier = 0,
    int InstanceLayer = 0)
{
    // Tier/Layer remain the persisted legacy names for World tier/layer.
    public int WorldTier => Tier;
    public int WorldLayer => Layer;
    public RistHierarchicalAddress Address => new RistHierarchicalAddress(
        WorldTier,
        WorldLayer,
        RegionTier,
        RegionLayer,
        LocalTier,
        LocalLayer,
        InstanceTier,
        InstanceLayer).Normalized();
}
