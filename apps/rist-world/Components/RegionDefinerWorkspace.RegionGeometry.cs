using System.Text.Json;
using Microsoft.JSInterop;

namespace RistWorld.Components;

public partial class RegionDefinerWorkspace
{
    [JSInvokable]
    public async Task<object> CreateRegionGeometryFromPrototypeAsync(JsonElement request)
    {
        var name = GeometryString(request, "name").Trim();

        // RegionDefiner v3 defines X/Y first from the permanent square World
        // coordinate grid. Cells are derived compatibility/index data only.
        var canonicalMinX = GeometryUnit(request, "canonicalMinX", 0);
        var canonicalMinY = GeometryUnit(request, "canonicalMinY", 0);
        var canonicalMaxX = GeometryUnit(request, "canonicalMaxX", 1);
        var canonicalMaxY = GeometryUnit(request, "canonicalMaxY", 1);
        if (canonicalMaxX < canonicalMinX)
            (canonicalMinX, canonicalMaxX) = (canonicalMaxX, canonicalMinX);
        if (canonicalMaxY < canonicalMinY)
            (canonicalMinY, canonicalMaxY) = (canonicalMaxY, canonicalMinY);
        if (canonicalMaxX <= canonicalMinX || canonicalMaxY <= canonicalMinY)
            throw new InvalidOperationException("Define four distinct X/Y Region boundaries before choosing Z.");

        var cells = GeometryIntArray(request, "cells");
        if (cells.Count == 0)
            cells = RectangleCells(
                canonicalMinX,
                canonicalMinY,
                canonicalMaxX,
                canonicalMaxY,
                WorldSession.SpatialScopeGridColumns,
                WorldSession.SpatialScopeGridRows);

        var boundaryGridColumns = Math.Clamp(GeometryInt(request, "boundaryGridColumns", 64), 1, 64);
        var boundaryGridRows = Math.Clamp(GeometryInt(request, "boundaryGridRows", 64), 1, 64);
        var boundaryCells = GeometryIntArray(request, "boundaryCells");
        if (boundaryCells.Count == 0)
            boundaryCells = RectangleBoundaryCells(
                canonicalMinX,
                canonicalMinY,
                canonicalMaxX,
                canonicalMaxY,
                boundaryGridColumns,
                boundaryGridRows);

        // Tier is not selected until X/Y has been confirmed. The Region volume
        // is inclusive Min Tier..Max Tier; canonical Z stores an exclusive top.
        var legacyTierIndex = Math.Max(0, GeometryInt(request, "tierIndex", 0));
        var minTierIndex = Math.Max(0, GeometryInt(request, "minTierIndex", legacyTierIndex));
        var maxTierIndex = Math.Max(0, GeometryInt(request, "maxTierIndex", minTierIndex));
        if (maxTierIndex < minTierIndex)
            (minTierIndex, maxTierIndex) = (maxTierIndex, minTierIndex);

        var sourceLayerOffsets = Enumerable.Range(0, WorldSession.LayersPerTier).ToList();
        var visibleTierIndices = Enumerable.Range(
            minTierIndex,
            (maxTierIndex - minTierIndex) + 1).ToList();
        var visibleLayerOffsets = sourceLayerOffsets.ToList();

        var viewMinX = GeometryUnit(request, "viewMinX", canonicalMinX);
        var viewMinY = GeometryUnit(request, "viewMinY", canonicalMinY);
        var viewMaxX = GeometryUnit(request, "viewMaxX", canonicalMaxX);
        var viewMaxY = GeometryUnit(request, "viewMaxY", canonicalMaxY);
        if (viewMaxX < viewMinX) (viewMinX, viewMaxX) = (viewMaxX, viewMinX);
        if (viewMaxY < viewMinY) (viewMinY, viewMaxY) = (viewMaxY, viewMinY);

        var region = await Session.CreateRegionAsync(
            name: name,
            selectedCells: cells,
            tierIndex: minTierIndex,
            sourceLayerOffsets: sourceLayerOffsets,
            gridShape: "square",
            boundaryCells: boundaryCells,
            boundaryGridColumns: boundaryGridColumns,
            boundaryGridRows: boundaryGridRows,
            viewMinX: viewMinX,
            viewMinY: viewMinY,
            viewMaxX: viewMaxX,
            viewMaxY: viewMaxY,
            canonicalMinX: canonicalMinX,
            canonicalMinY: canonicalMinY,
            canonicalMaxX: canonicalMaxX,
            canonicalMaxY: canonicalMaxY,
            resolutionScope: "REGION",
            viewZoomRatio: Math.Max(1, GeometryDouble(request, "viewZoomRatio", 1)),
            viewAngle: 60,
            visibleTierIndices: visibleTierIndices,
            visibleLayerOffsets: visibleLayerOffsets);

        region = await Session.ApplyRegionVolumeAsync(region.RegionId, minTierIndex, maxTierIndex);
        return GeometryRegion(region);
    }

