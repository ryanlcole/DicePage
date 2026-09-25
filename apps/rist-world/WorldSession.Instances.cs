using System.Globalization;
using System.Text.Json;

namespace RistWorld;

public sealed partial class WorldSession
{
    public const string InstanceMapFormat = "RIST_INSTANCE_MAP_V1";

    readonly List<WorldInstance> _instances = [];
    string _activeInstanceId = "";

    public IReadOnlyList<WorldInstance> Instances => _instances;
    public IReadOnlyList<WorldInstance> DefinedInstances => _instances
        .Where(item => string.Equals(item.WorldId, WorldId, StringComparison.Ordinal))
        .OrderBy(item => item.Name, StringComparer.OrdinalIgnoreCase)
        .ThenBy(item => item.InstanceId, StringComparer.Ordinal)
        .ToList();

    public WorldInstance? ActiveInstance => _instances.FirstOrDefault(item =>
        string.Equals(item.InstanceId, _activeInstanceId, StringComparison.Ordinal));

    public string InstanceDirectoryKey => $"{WorldStoragePrefix}/instances/index.json";
    public string InstanceLocalSaveKey => $"rist.instances.v1.{WorldId}";
    public string InstanceMapStorageKey(string instanceId)
        => $"{WorldStoragePrefix}/instances/{AssetPathSegment(instanceId)}/map.json";
    public string InstanceMapLocalSaveKey(string instanceId)
        => $"rist.instance.map.v1.{WorldId}.{instanceId}";

    public async Task LoadInstancesAsync()
    {
        _instances.Clear();
        if (!HasActiveWorld)
        {
            _activeInstanceId = "";
            Notify();
            return;
        }

        WorldInstanceCatalog? catalog = null;
        if (IsLoggedIn)
        {
            try { catalog = await auth.DownloadJsonAsync<WorldInstanceCatalog>(InstanceDirectoryKey); }
            catch { }
        }

        if (catalog is null)
        {
            try
            {
                var raw = await js.InvokeAsync<string?>("localStorage.getItem", InstanceLocalSaveKey);
                if (!string.IsNullOrWhiteSpace(raw))
                    catalog = JsonSerializer.Deserialize<WorldInstanceCatalog>(raw, MapReadOptions);
            }
            catch { }
        }

        if (catalog is not null && string.Equals(catalog.WorldId, WorldId, StringComparison.Ordinal))
        {
            _instances.AddRange((catalog.Instances ?? [])
                .Where(item => item is not null
                    && !string.IsNullOrWhiteSpace(item.InstanceId)
                    && string.Equals(item.WorldId, WorldId, StringComparison.Ordinal))
                .GroupBy(item => item.InstanceId.Trim(), StringComparer.OrdinalIgnoreCase)
                .Select(group => group.OrderByDescending(item => item.UpdatedAtUtc).First()));
        }

        if (!string.IsNullOrWhiteSpace(_activeInstanceId)
            && !_instances.Any(item => string.Equals(item.InstanceId, _activeInstanceId, StringComparison.Ordinal)))
            _activeInstanceId = "";

        Notify();
    }

    public void SetActiveInstance(string instanceId)
    {
        instanceId = (instanceId ?? "").Trim();
        if (instanceId.Length == 0)
        {
            _activeInstanceId = "";
            Notify();
            return;
        }

        if (_instances.Any(item => string.Equals(item.InstanceId, instanceId, StringComparison.Ordinal)))
        {
            _activeInstanceId = instanceId;
            Notify();
        }
    }

    public bool CanEditInstance(WorldInstance instance)
    {
        if (instance is null || !string.Equals(instance.WorldId, WorldId, StringComparison.Ordinal))
            return false;
        var region = _regions.FirstOrDefault(item =>
            string.Equals(item.RegionId, instance.RegionId, StringComparison.Ordinal));
        return region is not null && IsRegionInActiveWorld(region) && CanEditRegion(region);
    }

