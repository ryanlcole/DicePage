using System.Text.Json;

namespace RistWorld;

// RegionDefiner is a filtered WorldBuilder view. Parent World Z remains integer
// 0..9 (Layer 1..10). Region overlays occupy exact hundredths above it.
public static class RegionSourceProjector
{
    public static JsonElement Project(
        string worldId, string regionId, string parentNodeId, int parentTier,
        IEnumerable<int> selectedCells, string gridShape,
        IEnumerable<int> sourceLayerOffsets, JsonElement parent)
    {
        var cells = selectedCells.Where(i => i >= 0 && i < 900).Distinct().Order().ToArray();
        if (cells.Length == 0) throw new InvalidOperationException("The saved deed has no valid world cells.");
        var permitted = cells.ToHashSet();
        var layers = sourceLayerOffsets.Where(i => i >= 0 && i < 10).Distinct().ToHashSet();
        if (layers.Count == 0) layers = Enumerable.Range(0, 10).ToHashSet();
        var shape = gridShape == "hex" ? "hex" : "square";

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
            projection = "region-world-z-v2", worldId, regionId, parentNodeId,
            parentTierIndex = parentTier, gridShape = shape, selectedCells = cells,
            sourceCells = cells.Select(i => new
            {
                id = $"{worldId}:{parentNodeId}:tier:{parentTier}:cell:{i}",
                cellIndex = i, column = i % 30, row = i / 30, tierIndex = parentTier
            }).ToArray(),
            sourceTileIndex = index, tiles, sourceUserLayers, userLayers = regionLayers,
            gridColumns = 30, gridRows = 30,
            sourcePixelWidth = IntValue(parent, "sourcePixelWidth", 2508),
            sourcePixelHeight = IntValue(parent, "sourcePixelHeight", 2508),
            sourceLayerOffsets = layers.Order().ToArray(),
            requiresRasterIndex = bitmap && index.Select(x => IntValue(x, "cellIndex", -1)).Distinct().Count() < cells.Length,
            sourceBitmapWasOmitted = bitmap,
            zModel = new
            {
                worldIntegerMin = 0, worldIntegerMax = 9,
                regionHundredthMin = 1, regionHundredthMax = 9,
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
        var cells = selectedCells.Where(i => i >= 0 && i < 900).Distinct().Order().ToArray();
        if (cells.Length == 0) throw new UnauthorizedAccessException("Region deed contains no valid source cells.");
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
        var worldLayer = IntValue(raw, "worldLayer", IntValue(raw, "layer", 0));
        var regionLayer = IntValue(raw, "regionLayer", 1);
        if (worldLayer < 0 || worldLayer > 9)
            throw new UnauthorizedAccessException("World Z must be between 0 and 9.");
        if (regionLayer < 1 || regionLayer > 9)
            throw new UnauthorizedAccessException("Region layer must be between 1 and 9.");
        if (raw.TryGetProperty("tier", out var tier) && tier.TryGetInt32(out var tierValue) && tierValue != parentTier)
            throw new UnauthorizedAccessException("Regional overlay cannot leave its selected WorldBuilder tier.");

        var x = NumberValue(raw, "x", -1);
        var y = NumberValue(raw, "y", -1);
        if (x < 0 || x > 1 || y < 0 || y > 1 || !selectedCells.Contains(CellAt(x, y, gridShape)))
            throw new UnauthorizedAccessException("Regional overlay is outside the claimed coordinates.");
        if (BoolValue(raw, "fullWorld") || StringValue(raw, "placementRole") == "world-map")
            throw new UnauthorizedAccessException("Regional overlays cannot replace the parent map.");

        var z100 = worldLayer * 100 + regionLayer;
        if (raw.TryGetProperty("z100", out var rawZ) && rawZ.ValueKind == JsonValueKind.Number
            && rawZ.TryGetInt32(out var supplied) && supplied != z100)
            throw new InvalidOperationException("Region Z does not match its world and region layers.");

        var item = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(raw.GetRawText()) ?? [];
        item["worldId"] = JsonSerializer.SerializeToElement(worldId);
        item["regionId"] = JsonSerializer.SerializeToElement(regionId);
        item["parentNodeId"] = JsonSerializer.SerializeToElement(parentNodeId);
        item["parentTierIndex"] = JsonSerializer.SerializeToElement(parentTier);
        item["tier"] = JsonSerializer.SerializeToElement(parentTier);
        item["worldLayer"] = JsonSerializer.SerializeToElement(worldLayer);
        item["layer"] = JsonSerializer.SerializeToElement(worldLayer);
        item["regionLayer"] = JsonSerializer.SerializeToElement(regionLayer);
        item["z100"] = JsonSerializer.SerializeToElement(z100);
        item["parallaxMode"] = JsonSerializer.SerializeToElement("anchored");
        item["anchorTier"] = JsonSerializer.SerializeToElement(parentTier);
        return JsonSerializer.SerializeToElement(item);
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

    static int CellAt(double x, double y, string shape)
    {
        x = Math.Clamp(x, 0, 1);
        y = Math.Clamp(y, 0, 1);
        if (shape != "hex")
            return Math.Min(29, (int)(Math.Min(x, .999999) * 30))
                + 30 * Math.Min(29, (int)(Math.Min(y, .999999) * 30));

        var width = 30 * .75 + .25;
        var height = 30 + .5;
        var best = 0;
        var bestDistance = double.MaxValue;
        for (var i = 0; i < 900; i++)
        {
            var col = i % 30;
            var row = i / 30;
            var dx = (col * .75 + .5) / width - x;
            var dy = (row + (col % 2) * .5 + .5) / height - y;
            var d = dx * dx + dy * dy;
            if (d >= bestDistance) continue;
            bestDistance = d;
            best = i;
        }
        return best;
    }
}