    [JSInvokable]
    public object[] GetRegionGeometryCatalogForPrototype() =>
        Session.Regions.Select(GeometryRegion).ToArray();

    static object GeometryRegion(WorldRegion region)
    {
        var (minTierIndex, maxTierIndex) = WorldSession.RegionTierBounds(region);
        return new
        {
            id = region.RegionId,
            worldId = region.WorldId,
            name = region.Name,
            volumeModel = "BOUNDED_WORLD_VOLUME",
            selectedCells = region.SelectedCells,
            boundaryCells = region.BoundaryCells ?? [],
            boundaryGridColumns = region.BoundaryGridColumns,
            boundaryGridRows = region.BoundaryGridRows,
            gridShape = "square",
            tierIndex = minTierIndex,
            minTierIndex,
            maxTierIndex,
            canonicalZMin = region.CanonicalZMin,
            canonicalZMax = region.CanonicalZMax,
            sourceLayerOffsets = region.SourceLayerOffsets ?? [],
            viewMinX = region.ViewMinX,
            viewMinY = region.ViewMinY,
            viewMaxX = region.ViewMaxX,
            viewMaxY = region.ViewMaxY,
            canonicalMinX = region.CanonicalMinX,
            canonicalMinY = region.CanonicalMinY,
            canonicalMaxX = region.CanonicalMaxX,
            canonicalMaxY = region.CanonicalMaxY,
            resolutionScope = "REGION",
            viewZoomRatio = region.ViewZoomRatio,
            viewAngle = 60,
            visibleTierIndices = region.VisibleTierIndices ?? [],
            visibleLayerOffsets = region.VisibleLayerOffsets ?? []
        };
    }

    static List<int> RectangleCells(
        double minX,
        double minY,
        double maxX,
        double maxY,
        int columns,
        int rows)
    {
        columns = Math.Max(1, columns);
        rows = Math.Max(1, rows);
        var minColumn = Math.Clamp((int)Math.Floor(minX * columns), 0, columns - 1);
        var maxColumn = Math.Clamp((int)Math.Ceiling(maxX * columns) - 1, minColumn, columns - 1);
        var minRow = Math.Clamp((int)Math.Floor(minY * rows), 0, rows - 1);
        var maxRow = Math.Clamp((int)Math.Ceiling(maxY * rows) - 1, minRow, rows - 1);
        var result = new List<int>((maxColumn - minColumn + 1) * (maxRow - minRow + 1));
        for (var row = minRow; row <= maxRow; row++)
        for (var column = minColumn; column <= maxColumn; column++)
            result.Add((row * columns) + column);
        return result;
    }

    static List<int> RectangleBoundaryCells(
        double minX,
        double minY,
        double maxX,
        double maxY,
        int columns,
        int rows)
    {
        columns = Math.Max(1, columns);
        rows = Math.Max(1, rows);
        var minColumn = Math.Clamp((int)Math.Floor(minX * columns), 0, columns - 1);
        var maxColumn = Math.Clamp((int)Math.Ceiling(maxX * columns) - 1, minColumn, columns - 1);
        var minRow = Math.Clamp((int)Math.Floor(minY * rows), 0, rows - 1);
        var maxRow = Math.Clamp((int)Math.Ceiling(maxY * rows) - 1, minRow, rows - 1);
        var result = new List<int>();
        for (var row = minRow; row <= maxRow; row++)
        for (var column = minColumn; column <= maxColumn; column++)
        {
            if (row == minRow || row == maxRow || column == minColumn || column == maxColumn)
                result.Add((row * columns) + column);
        }
        return result.Distinct().Order().ToList();
    }

    static bool GeometryProperty(JsonElement source, string name, out JsonElement value)
    {
        value = default;
        return source.ValueKind == JsonValueKind.Object && source.TryGetProperty(name, out value);
    }

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

    static double GeometryUnit(JsonElement source, string name, double fallback) =>
        Math.Clamp(GeometryDouble(source, name, fallback), 0, 1);

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