    public async Task<IReadOnlyList<LocalInstanceAnchorReference>> LoadLocalInstanceReferencesAsync(string localId)
    {
        localId = (localId ?? "").Trim();
        var local = _locals.FirstOrDefault(item =>
            string.Equals(item.LocalId, localId, StringComparison.Ordinal)
            && string.Equals(item.WorldId, WorldId, StringComparison.Ordinal));
        if (local is null) return [];

        var rows = new List<LocalInstanceAnchorReference>
        {
            new(
                AssetId: local.AnchorObjectId,
                Name: string.IsNullOrWhiteSpace(local.AnchorName) ? "Local root" : local.AnchorName,
                Kind: string.IsNullOrWhiteSpace(local.AnchorKind) ? "asset" : local.AnchorKind,
                IsLocalRoot: true,
                X: 0,
                Y: 0,
                Tier: 1,
                Layer: 1,
                Recursive: local.HasRecursiveLocalScope)
        };

        var source = await LoadLocalMapAsync(local.LocalId);
        if (source?.State.ValueKind != JsonValueKind.Object
            || !source.State.TryGetProperty("userLayers", out var layers)
            || layers.ValueKind != JsonValueKind.Array)
            return rows;

        foreach (var layer in layers.EnumerateArray())
        {
            if (layer.ValueKind != JsonValueKind.Object) continue;
            var id = JsonString(layer, "id");
            if (id.Length == 0) continue;

            var name = JsonString(layer, "name");
            if (name.Length == 0) name = JsonString(layer, "text");
            if (name.Length == 0) name = "Unnamed Local asset";

            var kind = JsonString(layer, "kind");
            if (kind.Length == 0) kind = "asset";

            var recursive = layer.TryGetProperty("recursive", out var recursiveNode)
                && recursiveNode.ValueKind == JsonValueKind.Object
                && string.Equals(JsonString(recursiveNode, "format"), RecursiveScopeFormat, StringComparison.Ordinal)
                && string.Equals(JsonString(recursiveNode, "scopeKind"), "LOCAL", StringComparison.OrdinalIgnoreCase);

            var x = recursive ? JsonDouble(recursiveNode, "x", 0) : JsonDouble(layer, "x", 0);
            var y = recursive ? JsonDouble(recursiveNode, "y", 0) : JsonDouble(layer, "y", 0);
            var tier = recursive
                ? NormalizeScopeTier(JsonInt(recursiveNode, "tier", 1))
                : Math.Max(1, JsonInt(layer, "localTier", 0) + 1);
            var visualLayer = recursive
                ? NormalizeScopeLayer(JsonInt(recursiveNode, "layer", 1))
                : Math.Max(1, JsonInt(layer, "localLayer", 1));

            rows.Add(new(
                AssetId: id,
                Name: name,
                Kind: kind,
                IsLocalRoot: false,
                X: x,
                Y: y,
                Tier: tier,
                Layer: visualLayer,
                Recursive: recursive));
        }

        return rows
            .Where(item => !string.IsNullOrWhiteSpace(item.AssetId))
            .GroupBy(item => item.AssetId, StringComparer.Ordinal)
            .Select(group => group.First())
            .ToList();
    }

