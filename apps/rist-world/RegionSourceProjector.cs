using System.Text.Json;

namespace RistWorld;

// RegionDefiner now owns a recursive REGION authoring scope. The legacy
// worldLayer/regionLayer/z100 fields are retained only as a compatibility
// projection for the current prototype while RIST_RECURSIVE_SCOPE_V1 becomes
// the authoring authority.
public static class RegionSourceProjector
{
    const int Columns = 30;
    const int Rows = 30;
    const int LegacyWorldLayerMin = 0;
    const int LegacyWorldLayerMax = 9;
    const int LegacyRegionLayerMin = 1;
    const int LegacyRegionLayerMax = 9;

    public static JsonElement Project(
        string worldId, string regionId, string parentNodeId, int parentTier,
        IEnumerable<int> selectedCells, string gridShape,
        IEnumerable<int> sourceLayerOffsets, JsonElement parent)
    {
        var cells = CanonicalCells(selectedCells);
        var permitted = cells.ToHashSet();
        var layers = sourceLayerOffsets.Where(i => i >= 0 && i < 10).Distinct().ToHashSet();
        if (layers.Count == 0) layers = Enumerable.Range(0, 10).ToHashSet();
        var shape = gridShape == "hex" ? "hex" : "square";
        var frame = FrameFor(cells);

        var index = ArrayEntries(parent, "sourceTileIndex").Where(tile =>
            IntValue(tile, "tierIndex", 0) == parentTier
            && layers.Contains(IntValue(tile, "layerOffset", 0))
            && permitted.Contains(IntValue(tile, "cellIndex", -1))).ToArray();

        var tiles = ArrayEntries(parent, "tiles").Where(tile =>
            IntValue(tile, "tierIndex", 0) == parentTier
            && layers.Contains(IntValue(tile, "layerOffset", 0))
            && permitted.Contains(CellAt(NumberValue(tile, "x", 0), NumberValue(tile, "y", 0), shape))).ToArray();

        var sourceUserLayers = ArrayEntries(parent, "userLayers").Where(item =>
            string.IsNullOrWhiteSpace(StringValue(item, "regionId"))
            && IntValue(item, "tier", 0) == parentTier
            && layers.Contains(IntValue(item, "layer", 0))
            && permitted.Contains(CellAt(NumberValue(item, "x", 0), NumberValue(item, "y", 0), shape))).ToArray();

        var regionLayers = new List<JsonElement>();
        foreach (var raw in ArrayEntries(parent, "userLayers").Where(item =>
                     StringValue(item, "regionId") == regionId))
        {
            try { regionLayers.Add(NormalizeOverlay(worldId, regionId, parentNodeId, parentTier, cells, shape, raw)); }
            catch (Exception) { }
        }

        var images = ArrayEntries(parent, "tierImages");
        var bitmap = images.Length > parentTier && images[parentTier].ValueKind == JsonValueKind.String
            && !string.IsNullOrWhiteSpace(images[parentTier].GetString());

        return JsonSerializer.SerializeToElement(new
        {
            projection = "region-recursive-scope-v1",
            legacyProjection = "region-world-z-v2",
            recursiveScopeFormat = WorldSession.RecursiveScopeFormat,
            recursiveScope = new
            {
                kind = "REGION",
                scopeId = regionId,
                parentScopeId = worldId,
                parentAssetId = parentNodeId,
                viewDegrees = 15,
                origin = "claimed-region",
                coordinateFrame = new
                {
                    left = frame.Left,
                    top = frame.Top,
                    right = frame.Right,
                    bottom = frame.Bottom
                }
            },
            worldId,
            regionId,
            parentNodeId,
            parentTierIndex = parentTier,
            gridShape = shape,
            selectedCells = cells,
            sourceCells = cells.Select(i => new
            {
                id = $"{worldId}:{parentNodeId}:tier:{parentTier}:cell:{i}",
                cellIndex = i,
                column = i % Columns,
                row = i / Columns,
                tierIndex = parentTier
            }).ToArray(),
            sourceTileIndex = index,
            tiles,
            sourceUserLayers,
            userLayers = regionLayers,
            gridColumns = Columns,
            gridRows = Rows,
            sourcePixelWidth = IntValue(parent, "sourcePixelWidth", 2508),
            sourcePixelHeight = IntValue(parent, "sourcePixelHeight", 2508),
            sourceLayerOffsets = layers.Order().ToArray(),
            requiresRasterIndex = bitmap && index.Select(x => IntValue(x, "cellIndex", -1)).Distinct().Count() < cells.Length,
            sourceBitmapWasOmitted = bitmap,
            zModel = new
            {
                status = "legacy-compatibility-only",
                worldIntegerMin = 0,
                worldIntegerMax = 9,
                regionHundredthMin = 1,
                regionHundredthMax = 9,
                storage = "z100"
            }
        });
    }

