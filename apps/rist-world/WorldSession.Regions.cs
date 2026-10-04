using System.Text.Json;
using System.Text.Json.Serialization;

namespace RistWorld;

public sealed partial class WorldSession
{
    readonly List<WorldRegion> _regions = [];
    string _activeRegionId = "";
    string _activeSpatialRegionId = "";
    string _activeLocalId = "";
    string _activeInstanceId = "";

    public const string EndemarRegionDisplayName = "Sumaria";
    public const string EndemarCityDisplayName = "The Great City of Atsumaritas";

    public IReadOnlyList<WorldRegion> Regions => _regions;
    public WorldRegion? ActiveRegion => _regions.FirstOrDefault(x => string.Equals(x.RegionId, _activeRegionId, StringComparison.Ordinal));
    public IReadOnlyList<WorldSpatialNode> ActiveSpatialNodes => ActiveRegion?.SpatialNodes ?? [];
    public WorldSpatialNode? ActiveSpatialRegion => ActiveSpatialNodes.FirstOrDefault(x =>
        string.Equals(x.NodeId, _activeSpatialRegionId, StringComparison.Ordinal)
        && string.Equals(x.Kind, "REGION", StringComparison.OrdinalIgnoreCase));
    public WorldSpatialNode? ActiveLocal => ActiveSpatialNodes.FirstOrDefault(x =>
        string.Equals(x.NodeId, _activeLocalId, StringComparison.Ordinal)
        && string.Equals(x.Kind, "LOCAL", StringComparison.OrdinalIgnoreCase));
    public WorldSpatialNode? ActiveInstance => ActiveSpatialNodes.FirstOrDefault(x =>
        string.Equals(x.NodeId, _activeInstanceId, StringComparison.Ordinal)
        && string.Equals(x.Kind, "INSTANCE", StringComparison.OrdinalIgnoreCase));
    public IReadOnlyList<WorldSpatialNode> SpatialRegions => ActiveSpatialNodes
        .Where(x => string.Equals(x.Kind, "REGION", StringComparison.OrdinalIgnoreCase))
        .OrderBy(x => x.Name, StringComparer.OrdinalIgnoreCase)
        .ToList();
    string ActiveLocalParentId => ActiveSpatialRegion?.NodeId ?? ActiveRegion?.RegionId ?? "";
    public IReadOnlyList<WorldSpatialNode> LocalsForActiveSpatialRegion => string.IsNullOrWhiteSpace(ActiveLocalParentId)
        ? []
        : ActiveSpatialNodes
            .Where(x => string.Equals(x.Kind, "LOCAL", StringComparison.OrdinalIgnoreCase)
                && string.Equals(x.ParentNodeId, ActiveLocalParentId, StringComparison.Ordinal))
            .OrderBy(x => x.Name, StringComparer.OrdinalIgnoreCase)
            .ToList();
    public IReadOnlyList<WorldSpatialNode> InstancesForActiveLocal => ActiveLocal is null
        ? []
        : ActiveSpatialNodes
            .Where(x => string.Equals(x.Kind, "INSTANCE", StringComparison.OrdinalIgnoreCase)
                && string.Equals(x.ParentNodeId, ActiveLocal.NodeId, StringComparison.Ordinal))
            .OrderBy(x => x.Name, StringComparer.OrdinalIgnoreCase)
            .ToList();
    public string RegionDirectoryKey => $"{WorldStoragePrefix}/regions/index.json";
    public string RegionLocalSaveKey => $"rist.regions.v1.{WorldId}";

    static bool UsesSpatialScopeGrid(WorldRegion region) =>
        string.Equals(region.CoordinateSpace, SpatialWorldCoordinateSpace, StringComparison.OrdinalIgnoreCase);
    static int RegionGridColumnsFor(WorldRegion region) =>
        UsesSpatialScopeGrid(region) ? SpatialScopeGridColumns : GridColumns;
    static int RegionGridRowsFor(WorldRegion region) =>
        UsesSpatialScopeGrid(region) ? SpatialScopeGridRows : GridRows;