    public async Task<WorldInstance> CreateInstanceAsync(
        string name,
        string localId,
        string markerAssetId,
        string touchedAssetId,
        int gridColumns = 12,
        int gridRows = 12,
        string gridShape = "square")
    {
        if (!HasActiveWorld)
            throw new InvalidOperationException("Choose a world before defining an Instance.");

        localId = (localId ?? "").Trim();
        markerAssetId = (markerAssetId ?? "").Trim();
        touchedAssetId = (touchedAssetId ?? "").Trim();

        var local = _locals.FirstOrDefault(item =>
            string.Equals(item.LocalId, localId, StringComparison.Ordinal)
            && string.Equals(item.WorldId, WorldId, StringComparison.Ordinal))
            ?? throw new InvalidOperationException("Choose a Local before defining an Instance.");

        var region = _regions.FirstOrDefault(item =>
            string.Equals(item.RegionId, local.RegionId, StringComparison.Ordinal))
            ?? throw new InvalidOperationException("The Instance parent Region is unavailable.");
        if (!CanEditRegion(region))
            throw new UnauthorizedAccessException("Region edit authority is required to define an Instance.");

        name = NormalizeInstanceName(name);
        if (markerAssetId.Length == 0)
            throw new InvalidOperationException("Choose the named Local marker for this Instance.");
        if (touchedAssetId.Length == 0)
            throw new InvalidOperationException("Choose the Local asset touched by the marker.");
        if (string.Equals(markerAssetId, touchedAssetId, StringComparison.Ordinal))
            throw new InvalidOperationException("The marker and touched asset must be separate stable identities.");

        var references = await LoadLocalInstanceReferencesAsync(local.LocalId);
        var marker = references.FirstOrDefault(item =>
            !item.IsLocalRoot
            && IsInstanceMarkerKind(item.Kind)
            && string.Equals(item.AssetId, markerAssetId, StringComparison.Ordinal))
            ?? throw new InvalidOperationException("Choose a saved Local label, pin, or marker as the named Instance marker.");
        var touched = references.FirstOrDefault(item =>
            string.Equals(item.AssetId, touchedAssetId, StringComparison.Ordinal))
            ?? throw new InvalidOperationException("The touched asset is not part of the selected Local.");

        var duplicate = _instances.FirstOrDefault(item =>
            string.Equals(item.LocalId, local.LocalId, StringComparison.Ordinal)
            && string.Equals(item.MarkerAssetId, marker.AssetId, StringComparison.Ordinal)
            && string.Equals(item.TouchedAssetId, touched.AssetId, StringComparison.Ordinal));
        if (duplicate is not null)
        {
            _activeInstanceId = duplicate.InstanceId;
            Notify();
            return duplicate;
        }

        var now = DateTimeOffset.UtcNow;
        var instance = new WorldInstance(
            InstanceId: NewInstanceId(name),
            WorldId: WorldId,
            RegionId: local.RegionId,
            LocalId: local.LocalId,
            Name: name,
            MarkerAssetId: marker.AssetId,
            MarkerName: marker.Name,
            TouchedAssetId: touched.AssetId,
            TouchedAssetName: touched.Name,
            GridColumns: Math.Clamp(gridColumns, 2, 64),
            GridRows: Math.Clamp(gridRows, 2, 64),
            GridShape: NormalizeInstanceGridShape(gridShape),
            OwnerUserId: auth.Profile?.UserId?.Trim() ?? "",
            ParentNodeId: $"local:{local.LocalId}",
            RecursiveScopeFormat: RecursiveScopeFormat,
            ViewDegrees: 45,
            CreatedAtUtc: now,
            UpdatedAtUtc: now);

        _instances.Add(instance);
        _activeInstanceId = instance.InstanceId;
        await SaveInstancesAsync();

        var state = DefaultInstanceMapState(instance);
        await SaveInstanceMapAsync(instance.InstanceId, state);
        return instance;
    }

    public async Task SaveInstancesAsync()
    {
        if (!HasActiveWorld) return;
        var catalog = new WorldInstanceCatalog(
            WorldId,
            _instances
                .Where(item => string.Equals(item.WorldId, WorldId, StringComparison.Ordinal))
                .OrderBy(item => item.Name, StringComparer.OrdinalIgnoreCase)
                .ThenBy(item => item.InstanceId, StringComparer.Ordinal)
                .ToList(),
            DateTimeOffset.UtcNow);
        var json = JsonSerializer.Serialize(catalog, MapWriteOptions);
        await js.InvokeVoidAsync("localStorage.setItem", InstanceLocalSaveKey, json);
        if (IsLoggedIn)
            await auth.UploadTextAsync(InstanceDirectoryKey, json, "application/json");
        Notify();
    }

    public async Task<WorldInstanceMapSource?> LoadInstanceMapAsync(string instanceId)
    {
        instanceId = (instanceId ?? "").Trim();
        var instance = _instances.FirstOrDefault(item =>
            string.Equals(item.InstanceId, instanceId, StringComparison.Ordinal)
            && string.Equals(item.WorldId, WorldId, StringComparison.Ordinal));
        if (instance is null) return null;

        WorldInstanceMapSource? source = null;
        if (IsLoggedIn)
        {
            try { source = await auth.DownloadJsonAsync<WorldInstanceMapSource>(InstanceMapStorageKey(instanceId)); }
            catch { }
        }

        if (source is null)
        {
            try
            {
                var raw = await js.InvokeAsync<string?>("localStorage.getItem", InstanceMapLocalSaveKey(instanceId));
                if (!string.IsNullOrWhiteSpace(raw))
                    source = JsonSerializer.Deserialize<WorldInstanceMapSource>(raw, MapReadOptions);
            }
            catch { }
        }

        if (source is null
            || !string.Equals(source.WorldId, WorldId, StringComparison.Ordinal)
            || !string.Equals(source.LocalId, instance.LocalId, StringComparison.Ordinal)
            || !string.Equals(source.InstanceId, instance.InstanceId, StringComparison.Ordinal))
            return null;

        return source with { State = NormalizeInstanceMapState(instance, source.State) };
    }