    public static JsonElement MergeRegionLayers(
        string worldId, string regionId, string parentNodeId, int parentTier,
        IEnumerable<int> selectedCells, string gridShape, JsonElement parent, JsonElement incoming)
    {
        if (incoming.ValueKind != JsonValueKind.Array)
            throw new InvalidOperationException("Regional overlays must be an array.");

        var cells = CanonicalCells(selectedCells);
        var normalized = incoming.EnumerateArray()
            .Select(raw => NormalizeOverlay(worldId, regionId, parentNodeId, parentTier, cells, gridShape, raw))
            .ToArray();
        if (normalized.Length > 250) throw new InvalidOperationException("Regional overlay limit exceeded.");

        var state = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(parent.GetRawText()) ?? [];
        var preserved = ArrayEntries(parent, "userLayers")
            .Where(item => StringValue(item, "regionId") != regionId)
            .Concat(normalized)
            .ToArray();
        state["userLayers"] = JsonSerializer.SerializeToElement(preserved);
        state["worldId"] = JsonSerializer.SerializeToElement(worldId);
        return JsonSerializer.SerializeToElement(state);
    }

    static JsonElement NormalizeOverlay(
        string worldId, string regionId, string parentNodeId, int parentTier,
        IEnumerable<int> selectedCells, string gridShape, JsonElement raw)
    {
        if (raw.ValueKind != JsonValueKind.Object)
            throw new InvalidOperationException("Invalid regional overlay.");

        var cells = CanonicalCells(selectedCells);
        var shape = gridShape == "hex" ? "hex" : "square";
        var frame = FrameFor(cells);

        var hasRecursive = raw.TryGetProperty("recursive", out var recursive)
            && recursive.ValueKind == JsonValueKind.Object
            && string.Equals(StringValue(recursive, "format"), WorldSession.RecursiveScopeFormat, StringComparison.Ordinal)
            && string.Equals(StringValue(recursive, "scopeKind"), "REGION", StringComparison.OrdinalIgnoreCase)
            && string.Equals(StringValue(recursive, "scopeId"), regionId, StringComparison.Ordinal);

        double worldX;
        double worldY;
        double localX;
        double localY;

        if (hasRecursive)
        {
            localX = Math.Clamp(NumberValue(recursive, "x", 0), 0, 1);
            localY = Math.Clamp(NumberValue(recursive, "y", 0), 0, 1);
            (worldX, worldY) = WorldPoint(localX, localY, frame);
        }
        else
        {
            worldX = NumberValue(raw, "x", -1);
            worldY = NumberValue(raw, "y", -1);
            if (worldX < 0 || worldX > 1 || worldY < 0 || worldY > 1)
                throw new UnauthorizedAccessException("Regional overlay is outside the claimed coordinates.");
            (localX, localY) = LocalPoint(worldX, worldY, frame);
        }

        if (worldX < 0 || worldX > 1 || worldY < 0 || worldY > 1
            || !cells.Contains(CellAt(worldX, worldY, shape)))
            throw new UnauthorizedAccessException("Regional overlay is outside the claimed coordinates.");

        if (BoolValue(raw, "fullWorld") || StringValue(raw, "placementRole") == "world-map")
            throw new UnauthorizedAccessException("Regional overlays cannot replace the parent map.");

        if (raw.TryGetProperty("tier", out var legacyTier)
            && legacyTier.TryGetInt32(out var legacyTierValue)
            && legacyTierValue != parentTier)
            throw new UnauthorizedAccessException("Regional overlay cannot leave its selected WorldBuilder tier.");

        var legacyWorldLayer = IntValue(raw, "worldLayer", IntValue(raw, "layer", 0));
        var legacyRegionLayer = IntValue(raw, "regionLayer", 1);
        if (legacyWorldLayer < LegacyWorldLayerMin || legacyWorldLayer > LegacyWorldLayerMax)
            throw new UnauthorizedAccessException("World Z must be between 0 and 9.");
        if (legacyRegionLayer < LegacyRegionLayerMin || legacyRegionLayer > LegacyRegionLayerMax)
            throw new UnauthorizedAccessException("Legacy Region layer must be between 1 and 9.");

        var recursiveTier = hasRecursive ? Math.Max(1, IntValue(recursive, "tier", 1)) : 1;
        var recursiveLayer = hasRecursive
            ? Math.Max(1, IntValue(recursive, "layer", legacyRegionLayer))
            : Math.Max(1, legacyRegionLayer);

        // The old z100 address is kept only so the current prototype can render
        // the same representation during migration. Recursive Tier does not feed
        // this value and recursive Layer is only projected into its 1..9 legacy
        // window.
        var compatibilityRegionLayer = Math.Clamp(recursiveLayer, LegacyRegionLayerMin, LegacyRegionLayerMax);
        var z100 = legacyWorldLayer * 100 + compatibilityRegionLayer;
        if (raw.TryGetProperty("z100", out var rawZ) && rawZ.ValueKind == JsonValueKind.Number
            && rawZ.TryGetInt32(out var supplied) && supplied != legacyWorldLayer * 100 + legacyRegionLayer
            && !hasRecursive)
            throw new InvalidOperationException("Legacy Region Z does not match its world and region layers.");

        var assetId = StringValue(raw, "id");
        var linkedGroupId = hasRecursive ? StringValue(recursive, "linkedGroupId") : StringValue(raw, "groupId");
        var permissionResourceId = hasRecursive ? StringValue(recursive, "permissionResourceId") : "";
        if (string.IsNullOrWhiteSpace(permissionResourceId) && !string.IsNullOrWhiteSpace(assetId))
            permissionResourceId = WorldSession.RecursivePermissionResourceId(assetId);

        var item = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(raw.GetRawText()) ?? [];
        item["worldId"] = JsonSerializer.SerializeToElement(worldId);
        item["regionId"] = JsonSerializer.SerializeToElement(regionId);
        item["parentNodeId"] = JsonSerializer.SerializeToElement(parentNodeId);
        item["parentTierIndex"] = JsonSerializer.SerializeToElement(parentTier);

        // Compatibility representation fields.
        item["x"] = JsonSerializer.SerializeToElement(worldX);
        item["y"] = JsonSerializer.SerializeToElement(worldY);
        item["tier"] = JsonSerializer.SerializeToElement(parentTier);
        item["worldLayer"] = JsonSerializer.SerializeToElement(legacyWorldLayer);
        item["layer"] = JsonSerializer.SerializeToElement(legacyWorldLayer);
        item["regionLayer"] = JsonSerializer.SerializeToElement(compatibilityRegionLayer);
        item["z100"] = JsonSerializer.SerializeToElement(z100);
        item["parallaxMode"] = JsonSerializer.SerializeToElement("recursive-region");
        item["anchorTier"] = JsonSerializer.SerializeToElement(parentTier);

        // Canonical REGION scope authority.
        item["recursive"] = JsonSerializer.SerializeToElement(new
        {
            format = WorldSession.RecursiveScopeFormat,
            assetId,
            scopeKind = "REGION",
            scopeId = regionId,
            parentScopeId = worldId,
            parentAssetId = parentNodeId,
            x = localX,
            y = localY,
            tier = recursiveTier,
            layer = recursiveLayer,
            viewDegrees = 15,
            opacity = hasRecursive ? Math.Clamp(NumberValue(recursive, "opacity", 1), 0, 1) : 1,
            visible = hasRecursive ? BoolValueOr(recursive, "visible", true) : true,
            locked = hasRecursive ? BoolValueOr(recursive, "locked", false) : false,
            linkedGroupId,
            permissionResourceId
        });

        return JsonSerializer.SerializeToElement(item);
    }