    public async Task LoadRegionsAsync()
    {
        var requestedActiveRegionId = _activeRegionId;
        var requestedSpatialRegionId = _activeSpatialRegionId;
        var requestedLocalId = _activeLocalId;
        var requestedInstanceId = _activeInstanceId;
        _regions.Clear();
        _activeRegionId = "";
        _activeSpatialRegionId = "";
        _activeLocalId = "";
        _activeInstanceId = "";
        if (!HasActiveWorld) { Notify(); return; }

        WorldRegionCatalog? catalog = null;
        if (IsLoggedIn)
        {
            try
            {
                var authority = await GetClaimAuthorityClientAsync();
                var databaseRegions = authority is null ? null : await authority.GetRegionsAsync(WorldId);
                if (databaseRegions is not null)
                    catalog = new WorldRegionCatalog(WorldId, databaseRegions, DateTimeOffset.UtcNow);
            }
            catch { }

            if (catalog is null)
            {
                try { catalog = await auth.DownloadJsonAsync<WorldRegionCatalog>(RegionDirectoryKey); }
                catch { }
            }
        }

        if (catalog is null)
        {
            try
            {
                var local = await js.InvokeAsync<string?>("localStorage.getItem", RegionLocalSaveKey);
                if (!string.IsNullOrWhiteSpace(local)) catalog = JsonSerializer.Deserialize<WorldRegionCatalog>(local, MapReadOptions);
            }
            catch { }
        }

        if (catalog is not null && string.Equals(catalog.WorldId, WorldId, StringComparison.Ordinal))
        {
            _regions.AddRange((catalog.Regions ?? [])
                .Where(x => string.Equals(x.WorldId, WorldId, StringComparison.Ordinal) && !string.IsNullOrWhiteSpace(x.RegionId))
                .GroupBy(x => x.RegionId, StringComparer.Ordinal)
                .Select(g => g.OrderByDescending(x => x.UpdatedAtUtc).First())
                .OrderBy(x => x.Name, StringComparer.OrdinalIgnoreCase));
            _activeRegionId = !string.IsNullOrWhiteSpace(requestedActiveRegionId)
                && _regions.Any(x => string.Equals(x.RegionId, requestedActiveRegionId, StringComparison.Ordinal))
                ? requestedActiveRegionId
                : "";

            if (ActiveRegion is not null)
            {
                var nodes = ActiveRegion.SpatialNodes ?? [];
                _activeSpatialRegionId = nodes.Any(x =>
                    string.Equals(x.NodeId, requestedSpatialRegionId, StringComparison.Ordinal)
                    && string.Equals(x.Kind, "REGION", StringComparison.OrdinalIgnoreCase))
                    ? requestedSpatialRegionId
                    : "";
                var requestedLocalParentId = !string.IsNullOrWhiteSpace(_activeSpatialRegionId)
                    ? _activeSpatialRegionId
                    : _activeRegionId;
                _activeLocalId = nodes.Any(x =>
                    string.Equals(x.NodeId, requestedLocalId, StringComparison.Ordinal)
                    && string.Equals(x.Kind, "LOCAL", StringComparison.OrdinalIgnoreCase)
                    && string.Equals(x.ParentNodeId, requestedLocalParentId, StringComparison.Ordinal))
                    ? requestedLocalId
                    : "";
                _activeInstanceId = nodes.Any(x =>
                    string.Equals(x.NodeId, requestedInstanceId, StringComparison.Ordinal)
                    && string.Equals(x.Kind, "INSTANCE", StringComparison.OrdinalIgnoreCase)
                    && string.Equals(x.ParentNodeId, _activeLocalId, StringComparison.Ordinal))
                    ? requestedInstanceId
                    : "";
            }
        }

        Notify();
    }

    public void SetActiveRegion(string regionId)
    {
        if (string.IsNullOrWhiteSpace(regionId))
        {
            _activeRegionId = "";
            ClearSpatialSelection();
            Notify();
            return;
        }
        if (_regions.Any(x => string.Equals(x.RegionId, regionId, StringComparison.Ordinal)))
        {
            if (!string.Equals(_activeRegionId, regionId, StringComparison.Ordinal))
                ClearSpatialSelection();
            _activeRegionId = regionId;
            Notify();
        }
    }

    public void SetActiveSpatialRegion(string nodeId)
    {
        var node = ActiveSpatialNodes.FirstOrDefault(x =>
            string.Equals(x.NodeId, nodeId, StringComparison.Ordinal)
            && string.Equals(x.Kind, "REGION", StringComparison.OrdinalIgnoreCase));
        if (node is null) return;
        var changed = !string.Equals(_activeSpatialRegionId, node.NodeId, StringComparison.Ordinal);
        _activeSpatialRegionId = node.NodeId;
        if (changed)
        {
            _activeLocalId = "";
            _activeInstanceId = "";
        }
        Notify();
    }

