using Microsoft.JSInterop;

namespace RistWorld.Components;

public partial class WorldBuilderStudio
{
    double _lastStackPickX = double.NaN;
    double _lastStackPickY = double.NaN;
    int _stackPickCursor;

    /// <summary>
    /// Resolve a viewer tap against canonical world-space tile footprints.
    /// X/Y are normalized to the fixed viewer grid; Z is resolved from the
    /// tile's tier/layer through WorldSession.SceneZOf. The frontmost visible
    /// tile wins on the first tap. Repeated taps at the same world point cycle
    /// down through every visible tile in the stack, then wrap to the top.
    /// </summary>
    [JSInvokable]
    public Task<int[]> SelectPlacedTileAtWorldPoint(double x, double y, bool additive)
    {
        if (!double.IsFinite(x) || !double.IsFinite(y) || x < 0 || x > 1 || y < 0 || y > 1)
        {
            if (!additive) ClearWorldBuilderSelection();
            ResetStackPickCycle();
            return Task.FromResult(_selectedPlacedTileIndices.Order().ToArray());
        }

        var viewerSceneZ = Session.SceneZ;
        var hits = new List<(int Index, int SceneZ)>();

        for (var index = 0; index < Session.PlacedTiles.Count; index++)
        {
            var tile = Session.PlacedTiles[index];

            if (tile.CubeX != Session.CubeX ||
                tile.CubeY != Session.CubeY ||
                tile.CubeZ != Session.CubeZ ||
                tile.PlaneIndex != Session.PlaneIndex)
                continue;

            var sceneZ = WorldSession.SceneZOf(tile);
            if (sceneZ > viewerSceneZ)
                continue;

            var footprint = FootprintFor(tile);
            var width = Math.Min(footprint, WorldSession.GridColumns) / (double)WorldSession.GridColumns;
            var height = Math.Min(footprint, WorldSession.GridRows) / (double)WorldSession.GridRows;

            const double epsilon = 1e-9;
            if (x + epsilon < tile.X || x - epsilon > tile.X + width ||
                y + epsilon < tile.Y || y - epsilon > tile.Y + height)
                continue;

            hits.Add((index, sceneZ));
        }

        hits.Sort((a, b) =>
        {
            var depth = b.SceneZ.CompareTo(a.SceneZ);
            return depth != 0 ? depth : b.Index.CompareTo(a.Index);
        });

        if (!additive)
            ClearWorldBuilderSelection();

        if (hits.Count == 0)
        {
            ResetStackPickCycle();
            return Task.FromResult(_selectedPlacedTileIndices.Order().ToArray());
        }

        // Treat taps within roughly three quarters of a viewer cell as the
        // same stack pick. This is forgiving enough for phones without making
        // neighboring grid cells share a selection cycle.
        var toleranceX = 0.75 / WorldSession.GridColumns;
        var toleranceY = 0.75 / WorldSession.GridRows;
        var samePoint = !additive &&
                        double.IsFinite(_lastStackPickX) &&
                        Math.Abs(x - _lastStackPickX) <= toleranceX &&
                        Math.Abs(y - _lastStackPickY) <= toleranceY;

        if (!samePoint)
            _stackPickCursor = 0;
        else
            _stackPickCursor = (_stackPickCursor + 1) % hits.Count;

        _lastStackPickX = x;
        _lastStackPickY = y;

        var hitIndex = hits[Math.Clamp(_stackPickCursor, 0, hits.Count - 1)].Index;
        if (additive && !_selectedPlacedTileIndices.Add(hitIndex))
            _selectedPlacedTileIndices.Remove(hitIndex);
        else
            _selectedPlacedTileIndices.Add(hitIndex);

        return Task.FromResult(_selectedPlacedTileIndices.Order().ToArray());
    }

    void ResetStackPickCycle()
    {
        _lastStackPickX = double.NaN;
        _lastStackPickY = double.NaN;
        _stackPickCursor = 0;
    }
}