    static int[] CanonicalCells(IEnumerable<int> selectedCells)
    {
        var cells = selectedCells.Where(i => i >= 0 && i < Columns * Rows).Distinct().Order().ToArray();
        if (cells.Length == 0)
            throw new InvalidOperationException("The saved deed has no valid world cells.");
        return cells;
    }

    static RegionFrame FrameFor(IEnumerable<int> selectedCells)
    {
        var cells = CanonicalCells(selectedCells);
        var minColumn = cells.Min(i => i % Columns);
        var maxColumn = cells.Max(i => i % Columns);
        var minRow = cells.Min(i => i / Columns);
        var maxRow = cells.Max(i => i / Columns);
        return new RegionFrame(
            minColumn / (double)Columns,
            minRow / (double)Rows,
            (maxColumn + 1) / (double)Columns,
            (maxRow + 1) / (double)Rows);
    }

    static (double X, double Y) LocalPoint(double worldX, double worldY, RegionFrame frame)
    {
        var width = Math.Max(1.0 / Columns, frame.Right - frame.Left);
        var height = Math.Max(1.0 / Rows, frame.Bottom - frame.Top);
        return (
            Math.Clamp((worldX - frame.Left) / width, 0, 1),
            Math.Clamp((worldY - frame.Top) / height, 0, 1));
    }