    public void SetActiveLocal(string nodeId)
    {
        var parentId = ActiveLocalParentId;
        if (string.IsNullOrWhiteSpace(parentId)) return;
        var node = ActiveSpatialNodes.FirstOrDefault(x =>
            string.Equals(x.NodeId, nodeId, StringComparison.Ordinal)
            && string.Equals(x.Kind, "LOCAL", StringComparison.OrdinalIgnoreCase)
            && string.Equals(x.ParentNodeId, parentId, StringComparison.Ordinal));
        if (node is null) return;
        var changed = !string.Equals(_activeLocalId, node.NodeId, StringComparison.Ordinal);
        _activeLocalId = node.NodeId;
        if (changed) _activeInstanceId = "";
        Notify();
    }

    public void SetActiveInstance(string nodeId)
    {
        if (ActiveLocal is null) return;
        var node = ActiveSpatialNodes.FirstOrDefault(x =>
            string.Equals(x.NodeId, nodeId, StringComparison.Ordinal)
            && string.Equals(x.Kind, "INSTANCE", StringComparison.OrdinalIgnoreCase)
            && string.Equals(x.ParentNodeId, ActiveLocal.NodeId, StringComparison.Ordinal));
        if (node is null) return;
        _activeInstanceId = node.NodeId;
        Notify();
    }

    public async Task<EndemarHierarchySetupResult> PrepareEndemarThroughCityAsync()
    {
        if (!HasTrustedWorldBuilderAuthority)
            throw new UnauthorizedAccessException("World Builder authority is required to prepare Endemar.");
        if (!HasActiveWorld)
            throw new InvalidOperationException("Choose Shaelvien before preparing Endemar.");

        // Reuse the old persisted Region. Never synthesize a replacement Sumaria:
        // the point of this setup is to continue working in the existing Region.
        var region = _regions.FirstOrDefault(item =>
            string.Equals(item.Name, EndemarRegionDisplayName, StringComparison.OrdinalIgnoreCase)
            && string.IsNullOrWhiteSpace(item.ParcelId))
            ?? _regions.FirstOrDefault(item =>
                string.Equals(item.Name, EndemarRegionDisplayName, StringComparison.OrdinalIgnoreCase));

        if (region is null)
            throw new InvalidOperationException(
                $"Existing Endemar Region '{EndemarRegionDisplayName}' was not found. No replacement Region was created.");

        _activeRegionId = region.RegionId;
        _activeSpatialRegionId = "";
        _activeLocalId = "";
        _activeInstanceId = "";

        var nodes = (region.SpatialNodes ?? []).ToList();
        var city = nodes.FirstOrDefault(node =>
            string.Equals(node.Kind, "LOCAL", StringComparison.OrdinalIgnoreCase)
            && IsAtsumaritasName(node.Name));

        var createdCityMetadata = false;
        if (city is null)
        {
            // This is hierarchy metadata only. RegionDefiner continues to render
            // the old Region-owned map/art; no city map or Region is recreated.
            var now = DateTimeOffset.UtcNow;
            city = new WorldSpatialNode(
                NodeId: NewSpatialNodeId("LOCAL", EndemarCityDisplayName),
                Kind: "LOCAL",
                Name: EndemarCityDisplayName,
                ParentNodeId: region.RegionId,
                CreatedAtUtc: now,
                UpdatedAtUtc: now,
                GridShape: "",
                GridColumns: 0,
                GridRows: 0,
                SelectedCells: null);
            nodes.Add(city);

            var index = _regions.FindIndex(item => string.Equals(item.RegionId, region.RegionId, StringComparison.Ordinal));
            if (index < 0)
                throw new InvalidOperationException("The existing Sumaria Region record is unavailable.");

            region = region with { SpatialNodes = nodes, UpdatedAtUtc = now };
            _regions[index] = region;
            createdCityMetadata = true;
            await SaveRegionsAsync();
        }

        // If the old city metadata already lived beneath a legacy nested REGION
        // node, preserve that lineage instead of rewriting it.
        var legacyParentRegion = nodes.FirstOrDefault(node =>
            string.Equals(node.Kind, "REGION", StringComparison.OrdinalIgnoreCase)
            && string.Equals(node.NodeId, city.ParentNodeId, StringComparison.Ordinal));
        _activeSpatialRegionId = legacyParentRegion?.NodeId ?? "";
        _activeLocalId = city.NodeId;
        _activeInstanceId = "";

        Notify();
        return new EndemarHierarchySetupResult(region, city, createdCityMetadata);
    }

