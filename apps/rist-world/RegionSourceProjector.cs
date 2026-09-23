using System.Text.Json;

namespace RistWorld;

// Pure projection and validation for privately stored WorldBuilder sources.
// Same source-cell contract as the shared DynamoDB region projection.
public static class RegionSourceProjector
{
    public static JsonElement Project(
        string worldId, string regionId, string parentNodeId, int parentTier,
        IEnumerable<int> selectedCells, string gridShape,
        IEnumerable<int> sourceLayerOffsets, JsonElement parent, JsonElement? child = null)
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
            && permitted.Contains(CellAt(
                NumberValue(tile, "x", 0), NumberValue(tile, "y", 0), shape))).ToArray();
        var saved = child.HasValue && child.Value.ValueKind == JsonValueKind.Object ? child.Value : default;
        var hasSaved = saved.ValueKind == JsonValueKind.Object && StringValue(saved, "regionId") == regionId;
        var childLayers = hasSaved ? ArrayEntries(saved, "userLayers") :
            ArrayEntries(parent, "userLayers").Where(x => StringValue(x, "regionId") == regionId).ToArray();
        var normalized = childLayers.Select(raw =>
        {
            var values = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(raw.GetRawText())!;
            if (!hasSaved && !values.ContainsKey("relativeTier"))
            {
                values["tier"] = JsonSerializer.SerializeToElement(0);
                values["relativeTier"] = JsonSerializer.SerializeToElement(0);
            }
            return JsonSerializer.SerializeToElement(values);
        }).ToArray();
        var relativeTiers = hasSaved ? ArrayEntries(saved, "relativeTiers") : [];
        if (relativeTiers.Length == 0)
            relativeTiers = [JsonSerializer.SerializeToElement(new
            {
                id = regionId + ":tier:0", index = 0, label = "Region Base", sourceParentTier = parentTier
            })];
        var images = ArrayEntries(parent, "tierImages");
        var bitmap = images.Length > parentTier
            && images[parentTier].ValueKind == JsonValueKind.String
            && !string.IsNullOrWhiteSpace(images[parentTier].GetString());
        return JsonSerializer.SerializeToElement(new
        {
            projection = "region-child-v1", worldId, regionId,
            parentNodeId, parentTierIndex = parentTier,
            gridShape = shape, selectedCells = cells,
            sourceCells = cells.Select(i => new
            {
                id = $"{worldId}:{parentNodeId}:tier:{parentTier}:cell:{i}",
                cellIndex = i, column = i % 30, row = i / 30, tierIndex = parentTier
            }).ToArray(),
            sourceTileIndex = index, tiles, userLayers = normalized, relativeTiers,
            gridColumns = 30, gridRows = 30,
            sourcePixelWidth = IntValue(parent, "sourcePixelWidth", 2508),
            sourcePixelHeight = IntValue(parent, "sourcePixelHeight", 2508),
            sourceLayerOffsets = layers.Order().ToArray(),
            requiresRasterIndex = bitmap && index.Select(x => IntValue(x, "cellIndex", -1)).Distinct().Count() < cells.Length,
            sourceBitmapWasOmitted = bitmap
        });
    }

    public static JsonElement NormalizeChild(
        string worldId, string regionId, string parentNodeId, int parentTier,
        IEnumerable<int> selectedCells, string gridShape,
        JsonElement layers, JsonElement tiers)
    {
        if (layers.ValueKind != JsonValueKind.Array || tiers.ValueKind != JsonValueKind.Array)
            throw new InvalidOperationException("Regional layers and tiers must be arrays.");
        var chosen = selectedCells.Where(i => i >= 0 && i < 900).ToHashSet();
        if (chosen.Count == 0) throw new UnauthorizedAccessException("Region deed contains no valid source cells.");
        var tierList = tiers.EnumerateArray().ToArray();
        var allowed = tierList.Select(x => IntValue(x, "index", -1)).ToArray();
        if (allowed.Length == 0 || allowed.Length > 10 || !allowed.Contains(0)
            || allowed.Distinct().Count() != allowed.Length || allowed.Any(x => x < 0 || x > 9))
            throw new InvalidOperationException("Regional tier indexes must be unique, between 0 and 9, including base tier 0.");
        var incoming = layers.EnumerateArray().ToArray();
        if (incoming.Length > 250) throw new InvalidOperationException("Regional object limit exceeded.");
        var normalized = new List<Dictionary<string, JsonElement>>();
        foreach (var raw in incoming)
        {
            if (raw.ValueKind != JsonValueKind.Object) throw new InvalidOperationException("Invalid regional object.");
            var relative = IntValue(raw, "relativeTier", IntValue(raw, "tier", 0));
            var layer = IntValue(raw, "layer", 0);
            var x = NumberValue(raw, "x", -1);
            var y = NumberValue(raw, "y", -1);
            if (!allowed.Contains(relative) || layer < 0 || layer > 9)
                throw new UnauthorizedAccessException("Object targets an unclaimed regional tier or layer.");
            if (x < 0 || x > 1 || y < 0 || y > 1
                || !chosen.Contains(CellAt(x, y, gridShape)))
                throw new UnauthorizedAccessException("Object is outside the deed's selected source cells.");
            if (BoolValue(raw, "fullWorld") || StringValue(raw, "placementRole") == "world-map")
                throw new UnauthorizedAccessException("Regional objects cannot replace the parent map.");
            var item = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(raw.GetRawText())!;
            item["worldId"] = JsonSerializer.SerializeToElement(worldId);
            item["regionId"] = JsonSerializer.SerializeToElement(regionId);
            item["parentNodeId"] = JsonSerializer.SerializeToElement(parentNodeId);
            item["parentTierIndex"] = JsonSerializer.SerializeToElement(parentTier);
            item["tier"] = JsonSerializer.SerializeToElement(relative);
            item["relativeTier"] = JsonSerializer.SerializeToElement(relative);
            item["parallaxMode"] = JsonSerializer.SerializeToElement(relative == 0 ? "anchored" : "tier");
            normalized.Add(item);
        }
        return JsonSerializer.SerializeToElement(new
        {
            worldId, regionId, parentNodeId, parentTierIndex = parentTier,
            sourceCells = chosen.Order().ToArray(),
            userLayers = normalized, relativeTiers = tierList
        });
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