    public async Task<WorldInstanceMapSource> SaveInstanceMapAsync(string instanceId, WorldInstanceMapState state)
    {
        instanceId = (instanceId ?? "").Trim();
        var instance = _instances.FirstOrDefault(item =>
            string.Equals(item.InstanceId, instanceId, StringComparison.Ordinal)
            && string.Equals(item.WorldId, WorldId, StringComparison.Ordinal))
            ?? throw new InvalidOperationException("Choose an Instance before saving Instance geometry.");

        if (!CanEditInstance(instance))
            throw new UnauthorizedAccessException("Region edit authority is required to save this Instance.");

        var normalized = NormalizeInstanceMapState(instance, state);
        var source = new WorldInstanceMapSource(
            WorldId,
            instance.RegionId,
            instance.LocalId,
            instance.InstanceId,
            normalized,
            DateTimeOffset.UtcNow);

        var json = JsonSerializer.Serialize(source, MapWriteOptions);
        await js.InvokeVoidAsync("localStorage.setItem", InstanceMapLocalSaveKey(instanceId), json);
        if (IsLoggedIn)
            await auth.UploadTextAsync(InstanceMapStorageKey(instanceId), json, "application/json");

        var index = _instances.FindIndex(item =>
            string.Equals(item.InstanceId, instance.InstanceId, StringComparison.Ordinal));
        if (index >= 0)
            _instances[index] = instance with { UpdatedAtUtc = source.UpdatedAtUtc };
        await SaveInstancesAsync();
        return source;
    }

    public async Task<int> DeleteInstanceAsync(WorldInstance instance)
    {
        if (instance is null || !CanEditInstance(instance)) return 0;
        var removed = _instances.RemoveAll(item =>
            string.Equals(item.InstanceId, instance.InstanceId, StringComparison.Ordinal)
            && string.Equals(item.WorldId, WorldId, StringComparison.Ordinal));
        if (removed == 0) return 0;

        if (string.Equals(_activeInstanceId, instance.InstanceId, StringComparison.Ordinal))
            _activeInstanceId = "";
        try { await js.InvokeVoidAsync("localStorage.removeItem", InstanceMapLocalSaveKey(instance.InstanceId)); }
        catch { }
        await SaveInstancesAsync();
        return removed;
    }

    public static WorldInstanceMapState DefaultInstanceMapState(WorldInstance instance)
        => new(
            Format: InstanceMapFormat,
            RecursiveScopeFormat: RecursiveScopeFormat,
            InstanceId: instance.InstanceId,
            LocalId: instance.LocalId,
            ViewDegrees: 45,
            GridColumns: instance.GridColumns,
            GridRows: instance.GridRows,
            GridShape: NormalizeInstanceGridShape(instance.GridShape),
            // Compatibility display fields only. New Instance Builder uses the
            // world's canonical physical/Measurefict measurement authority.
            MeasurementUnit: "steps",
            MeasurementPerStep: 1,
            Cells: [],
            Assets: []);