    static bool IsAtsumaritasName(string? name)
    {
        var value = (name ?? "").Trim();
        return string.Equals(value, EndemarCityDisplayName, StringComparison.OrdinalIgnoreCase)
            || string.Equals(value, "Great City of Atsumaritas", StringComparison.OrdinalIgnoreCase)
            || string.Equals(value, "Atsumaritas", StringComparison.OrdinalIgnoreCase);
    }

    public async Task<WorldSpatialNode> CreateSpatialNodeAsync(
        string kind,
        string name,
        bool inspectionEdit = false,
        string inspectionReason = "",
        IEnumerable<int>? selectedCells = null,
        string gridShape = "hex",
        int gridColumns = 30,
        int gridRows = 30)
    {
        var authorityRegion = ActiveRegion
            ?? throw new InvalidOperationException("Select a Shaelvien world before creating a spatial depth.");
        if (!CanEditRegion(authorityRegion) && !(inspectionEdit && TrustedPlatformDeveloper))
            throw new UnauthorizedAccessException("Edit authority is required to create this spatial depth.");

        kind = (kind ?? "").Trim().ToUpperInvariant();
        if (kind is not ("REGION" or "LOCAL" or "INSTANCE"))
            throw new InvalidOperationException("Spatial depth must be Region, Local, or Instance.");

        name = (name ?? "").Trim();
        if (name.Length == 0) throw new InvalidOperationException($"Enter a {kind.ToLowerInvariant()} name.");
        if (name.Length > 80) throw new InvalidOperationException("Spatial names must be 80 characters or fewer.");

        gridShape = string.Equals(gridShape, "square", StringComparison.OrdinalIgnoreCase) ? "square" : "hex";
        gridColumns = Math.Clamp(gridColumns, 1, 64);
        gridRows = Math.Clamp(gridRows, 1, 64);
        var spatialCells = (selectedCells ?? [])
            .Where(cell => cell >= 0 && cell < gridColumns * gridRows)
            .Distinct()
            .Order()
            .ToList();
        if (kind == "REGION" && selectedCells is not null && spatialCells.Count == 0)
            throw new InvalidOperationException("Select at least one map cell for the Region.");

        string parentNodeId = kind switch
        {
            "REGION" => authorityRegion.RegionId,
            "LOCAL" when ActiveSpatialRegion is not null => ActiveSpatialRegion.NodeId,
            "LOCAL" => authorityRegion.RegionId,
            "INSTANCE" when ActiveLocal is not null => ActiveLocal.NodeId,
            "INSTANCE" => throw new InvalidOperationException("Select a Local before creating an Instance."),
            _ => authorityRegion.RegionId
        };

        var now = DateTimeOffset.UtcNow;
        var node = new WorldSpatialNode(
            NodeId: NewSpatialNodeId(kind, name),
            Kind: kind,
            Name: name,
            ParentNodeId: parentNodeId,
            CreatedAtUtc: now,
            UpdatedAtUtc: now,
            GridShape: kind == "REGION" ? gridShape : "",
            GridColumns: kind == "REGION" ? gridColumns : 0,
            GridRows: kind == "REGION" ? gridRows : 0,
            SelectedCells: kind == "REGION" ? spatialCells : null);

        var nodes = (authorityRegion.SpatialNodes ?? []).ToList();
        nodes.Add(node);
        var index = _regions.FindIndex(x => string.Equals(x.RegionId, authorityRegion.RegionId, StringComparison.Ordinal));
        if (index < 0) throw new InvalidOperationException("The active Shaelvien world record is unavailable.");
        _regions[index] = authorityRegion with { SpatialNodes = nodes, UpdatedAtUtc = now };

        switch (kind)
        {
            case "REGION":
                _activeSpatialRegionId = node.NodeId;
                _activeLocalId = "";
                _activeInstanceId = "";
                break;
            case "LOCAL":
                _activeLocalId = node.NodeId;
                _activeInstanceId = "";
                break;
            case "INSTANCE":
                _activeInstanceId = node.NodeId;
                break;
        }

        await SaveRegionsAsync(inspectionEdit, inspectionReason);
        Notify();
        return node;
    }

