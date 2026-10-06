using System.Text.Json;
using Microsoft.JSInterop;

namespace RistWorld.Components;

public partial class RegionDefinerWorkspace
{
    [JSInvokable]
    public async Task<object> CreateRegionGeometryFromPrototypeAsync(JsonElement request)
    {
        var name = GeometryString(request, "name").Trim();
        var cells = GeometryIntArray(request, "cells");
        var boundaryCells = GeometryIntArray(request, "boundaryCells");
        var tierIndex = Math.Max(0, GeometryInt(request, "tierIndex", 0));
        var sourceLayerOffsets = GeometryIntArray(request, "sourceLayerOffsets");
        if (sourceLayerOffsets.Count == 0)
            sourceLayerOffsets = Enumerable.Range(0, WorldSession.LayersPerTier).ToList();

        var visibleTierIndices = GeometryIntArray(request, "visibleTierIndices")
            .Where(value => value >= 0)
            .Distinct()
            .Order()
            .ToList();
        if (visibleTierIndices.Count == 0)
            visibleTierIndices.Add(tierIndex);

        var visibleLayerOffsets = GeometryIntArray(request, "visibleLayerOffsets")
            .Where(value => value >= 0 && value < WorldSession.LayersPerTier)
            .Distinct()
            .Order()
            .ToList();
        if (visibleLayerOffsets.Count == 0)
            visibleLayerOffsets = sourceLayerOffsets
                .Where(value => value >= 0 && value < WorldSession.LayersPerTier)
                .Distinct()
                .Order()
                .ToList();

        var region = await Session.CreateRegionAsync(
            name,
            cells,
            tierIndex,
            sourceLayerOffsets,
            GeometryString(request, "gridShape", "square"),
            boundaryCells,
            Math.Clamp(GeometryInt(request, "boundaryGridColumns", 64), 1, 64),
            Math.Clamp(GeometryInt(request, "boundaryGridRows", 64), 1, 64),
            GeometryDouble(request, "viewMinX", 0),
            GeometryDouble(request, "viewMinY", 0),
            GeometryDouble(request, "viewMaxX", 1),
            GeometryDouble(request, "viewMaxY", 1),
            GeometryDouble(request, "canonicalMinX", double.NaN),
            GeometryDouble(request, "canonicalMinY", double.NaN),
            GeometryDouble(request, "canonicalMaxX", double.NaN),
            GeometryDouble(request, "canonicalMaxY", double.NaN),
            GeometryString(request, "resolutionScope", "REGION"),
            Math.Max(1, GeometryDouble(request, "viewZoomRatio", 1)),
            Math.Clamp(GeometryInt(request, "viewAngle", 60), 0, 89),
            visibleTierIndices,
            visibleLayerOffsets);

        return GeometryRegion(region);
    }

    [JSInvokable]
    public object[] GetRegionGeometryCatalogForPrototype() =>
        Session.Regions.Select(GeometryRegion).ToArray();

    static object GeometryRegion(WorldRegion region) => new
    {
        id = region.RegionId,
        worldId = region.WorldId,
        name = region.Name,
        selectedCells = region.SelectedCells,
        boundaryCells = region.BoundaryCells ?? [],
        boundaryGridColumns = region.BoundaryGridColumns,
        boundaryGridRows = region.BoundaryGridRows,
        gridShape = region.GridShape,
        tierIndex = region.TierIndex,
        sourceLayerOffsets = region.SourceLayerOffsets ?? [],
        viewMinX = region.ViewMinX,
        viewMinY = region.ViewMinY,
        viewMaxX = region.ViewMaxX,
        viewMaxY = region.ViewMaxY,
        canonicalMinX = region.CanonicalMinX,
        canonicalMinY = region.CanonicalMinY,
        canonicalMaxX = region.CanonicalMaxX,
        canonicalMaxY = region.CanonicalMaxY,
        resolutionScope = region.ResolutionScope,
        viewZoomRatio = region.ViewZoomRatio,
        viewAngle = region.ViewAngle,
        visibleTierIndices = region.VisibleTierIndices ?? [],
        visibleLayerOffsets = region.VisibleLayerOffsets ?? []
    };

    static bool GeometryProperty(JsonElement source, string name, out JsonElement value) =>
        source.ValueKind == JsonValueKind.Object && source.TryGetProperty(name, out value);

    static string GeometryString(JsonElement source, string name, string fallback = "") =>
        GeometryProperty(source, name, out var value) && value.ValueKind == JsonValueKind.String
            ? value.GetString() ?? fallback
            : fallback;

    static int GeometryInt(JsonElement source, string name, int fallback = 0)
    {
        if (!GeometryProperty(source, name, out var value)) return fallback;
        if (value.ValueKind == JsonValueKind.Number && value.TryGetInt32(out var number)) return number;
        if (value.ValueKind == JsonValueKind.String && int.TryParse(value.GetString(), out number)) return number;
        return fallback;
    }

    static double GeometryDouble(JsonElement source, string name, double fallback = 0)
    {
        if (!GeometryProperty(source, name, out var value)) return fallback;
        if (value.ValueKind == JsonValueKind.Number && value.TryGetDouble(out var number)) return number;
        if (value.ValueKind == JsonValueKind.String && double.TryParse(value.GetString(), out number)) return number;
        return fallback;
    }

    static List<int> GeometryIntArray(JsonElement source, string name)
    {
        if (!GeometryProperty(source, name, out var value) || value.ValueKind != JsonValueKind.Array)
            return [];

        var result = new List<int>();
        foreach (var item in value.EnumerateArray())
        {
            if (item.ValueKind == JsonValueKind.Number && item.TryGetInt32(out var number))
                result.Add(number);
            else if (item.ValueKind == JsonValueKind.String && int.TryParse(item.GetString(), out number))
                result.Add(number);
        }
        return result.Distinct().Order().ToList();
    }
}
