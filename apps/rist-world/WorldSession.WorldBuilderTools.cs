namespace RistWorld;

public sealed partial class WorldSession
{
    static readonly HashSet<string> AllowedWorldBuilderTools = new(StringComparer.Ordinal)
    {
        "draw", "brush", "fill", "line", "square", "circle", "erase"
    };

    public string WorldBuilderTool { get; private set; } = "draw";
    public string WorldBuilderStatus { get; private set; } = "Select a tile, unlock the map, then draw.";
    public int? WorldBuilderAnchorColumn { get; private set; }
    public int? WorldBuilderAnchorRow { get; private set; }
    public string BaseTerrainOverrideTileId { get; private set; } = "";

    public AtlasTile? SelectedWorldBuilderTile =>
        string.IsNullOrWhiteSpace(SelectedTile) ? null : AtlasTiles.FirstOrDefault(x => x.Id == SelectedTile);

    public AtlasTile? BaseTerrainOverrideTile =>
        string.IsNullOrWhiteSpace(BaseTerrainOverrideTileId) ? null : AtlasTiles.FirstOrDefault(x => x.Id == BaseTerrainOverrideTileId);

    public void SetWorldBuilderTool(string? tool)
    {
        var normalized = (tool ?? "").Trim().ToLowerInvariant();
        if (!AllowedWorldBuilderTools.Contains(normalized)) normalized = "draw";
        WorldBuilderTool = normalized;
        CancelWorldBuilderShape();
        WorldBuilderStatus = normalized switch
        {
            "line" or "square" or "circle" => "Tap a start cell, then an end cell.",
            "erase" => "Tap cells to return them to the terrain beneath.",
            "fill" => "Tap a region to replace matching terrain.",
            _ => $"{char.ToUpperInvariant(normalized[0]) + normalized[1..]} tool ready."
        };
        Notify();
    }

    public void SelectWorldBuilderTile(AtlasTile tile)
    {
        SelectedTile = tile.Id;
        WorldBuilderStatus = $"Selected {tile.Name}.";
        Notify();
    }

    public void CancelWorldBuilderShape()
    {
        WorldBuilderAnchorColumn = null;
        WorldBuilderAnchorRow = null;
    }

    public bool ApplyWorldBuilderTool(double normalizedX, double normalizedY)
    {
        if (!CanEditTiles)
        {
            WorldBuilderStatus = "World editing requires GameMaster worldbuilder access.";
            Notify();
            return false;
        }
        if (MapLocked)
        {
            WorldBuilderStatus = "Unlock the map to edit terrain.";
            Notify();
            return false;
        }

        var (column, row) = MileCell(normalizedX, normalizedY);
        if (WorldBuilderTool == "erase")
        {
            var changed = EraseCell(column, row);
            WorldBuilderStatus = changed ? $"Erased {CellLabel(column, row)}." : $"Nothing editable at {CellLabel(column, row)}.";
            Notify();
            return changed;
        }

        var selected = SelectedWorldBuilderTile;
        if (selected is null)
        {
            WorldBuilderStatus = "Select a tile from the asset library first.";
            Notify();
            return false;
        }

        var changed = WorldBuilderTool switch
        {
            "draw" => PaintCells(selected, [(column, row)]),
            "brush" => PaintCells(selected, BrushCells(column, row)),
            "fill" => FillRegion(selected, column, row),
            "line" => ApplyAnchoredShape(selected, column, row, LineCells),
            "square" => ApplyAnchoredShape(selected, column, row, RectangleCells),
            "circle" => ApplyAnchoredShape(selected, column, row, CircleCells),
            _ => PaintCells(selected, [(column, row)])
        };
        Notify();
        return changed;
    }

    bool ApplyAnchoredShape(AtlasTile tile, int column, int row, Func<int, int, int, int, IEnumerable<(int Column, int Row)>> shape)
    {
        if (WorldBuilderAnchorColumn is null || WorldBuilderAnchorRow is null)
        {
            WorldBuilderAnchorColumn = column;
            WorldBuilderAnchorRow = row;
            WorldBuilderStatus = $"Start set at {CellLabel(column, row)}. Tap an end cell.";
            return false;
        }

        var startColumn = WorldBuilderAnchorColumn.Value;
        var startRow = WorldBuilderAnchorRow.Value;
        CancelWorldBuilderShape();
        var cells = shape(startColumn, startRow, column, row).Distinct().ToArray();
        var changed = PaintCells(tile, cells);
        WorldBuilderStatus = changed ? $"{WorldBuilderTool} placed across {cells.Length} cell{(cells.Length == 1 ? "" : "s")}." : "No editable cells changed.";
        return changed;
    }

    bool PaintCells(AtlasTile tile, IEnumerable<(int Column, int Row)> cells)
    {
        var changed = false;
        foreach (var (column, row) in cells)
        {
            if (!InsideCell(column, row)) continue;
            var existing = EditableTileAt(column, row);
            if (existing is not null && existing.Id == tile.Id) continue;
            if (existing is not null) PlacedTiles.Remove(existing);
            PlacedTiles.Add(TileForCell(tile, column, row));
            changed = true;
        }
        if (changed && WorldBuilderTool is "draw" or "brush")
            WorldBuilderStatus = $"Painted {tile.Name}.";
        return changed;
    }

    bool EraseCell(int column, int row)
    {
        var tile = EditableTileAt(column, row);
        if (tile is null) return false;
        PlacedTiles.Remove(tile);
        return true;
    }