    void ClearSpatialSelection()
    {
        _activeSpatialRegionId = "";
        _activeLocalId = "";
        _activeInstanceId = "";
    }

    static string NewSpatialNodeId(string kind, string name)
    {
        var segment = new string(name.ToLowerInvariant()
            .Select(ch => char.IsLetterOrDigit(ch) ? ch : '-')
            .ToArray()).Trim('-');
        while (segment.Contains("--", StringComparison.Ordinal))
            segment = segment.Replace("--", "-", StringComparison.Ordinal);
        if (segment.Length == 0) segment = kind.ToLowerInvariant();
        if (segment.Length > 32) segment = segment[..32].Trim('-');
        return $"{kind.ToLowerInvariant()}-{segment}-{Guid.NewGuid():N}";
    }

    public async Task<WorldRegion> CreateRegionAsync(string name, IEnumerable<int> selectedCells, int tierIndex = 0, IEnumerable<int>? sourceLayerOffsets = null, string gridShape = "square")
    {
        if (!HasTrustedWorldBuilderAuthority) throw new UnauthorizedAccessException("World Builder authority is required to define regions.");
        if (!HasActiveWorld) throw new InvalidOperationException("Choose a world before defining a region.");
        name = NormalizeRegionName(name);
        var maxTierIndex = IsGeonaphWorld
            ? Math.Max(0, (MmoParcelMaxHeight - 1) / LayersPerTier)
            : 2;
        tierIndex = Math.Clamp(tierIndex, 0, maxTierIndex);
        gridShape = string.Equals(gridShape, "hex", StringComparison.OrdinalIgnoreCase) ? "hex" : "square";
        var sourceLayers = sourceLayerOffsets is null
            ? Enumerable.Range(0, LayersPerTier).ToList()
            : sourceLayerOffsets.Where(x => x >= 0 && x < LayersPerTier).Distinct().Order().ToList();
        var sourceLayerSet = sourceLayers.ToHashSet();
        var cells = selectedCells
            .Where(x => x >= 0 && x < SpatialScopeGridColumns * SpatialScopeGridRows)
            .Distinct()
            .Order()
            .ToList();
        if (cells.Count == 0) throw new InvalidOperationException("Select at least one world tile for the region.");

        var columns = cells.Select(x => x % SpatialScopeGridColumns).ToList();
        var rows = cells.Select(x => x / SpatialScopeGridColumns).ToList();
        var minColumn = columns.Min();
        var maxColumn = columns.Max();
        var minRow = rows.Min();
        var maxRow = rows.Max();
        // A region is authority/view metadata over the canonical world map.
        // It never stores a cropped or transformed copy of the map.
        var now = DateTimeOffset.UtcNow;
        var region = new WorldRegion(
            RegionId: NewRegionId(name),
            WorldId: WorldId,
            Name: name,
            MinColumn: minColumn,
            MinRow: minRow,
            MaxColumn: maxColumn,
            MaxRow: maxRow,
            SelectedCells: cells,
            SourceTiles: [],
            OverlayTiles: [],
            CreatedAtUtc: now,
            UpdatedAtUtc: now,
            TierIndex: tierIndex,
            SourceLayerOffsets: sourceLayers,
            GridShape: gridShape,
            OwnerUserId: auth.Profile?.UserId?.Trim() ?? "",
            ParentNodeId: $"world:{WorldId}",
            CoordinateSpace: SpatialWorldCoordinateSpace,
            CanonicalMinX: minColumn / (double)SpatialScopeGridColumns,
            CanonicalMinY: minRow / (double)SpatialScopeGridRows,
            CanonicalMaxX: (maxColumn + 1) / (double)SpatialScopeGridColumns,
            CanonicalMaxY: (maxRow + 1) / (double)SpatialScopeGridRows,
            CanonicalZMin: (tierIndex * LayersPerTier) + (sourceLayers.Count > 0 ? sourceLayers.Min() : 0),
            CanonicalZMax: (tierIndex * LayersPerTier) + (sourceLayers.Count > 0 ? sourceLayers.Max() + 1 : LayersPerTier));

        _regions.Add(region);
        _activeRegionId = region.RegionId;
        await SaveRegionsAsync();
        return region;
    }