    static (double X, double Y) WorldPoint(double localX, double localY, RegionFrame frame)
    {
        var width = Math.Max(1.0 / Columns, frame.Right - frame.Left);
        var height = Math.Max(1.0 / Rows, frame.Bottom - frame.Top);
        return (
            frame.Left + Math.Clamp(localX, 0, 1) * width,
            frame.Top + Math.Clamp(localY, 0, 1) * height);
    }

    static JsonElement[] ArrayEntries(JsonElement obj, string name) =>
        obj.ValueKind == JsonValueKind.Object && obj.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.Array
            ? value.EnumerateArray().ToArray() : [];

    static int IntValue(JsonElement item, string key, int fallback) =>
        item.ValueKind == JsonValueKind.Object && item.TryGetProperty(key, out var value)
        && value.ValueKind == JsonValueKind.Number && value.TryGetInt32(out var n) ? n : fallback;

    static double NumberValue(JsonElement item, string key, double fallback) =>
        item.ValueKind == JsonValueKind.Object && item.TryGetProperty(key, out var value)
        && value.ValueKind == JsonValueKind.Number && value.TryGetDouble(out var n) && double.IsFinite(n) ? n : fallback;

    static string StringValue(JsonElement item, string key) =>
        item.ValueKind == JsonValueKind.Object && item.TryGetProperty(key, out var value)
        && value.ValueKind == JsonValueKind.String ? value.GetString() ?? "" : "";

    static bool BoolValue(JsonElement item, string key) =>
        item.ValueKind == JsonValueKind.Object && item.TryGetProperty(key, out var value)
        && value.ValueKind == JsonValueKind.True;

    static bool BoolValueOr(JsonElement item, string key, bool fallback)
    {
        if (item.ValueKind != JsonValueKind.Object || !item.TryGetProperty(key, out var value))
            return fallback;
        return value.ValueKind switch
        {
            JsonValueKind.True => true,
            JsonValueKind.False => false,
            _ => fallback
        };
    }

    static int CellAt(double x, double y, string shape)
    {
        x = Math.Clamp(x, 0, 1);
        y = Math.Clamp(y, 0, 1);
        if (shape != "hex")
            return Math.Min(Columns - 1, (int)(Math.Min(x, .999999) * Columns))
                + Columns * Math.Min(Rows - 1, (int)(Math.Min(y, .999999) * Rows));

        var width = Columns * .75 + .25;
        var height = Rows + .5;
        var best = 0;
        var bestDistance = double.MaxValue;
        for (var i = 0; i < Columns * Rows; i++)
        {
            var col = i % Columns;
            var row = i / Columns;
            var dx = (col * .75 + .5) / width - x;
            var dy = (row + (col % 2) * .5 + .5) / height - y;
            var d = dx * dx + dy * dy;
            if (d >= bestDistance) continue;
            bestDistance = d;
            best = i;
        }
        return best;
    }

    readonly record struct RegionFrame(double Left, double Top, double Right, double Bottom);
}
