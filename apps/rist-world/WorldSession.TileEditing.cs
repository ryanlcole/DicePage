namespace RistWorld;

public sealed partial class WorldSession
{
    int _editingTileIndex = -1;
    bool _tileLockArmed;

    public int EditingTileIndex => _editingTileIndex;
    public TileItem? EditingTile => _editingTileIndex >= 0 && _editingTileIndex < PlacedTiles.Count
        ? PlacedTiles[_editingTileIndex]
        : null;
    public bool HasEditingTile => EditingTile is { Locked: false };
    public bool TileLockArmed => HasEditingTile && _tileLockArmed;

    public void SelectTileForEditing(int index, bool rotateIfAlready = false)
    {
        if (!CanEditTiles || index < 0 || index >= PlacedTiles.Count) return;
        var tile = PlacedTiles[index];
        if (tile.Locked) return;

        if (_editingTileIndex == index)
        {
            if (rotateIfAlready) RotateEditingTileClockwise();
            return;
        }

        _editingTileIndex = index;
        _tileLockArmed = false;
        Notify();
    }

    public void SelectNewestTileForEditing()
    {
        if (!CanEditTiles || PlacedTiles.Count == 0) return;
        for (var index = PlacedTiles.Count - 1; index >= 0; index--)
        {
            if (PlacedTiles[index].Locked) continue;
            SelectTileForEditing(index);
            return;
        }
    }

    public void RotateEditingTileClockwise()
    {
        if (!TryEditingTile(out var index, out var tile)) return;
        PlacedTiles[index] = tile with { RotationQuarterTurns = (tile.RotationQuarterTurns + 1) % 4 };
        RecordPureStateCommit();
        _tileLockArmed = false;
        Notify();
    }

    public void NudgeEditingTile(double deltaX, double deltaY)
    {
        if (!TryEditingTile(out var index, out var tile)) return;
        var next = tile with
        {
            X = Math.Clamp(tile.X + deltaX, 0, 1),
            Y = Math.Clamp(tile.Y + deltaY, 0, 1)
        };
        if (IsPureStateNoOp(tile, next)) return;
        PlacedTiles[index] = next;
        RecordPureStateCommit();
        _tileLockArmed = false;
        Notify();
    }

    public void ResizeEditingTile(double visualFactor)
    {
        if (!TryEditingTile(out var index, out var tile) || visualFactor <= 0) return;
        var nextPlacementZoom = Math.Clamp(tile.PlacementZoom / visualFactor, 1.0 / 300.0, 300.0);
        var next = tile with { PlacementZoom = nextPlacementZoom };
        if (IsPureStateNoOp(tile, next)) return;
        PlacedTiles[index] = next;
        RecordPureStateCommit();
        _tileLockArmed = false;
        Notify();
    }

    public void ArmEditingTileLock()
    {
        if (!HasEditingTile || _tileLockArmed) return;
        _tileLockArmed = true;
        Notify();
    }

    public async Task LockEditingTileAsync()
    {
        if (!_tileLockArmed || !TryEditingTile(out var index, out var tile)) return;

        PlacedTiles[index] = tile with { Locked = true };
        RecordPureStateCommit();
        _editingTileIndex = -1;
        _tileLockArmed = false;
        Notify();

        // Lock is the explicit commit point. Always persist locally, then mirror
        // to private storage when the user is signed in. Truth conservation may
        // skip only a target already confirmed to contain this exact truth.
        await SaveAsync();
        await AutoSavePrivateAsync();
    }

    public void ClearEditingTile()
    {
        if (_editingTileIndex < 0 && !_tileLockArmed) return;
        _editingTileIndex = -1;
        _tileLockArmed = false;
        Notify();
    }

    bool TryEditingTile(out int index, out TileItem tile)
    {
        index = _editingTileIndex;
        if (index >= 0 && index < PlacedTiles.Count && !PlacedTiles[index].Locked)
        {
            tile = PlacedTiles[index];
            return true;
        }

        tile = default!;
        _editingTileIndex = -1;
        _tileLockArmed = false;
        return false;
    }
}