    public async Task<bool> AddRegionOverlayTileAsync(string regionId, AtlasTile asset, double x, double y, int footprint)
    {
        var index = _regions.FindIndex(r => string.Equals(r.RegionId, regionId, StringComparison.Ordinal));
        if (index < 0) return false;
        var region = _regions[index];
        if (!CanEditRegion(region)) return false;
        footprint = Math.Clamp(footprint, 1, Math.Max(1, Math.Min(region.Width, region.Height)));
        x = Math.Clamp(x, 0, 1);
        y = Math.Clamp(y, 0, 1);

        var localColumn = Math.Clamp((int)Math.Floor(x * region.Width), 0, region.Width - 1);
        var localRow = Math.Clamp((int)Math.Floor(y * region.Height), 0, region.Height - 1);
        var originalColumn = region.MinColumn + localColumn;
        var originalRow = region.MinRow + localRow;
        var selected = region.SelectedCells.ToHashSet();
        var regionColumns = RegionGridColumnsFor(region);
        for (var row = originalRow; row < originalRow + footprint; row++)
        for (var column = originalColumn; column < originalColumn + footprint; column++)
        {
            if (column > region.MaxColumn || row > region.MaxRow || !selected.Contains(row * regionColumns + column)) return false;
        }

        var width = footprint / (double)region.Width;
        var height = footprint / (double)region.Height;
        x = Math.Clamp(localColumn / (double)region.Width, 0, Math.Max(0, 1 - width));
        y = Math.Clamp(localRow / (double)region.Height, 0, Math.Max(0, 1 - height));
        var overlays = region.OverlayTiles.ToList();
        overlays.Add(new RegionOverlayTile(
            Id: Guid.NewGuid().ToString("N"),
            AssetId: asset.Id,
            Name: asset.Name,
            Image: asset.Image,
            X: x,
            Y: y,
            Footprint: footprint,
            SourceWidth: asset.SourceWidth,
            SourceHeight: asset.SourceHeight,
            CropX: asset.CropX,
            CropY: asset.CropY,
            CropWidth: asset.CropWidth,
            CropHeight: asset.CropHeight));
        region = region with { OverlayTiles = overlays, UpdatedAtUtc = DateTimeOffset.UtcNow };
        _regions[index] = region;
        _activeRegionId = region.RegionId;
        await SaveRegionsAsync();
        return true;
    }

    public async Task RemoveRegionOverlayTileAsync(string regionId, string overlayId)
    {
        var index = _regions.FindIndex(r => string.Equals(r.RegionId, regionId, StringComparison.Ordinal));
        if (index < 0) return;
        var region = _regions[index];
        if (!CanEditRegion(region)) return;
        var overlays = region.OverlayTiles.Where(x => !string.Equals(x.Id, overlayId, StringComparison.Ordinal)).ToList();
        if (overlays.Count == region.OverlayTiles.Count) return;
        _regions[index] = region with { OverlayTiles = overlays, UpdatedAtUtc = DateTimeOffset.UtcNow };
        await SaveRegionsAsync();
    }

    public async Task SaveRegionsAsync(
        bool inspectionEdit = false,
        string inspectionReason = "")
    {
        if (!HasActiveWorld) return;
        var editableRegions = inspectionEdit && TrustedPlatformDeveloper
            ? _regions.Where(region =>
                ActiveRegion is not null
                && string.Equals(region.RegionId, ActiveRegion.RegionId, StringComparison.Ordinal)).ToList()
            : HasTrustedWorldBuilderAuthority
                ? _regions.ToList()
                : _regions.Where(CanEditRegion).ToList();
        if (editableRegions.Count == 0)
            throw new UnauthorizedAccessException("Region edit authority is required to save regions.");

        var catalog = new WorldRegionCatalog(WorldId, _regions.ToList(), DateTimeOffset.UtcNow);
        var json = JsonSerializer.Serialize(catalog, MapWriteOptions);
        await js.InvokeVoidAsync("localStorage.setItem", RegionLocalSaveKey, json);
        if (IsLoggedIn)
        {
            var authority = await GetClaimAuthorityClientAsync();
            if (authority is null)
                throw new InvalidOperationException("Region database authority is unavailable.");

            foreach (var region in editableRegions)
                await authority.SaveRegionAsync(
                    WorldId,
                    region,
                    inspectionEdit,
                    inspectionReason);

            // Only a world GM/owner writes the complete recovery catalog. A
            // claimant can mutate only the database-backed region they own.
            if (HasTrustedWorldBuilderAuthority)
            {
                await EnsureWorldRelationshipAsync();
                await auth.UploadTextAsync(RegionDirectoryKey, json, "application/json");
            }
        }
        Notify();
    }