    public static WorldInstanceMapState NormalizeInstanceMapState(WorldInstance instance, WorldInstanceMapState? state)
    {
        state ??= DefaultInstanceMapState(instance);
        var columns = Math.Clamp(state.GridColumns > 0 ? state.GridColumns : instance.GridColumns, 2, 64);
        var rows = Math.Clamp(state.GridRows > 0 ? state.GridRows : instance.GridRows, 2, 64);

        var cells = (state.Cells ?? [])
            .Where(cell => cell.Column >= 0 && cell.Column < columns && cell.Row >= 0 && cell.Row < rows)
            .GroupBy(cell => (cell.Column, cell.Row))
            .Select(group => NormalizeInstanceCell(group.Last()))
            .Where(cell => !cell.IsDefault)
            .OrderBy(cell => cell.Row)
            .ThenBy(cell => cell.Column)
            .ToList();

        var assets = (state.Assets ?? [])
            .Where(asset => !string.IsNullOrWhiteSpace(asset.PlacementId))
            .Select(asset => asset.Normalize(instance.InstanceId, columns, rows))
            .GroupBy(asset => asset.PlacementId, StringComparer.Ordinal)
            .Select(group => group.Last())
            .OrderBy(asset => asset.Layer)
            .ThenBy(asset => asset.PlacementId, StringComparer.Ordinal)
            .ToList();

        return state with
        {
            Format = InstanceMapFormat,
            RecursiveScopeFormat = RecursiveScopeFormat,
            InstanceId = instance.InstanceId,
            LocalId = instance.LocalId,
            ViewDegrees = 45,
            GridColumns = columns,
            GridRows = rows,
            GridShape = NormalizeInstanceGridShape(state.GridShape),
            MeasurementUnit = NormalizeInstanceMeasurementUnit(state.MeasurementUnit),
            MeasurementPerStep = Math.Clamp(
                double.IsFinite(state.MeasurementPerStep) ? state.MeasurementPerStep : 1,
                0.001,
                100000),
            Cells = cells,
            Assets = assets
        };
    }

    public static WorldInstanceCellState NormalizeInstanceCell(WorldInstanceCellState cell)
        => cell with
        {
            ElevationSteps = Math.Clamp(cell.ElevationSteps, -1000, 1000),
            TerrainType = (cell.TerrainType ?? "").Trim(),
            MovementCost = Math.Clamp(
                double.IsFinite(cell.MovementCost) ? cell.MovementCost : 1,
                0,
                1000),
            Tags = (cell.Tags ?? "").Trim(),
            Notes = (cell.Notes ?? "").Trim()
        };

    public static int InstanceElevationParallaxBand(int elevationSteps) => elevationSteps / 10;

    public static string InstanceCellId(string instanceId, int column, int row)
        => $"instance:{AssetPathSegment(instanceId)}:cell:{column}:{row}";

    public static string InstanceSurfaceId(
        string instanceId,
        int column,
        int row,
        string face,
        int elevationStep)
    {
        var normalizedFace = NormalizeInstanceSurfaceFace(face);
        return string.Equals(normalizedFace, "top", StringComparison.Ordinal)
            ? $"{InstanceCellId(instanceId, column, row)}:surface:top"
            : $"{InstanceCellId(instanceId, column, row)}:surface:{normalizedFace}:step:{elevationStep}";
    }

    public static IReadOnlyList<WorldInstanceSurface> InstanceSurfacesForCell(
        WorldInstanceMapState state,
        int column,
        int row)
    {
        if (column < 0 || row < 0 || column >= state.GridColumns || row >= state.GridRows)
            return [];

        var cellElevation = InstanceCellAt(state, column, row).ElevationSteps;
        var result = new List<WorldInstanceSurface>
        {
            new(
                InstanceSurfaceId(state.InstanceId, column, row, "top", cellElevation),
                column,
                row,
                "top",
                cellElevation,
                true)
        };

        foreach (var neighbor in InstanceNeighborFaces(state.GridShape, column, row))
        {
            var neighborElevation = neighbor.Column < 0 || neighbor.Row < 0
                || neighbor.Column >= state.GridColumns || neighbor.Row >= state.GridRows
                ? 0
                : InstanceCellAt(state, neighbor.Column, neighbor.Row).ElevationSteps;

            if (cellElevation <= neighborElevation) continue;
            for (var step = neighborElevation + 1; step <= cellElevation; step++)
            {
                result.Add(new(
                    InstanceSurfaceId(state.InstanceId, column, row, neighbor.Face, step),
                    column,
                    row,
                    neighbor.Face,
                    step,
                    false));
            }
        }

        return result;
    }

    public static WorldInstanceCellState InstanceCellAt(WorldInstanceMapState state, int column, int row)
        => (state.Cells ?? []).LastOrDefault(cell => cell.Column == column && cell.Row == row)
            ?? new WorldInstanceCellState(column, row);