    bool FillRegion(AtlasTile replacement, int startColumn, int startRow)
    {
        var target = EditableTileAt(startColumn, startRow);
        if (target is null)
        {
            // The implicit ocean is one connected semantic base. Changing it is
            // represented as one override, not 900 authored tile records.
            if (string.Equals(BaseTerrainOverrideTileId, replacement.Id, StringComparison.Ordinal))
            {
                WorldBuilderStatus = $"Base terrain is already {replacement.Name}.";
                return false;
            }
            BaseTerrainOverrideTileId = replacement.Id;
            WorldBuilderStatus = $"Filled the implicit base with {replacement.Name} without materializing 900 cells.";
            return true;
        }

        var targetId = target.Id;
        if (targetId == replacement.Id)
        {
            WorldBuilderStatus = "That region already uses the selected tile.";
            return false;
        }

        var occupied = PlacedTiles
            .Where(IsCurrentAddressTile)
            .Where(x => !x.Locked)
            .GroupBy(TileCell)
            .ToDictionary(g => g.Key, g => g.Last());
        var queue = new Queue<(int Column, int Row)>();
        var visited = new HashSet<(int Column, int Row)>();
        var region = new List<(int Column, int Row)>();
        queue.Enqueue((startColumn, startRow));
        while (queue.Count > 0)
        {
            var cell = queue.Dequeue();
            if (!visited.Add(cell) || !InsideCell(cell.Column, cell.Row)) continue;
            if (!occupied.TryGetValue(cell, out var tile) || tile.Id != targetId) continue;
            region.Add(cell);
            queue.Enqueue((cell.Column - 1, cell.Row));
            queue.Enqueue((cell.Column + 1, cell.Row));
            queue.Enqueue((cell.Column, cell.Row - 1));
            queue.Enqueue((cell.Column, cell.Row + 1));
        }
        var changed = PaintCells(replacement, region);
        WorldBuilderStatus = changed ? $"Filled {region.Count} connected cell{(region.Count == 1 ? "" : "s")}." : "No editable cells changed.";
        return changed;
    }

    TileItem TileForCell(AtlasTile tile, int column, int row) => new(
        tile.Id,
        tile.Name,
        tile.Image,
        column / (double)GridColumns,
        row / (double)GridRows,
        tile.SourceWidth,
        tile.SourceHeight,
        tile.CropX,
        tile.CropY,
        tile.CropWidth,
        tile.CropHeight,
        1,
        CubeX: CubeX,
        CubeY: CubeY,
        CubeZ: CubeZ,
        PlaneIndex: PlaneIndex,
        TierIndex: TierIndex,
        LayerOffset: LayerOffset);

    TileItem? EditableTileAt(int column, int row) => PlacedTiles
        .LastOrDefault(tile => !tile.Locked && IsCurrentAddressTile(tile) && TileCell(tile) == (column, row));

    bool IsCurrentAddressTile(TileItem tile) =>
        tile.CubeX == CubeX && tile.CubeY == CubeY && tile.CubeZ == CubeZ &&
        tile.PlaneIndex == PlaneIndex && tile.TierIndex == TierIndex && tile.LayerOffset == LayerOffset;

    static (int Column, int Row) TileCell(TileItem tile) =>
        (Math.Clamp((int)Math.Round(tile.X * GridColumns), 0, GridColumns - 1),
         Math.Clamp((int)Math.Round(tile.Y * GridRows), 0, GridRows - 1));

    static bool InsideCell(int column, int row) =>
        column >= 0 && column < GridColumns && row >= 0 && row < GridRows;

    static string CellLabel(int column, int row) => $"{column + 1},{row + 1}";

    static IEnumerable<(int Column, int Row)> BrushCells(int column, int row)
    {
        for (var y = row - 1; y <= row + 1; y++)
            for (var x = column - 1; x <= column + 1; x++)
                if (InsideCell(x, y)) yield return (x, y);
    }

    static IEnumerable<(int Column, int Row)> LineCells(int x0, int y0, int x1, int y1)
    {
        var dx = Math.Abs(x1 - x0);
        var sx = x0 < x1 ? 1 : -1;
        var dy = -Math.Abs(y1 - y0);
        var sy = y0 < y1 ? 1 : -1;
        var error = dx + dy;
        while (true)
        {
            yield return (x0, y0);
            if (x0 == x1 && y0 == y1) break;
            var e2 = 2 * error;
            if (e2 >= dy) { error += dy; x0 += sx; }
            if (e2 <= dx) { error += dx; y0 += sy; }
        }
    }

    static IEnumerable<(int Column, int Row)> RectangleCells(int x0, int y0, int x1, int y1)
    {
        var left = Math.Min(x0, x1);
        var right = Math.Max(x0, x1);
        var top = Math.Min(y0, y1);
        var bottom = Math.Max(y0, y1);
        for (var x = left; x <= right; x++) { yield return (x, top); yield return (x, bottom); }
        for (var y = top + 1; y < bottom; y++) { yield return (left, y); yield return (right, y); }
    }

    static IEnumerable<(int Column, int Row)> CircleCells(int x0, int y0, int x1, int y1)
    {
        var rx = Math.Max(1, Math.Abs(x1 - x0));
        var ry = Math.Max(1, Math.Abs(y1 - y0));
        var cells = new HashSet<(int Column, int Row)>();
        const int samples = 144;
        for (var i = 0; i < samples; i++)
        {
            var angle = i * Math.PI * 2 / samples;
            var x = (int)Math.Round(x0 + rx * Math.Cos(angle));
            var y = (int)Math.Round(y0 + ry * Math.Sin(angle));
            if (InsideCell(x, y)) cells.Add((x, y));
        }
        return cells;
    }

    public void ResetBaseTerrainToOcean()
    {
        BaseTerrainOverrideTileId = "";
        WorldBuilderStatus = "Restored Ocean 071 as the implicit base terrain.";
        Notify();
    }
}