    public bool CanEditRegion(WorldRegion? region)
    {
        if (region is null) return false;
        if (HasTrustedWorldBuilderAuthority) return true;

        var userId = auth.Profile?.UserId?.Trim() ?? "";
        if (userId.Length > 0 && string.Equals(region.OwnerUserId, userId, StringComparison.Ordinal))
            return true;

        if (string.IsNullOrWhiteSpace(region.ParcelId))
            return false;

        var parcel = _mmoParcels.FirstOrDefault(item =>
            string.Equals(item.ParcelId, region.ParcelId, StringComparison.Ordinal));
        return CanEditMmoParcel(parcel);
    }

    static string NormalizeRegionName(string? name)
    {
        var value = (name ?? "").Trim();
        if (value.Length == 0) throw new InvalidOperationException("Enter a Region Name.");
        if (value.Length > 80) throw new InvalidOperationException("Region Name must be 80 characters or fewer.");
        return value;
    }

    static string NewRegionId(string name)
    {
        var segment = AssetPathSegment(name);
        if (segment.Length > 36) segment = segment[..36].TrimEnd('-');
        return $"region-{segment}-{Guid.NewGuid():N}";
    }

    static bool TileTouchesSelectedWorldCells(TileItem tile, HashSet<int> selected)
    {
        var column = Math.Clamp((int)Math.Floor(tile.X * SpatialScopeGridColumns), 0, SpatialScopeGridColumns - 1);
        var row = Math.Clamp((int)Math.Floor(tile.Y * SpatialScopeGridRows), 0, SpatialScopeGridRows - 1);
        var footprint = Math.Clamp((int)Math.Round(1.0 / Math.Max(tile.PlacementZoom, 1.0 / SpatialScopeGridColumns)), 1, SpatialScopeGridColumns);
        for (var y = row; y < Math.Min(SpatialScopeGridRows, row + footprint); y++)
        for (var x = column; x < Math.Min(SpatialScopeGridColumns, column + footprint); x++)
            if (selected.Contains(y * SpatialScopeGridColumns + x)) return true;
        return false;
    }
}

public sealed record WorldRegionCatalog(string WorldId, List<WorldRegion> Regions, DateTimeOffset UpdatedAtUtc);

public sealed record WorldRegion(
    string RegionId,
    string WorldId,
    string Name,
    int MinColumn,
    int MinRow,
    int MaxColumn,
    int MaxRow,
    List<int> SelectedCells,
    List<TileItem> SourceTiles,
    List<RegionOverlayTile> OverlayTiles,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc,
    int TierIndex = 0,
    List<int>? SourceLayerOffsets = null,
    string GridShape = "square",
    string OwnerUserId = "",
    string ParcelId = "",
    int ParcelPixelWidth = 0,
    int ParcelPixelHeight = 0,
    int MaxHeight = 0,
    string ParentNodeId = "",
    string CoordinateSpace = "world-normalized-v1",
    double CanonicalMinX = 0,
    double CanonicalMinY = 0,
    double CanonicalMaxX = 0,
    double CanonicalMaxY = 0,
    int CanonicalZMin = 0,
    int CanonicalZMax = 0,
    string Description = "",
    List<WorldSpatialNode>? SpatialNodes = null)
{
    [JsonIgnore] public int Width => Math.Max(1, MaxColumn - MinColumn + 1);
    [JsonIgnore] public int Height => Math.Max(1, MaxRow - MinRow + 1);
}

public sealed record EndemarHierarchySetupResult(
    WorldRegion Region,
    WorldSpatialNode City,
    bool CityMetadataCreated);

public sealed record WorldSpatialNode(
    string NodeId,
    string Kind,
    string Name,
    string ParentNodeId,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc,
    string Description = "",
    string GridShape = "hex",
    int GridColumns = 30,
    int GridRows = 30,
    List<int>? SelectedCells = null);

public sealed record RegionOverlayTile(
    string Id,
    string AssetId,
    string Name,
    string Image,
    double X,
    double Y,
    int Footprint,
    int SourceWidth = 0,
    int SourceHeight = 0,
    int CropX = 0,
    int CropY = 0,
    int CropWidth = 0,
    int CropHeight = 0);