    public static string FormatInstanceElevation(WorldInstanceMapState state, int elevationSteps)
    {
        // Compatibility formatter for saved display preferences. Canonical
        // elevation remains ElevationSteps regardless of presentation unit.
        if (string.Equals(state.MeasurementUnit, "steps", StringComparison.OrdinalIgnoreCase))
            return $"{elevationSteps} step{(Math.Abs(elevationSteps) == 1 ? "" : "s")}";
        var value = elevationSteps * state.MeasurementPerStep;
        return $"{value.ToString("0.###", CultureInfo.InvariantCulture)} {state.MeasurementUnit}";
    }

    public double InstanceElevationUnitsPerStep => Math.Max(MinMeasurementPerCell, GridDistance);

    public string InstanceElevationStepSummary =>
        $"1 elevation step = {FormatMeasurementNumber(InstanceElevationUnitsPerStep)} {MeasurementUnitName(InstanceElevationUnitsPerStep)}";

    public string FormatInstanceElevationForCurrentMeasurement(int elevationSteps)
    {
        // Measurement and parallax are independent projections of the same
        // signed step truth. The world's configured measurement translates
        // each elevation step for display; the 10-step parallax band rule is
        // calculated separately by InstanceElevationParallaxBand().
        var value = elevationSteps * InstanceElevationUnitsPerStep;
        return $"{FormatMeasurementNumber(value)} {MeasurementUnitName(value)}";
    }

    public static bool IsInstanceMarkerKind(string? kind)
    {
        var value = (kind ?? "").Trim().ToLowerInvariant();
        return value is "label" or "pin" or "marker";
    }

    public static string NormalizeInstanceGridShape(string? value)
        => string.Equals(value, "hex", StringComparison.OrdinalIgnoreCase) ? "hex" : "square";

    public static string NormalizeInstanceMeasurementUnit(string? value)
    {
        var unit = (value ?? "ft").Trim().ToLowerInvariant();
        return unit switch
        {
            "m" or "meter" or "meters" => "m",
            "steps" or "step" => "steps",
            _ => "ft"
        };
    }

    static IEnumerable<InstanceNeighborFace> InstanceNeighborFaces(
        string gridShape,
        int column,
        int row)
    {
        if (string.Equals(NormalizeInstanceGridShape(gridShape), "hex", StringComparison.Ordinal))
        {
            var odd = (column & 1) == 1;
            yield return new(column - 1, row + (odd ? 0 : -1), "nw");
            yield return new(column, row - 1, "n");
            yield return new(column + 1, row + (odd ? 0 : -1), "ne");
            yield return new(column + 1, row + (odd ? 1 : 0), "se");
            yield return new(column, row + 1, "s");
            yield return new(column - 1, row + (odd ? 1 : 0), "sw");
            yield break;
        }

        yield return new(column, row - 1, "north");
        yield return new(column + 1, row, "east");
        yield return new(column, row + 1, "south");
        yield return new(column - 1, row, "west");
    }

    static string NormalizeInstanceSurfaceFace(string? value)
    {
        var face = (value ?? "top").Trim().ToLowerInvariant();
        return face switch
        {
            "north" or "east" or "south" or "west"
                or "n" or "ne" or "se" or "s" or "sw" or "nw" or "top" => face,
            _ => "top"
        };
    }

    static string JsonString(JsonElement value, string property)
        => value.TryGetProperty(property, out var node) && node.ValueKind == JsonValueKind.String
            ? node.GetString()?.Trim() ?? ""
            : "";

    static int JsonInt(JsonElement value, string property, int fallback)
        => value.TryGetProperty(property, out var node) && node.TryGetInt32(out var result)
            ? result
            : fallback;

    static double JsonDouble(JsonElement value, string property, double fallback)
        => value.TryGetProperty(property, out var node) && node.TryGetDouble(out var result)
            ? result
            : fallback;

    static string NormalizeInstanceName(string? name)
    {
        var value = (name ?? "").Trim();
        if (value.Length == 0) throw new InvalidOperationException("Enter an Instance name.");
        if (value.Length > 80) throw new InvalidOperationException("Instance name must be 80 characters or fewer.");
        return value;
    }

