using System.Text.Json;
using System.Text.Json.Serialization;

namespace RistWorld;

public sealed partial class WorldSession
{
    readonly List<WorldRegion> _regions = [];
    string _activeRegionId = "";

    public IReadOnlyList<WorldRegion> Regions => _regions;
    public WorldRegion? ActiveRegion => _regions.FirstOrDefault(x => string.Equals(x.RegionId, _activeRegionId, StringComparison.Ordinal));
    public string RegionDirectoryKey => $"{WorldStoragePrefix}/regions/index.json";
    public string RegionLocalSaveKey => $"rist.regions.v1.{WorldId}";

    public async Task LoadRegionsAsync()
    {
        var requestedActiveRegionId = _activeRegionId;
        _regions.Clear();
        _activeRegionId = "";
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
        }

        Notify();
    }

    public void SetActiveRegion(string regionId)
    {
        if (string.IsNullOrWhiteSpace(regionId))
        {
            _activeRegionId = "";
            Notify();
            return;
        }
        if (_regions.Any(x => string.Equals(x.RegionId, regionId, StringComparison.Ordinal)))
        {
            _activeRegionId = regionId;
            Notify();
        }
    }

    public async Task<WorldRegion> CreateRegionAsync(string name, IEnumerable<int> selectedCells, int tierIndex = 0, IEnumerable<int>? sourceLayerOffsets = null, string gridShape = "square")
    {
        if (!HasTrustedWorldBuilderAuthority) throw new UnauthorizedAccessException("World Builder authority is required to define regions.");
        if (!HasActiveWorld) throw new InvalidOperationException("Choose a world before defining a region.");
        name = NormalizeRegionName(name);
        tierIndex = Math.Clamp(tierIndex, 0, 2);
        gridShape = string.Equals(gridShape, "hex", StringComparison.OrdinalIgnoreCase) ? "hex" : "square";
        var sourceLayers = sourceLayerOffsets is null
            ? Enumerable.Range(0, LayersPerTier).ToList()
            : sourceLayerOffsets.Where(x => x >= 0 && x < LayersPerTier).Distinct().Order().ToList();
        var sourceLayerSet = sourceLayers.ToHashSet();
        var cells = selectedCells
            .Where(x => x >= 0 && x < GridColumns * GridRows)
            .Distinct()
            .Order()
            .ToList();
        if (cells.Count == 0) throw new InvalidOperationException("Select at least one world tile for the region.");

        var columns = cells.Select(x => x % GridColumns).ToList();
        var rows = cells.Select(x => x / GridColumns).ToList();
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
            OwnerUserId: auth.Profile?.UserId?.Trim() ?? "");

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
        for (var row = originalRow; row < originalRow + footprint; row++)
        for (var column = originalColumn; column < originalColumn + footprint; column++)
        {
            if (column > region.MaxColumn || row > region.MaxRow || !selected.Contains(row * GridColumns + column)) return false;
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

    public async Task<WorldRegion> SaveRegionLayerStateAsync(string regionId, JsonElement layerState)
    {
        var index = _regions.FindIndex(r => string.Equals(r.RegionId, regionId, StringComparison.Ordinal));
        if (index < 0) throw new InvalidOperationException("The selected region is not available.");
        var region = _regions[index];
        if (!CanEditRegion(region)) throw new UnauthorizedAccessException("Region edit authority is required.");
        if (layerState.ValueKind != JsonValueKind.Object) throw new InvalidOperationException("Region layer state must be an object.");

        if (layerState.TryGetProperty("worldId", out var stateWorldId))
        {
            var value = stateWorldId.GetString()?.Trim() ?? "";
            if (value.Length > 0 && !string.Equals(value, WorldId, StringComparison.Ordinal))
                throw new InvalidOperationException("Region layer state belongs to a different world.");
        }
        if (layerState.TryGetProperty("regionId", out var stateRegionId))
        {
            var value = stateRegionId.GetString()?.Trim() ?? "";
            if (value.Length > 0 && !string.Equals(value, region.RegionId, StringComparison.Ordinal))
                throw new InvalidOperationException("Region layer state belongs to a different region.");
        }

        region = region with
        {
            LayerState = layerState.Clone(),
            UpdatedAtUtc = DateTimeOffset.UtcNow
        };
        _regions[index] = region;
        _activeRegionId = region.RegionId;
        await SaveRegionsAsync();
        return region;
    }

    public async Task SaveRegionsAsync()
    {
        if (!HasActiveWorld) return;
        var editableRegions = HasTrustedWorldBuilderAuthority
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
                await authority.SaveRegionAsync(WorldId, region);

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
        var column = Math.Clamp((int)Math.Floor(tile.X * GridColumns), 0, GridColumns - 1);
        var row = Math.Clamp((int)Math.Floor(tile.Y * GridRows), 0, GridRows - 1);
        var footprint = Math.Clamp((int)Math.Round(1.0 / Math.Max(tile.PlacementZoom, 1.0 / 300.0)), 1, 300);
        for (var y = row; y < Math.Min(GridRows, row + footprint); y++)
        for (var x = column; x < Math.Min(GridColumns, column + footprint); x++)
            if (selected.Contains(y * GridColumns + x)) return true;
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
    JsonElement? LayerState = null)
{
    [JsonIgnore] public int Width => Math.Max(1, MaxColumn - MinColumn + 1);
    [JsonIgnore] public int Height => Math.Max(1, MaxRow - MinRow + 1);
}

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