    static string NewInstanceId(string name)
    {
        var segment = AssetPathSegment(name);
        if (segment.Length > 36) segment = segment[..36].TrimEnd('-');
        return $"instance-{segment}-{Guid.NewGuid():N}";
    }

    sealed record InstanceNeighborFace(int Column, int Row, string Face);
}

public sealed record WorldInstanceCatalog(
    string WorldId,
    List<WorldInstance> Instances,
    DateTimeOffset UpdatedAtUtc);

public sealed record WorldInstance(
    string InstanceId,
    string WorldId,
    string RegionId,
    string LocalId,
    string Name,
    string MarkerAssetId,
    string MarkerName,
    string TouchedAssetId,
    string TouchedAssetName,
    int GridColumns,
    int GridRows,
    string GridShape,
    string OwnerUserId,
    string ParentNodeId,
    string RecursiveScopeFormat,
    int ViewDegrees,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc);

public sealed record LocalInstanceAnchorReference(
    string AssetId,
    string Name,
    string Kind,
    bool IsLocalRoot,
    double X,
    double Y,
    int Tier,
    int Layer,
    bool Recursive);

public sealed record WorldInstanceMapSource(
    string WorldId,
    string RegionId,
    string LocalId,
    string InstanceId,
    WorldInstanceMapState State,
    DateTimeOffset UpdatedAtUtc);

public sealed record WorldInstanceMapState(
    string Format,
    string RecursiveScopeFormat,
    string InstanceId,
    string LocalId,
    int ViewDegrees,
    int GridColumns,
    int GridRows,
    string GridShape,
    string MeasurementUnit,
    double MeasurementPerStep,
    List<WorldInstanceCellState> Cells,
    List<WorldInstanceAssetPlacement> Assets);

public sealed record WorldInstanceCellState(
    int Column,
    int Row,
    int ElevationSteps = 0,
    string TerrainType = "",
    double MovementCost = 1,
    bool BlocksMovement = false,
    bool BlocksSight = false,
    string Tags = "",
    string Notes = "")
{
    public bool IsDefault =>
        ElevationSteps == 0
        && string.IsNullOrWhiteSpace(TerrainType)
        && Math.Abs(MovementCost - 1) < 0.0000001
        && !BlocksMovement
        && !BlocksSight
        && string.IsNullOrWhiteSpace(Tags)
        && string.IsNullOrWhiteSpace(Notes);
}

public sealed record WorldInstanceAssetPlacement(
    string PlacementId,
    string SourceAssetId,
    string Name,
    string Kind,
    int Column,
    int Row,
    string SurfaceId,
    int Tier = 1,
    int Layer = 1,
    double Opacity = 1,
    bool Visible = true,
    bool Locked = false,
    string LinkedGroupId = "",
    string PermissionResourceId = "")
{
    public WorldInstanceAssetPlacement Normalize(string instanceId, int columns, int rows)
    {
        var placementId = (PlacementId ?? "").Trim();
        return this with
        {
            PlacementId = placementId,
            SourceAssetId = (SourceAssetId ?? "").Trim(),
            Name = (Name ?? "").Trim(),
            Kind = string.IsNullOrWhiteSpace(Kind) ? "asset" : Kind.Trim().ToLowerInvariant(),
            Column = Math.Clamp(Column, 0, Math.Max(0, columns - 1)),
            Row = Math.Clamp(Row, 0, Math.Max(0, rows - 1)),
            SurfaceId = (SurfaceId ?? "").Trim(),
            Tier = WorldSession.NormalizeScopeTier(Tier),
            Layer = WorldSession.NormalizeScopeLayer(Layer),
            Opacity = Math.Clamp(Opacity, 0, 1),
            LinkedGroupId = (LinkedGroupId ?? "").Trim(),
            PermissionResourceId = string.IsNullOrWhiteSpace(PermissionResourceId)
                ? WorldSession.RecursivePermissionResourceId(placementId)
                : WorldSession.RecursivePermissionResourceId(PermissionResourceId)
        };
    }
}

public sealed record WorldInstanceSurface(
    string SurfaceId,
    int Column,
    int Row,
    string Face,
    int ElevationStep,
    bool IsTop);
