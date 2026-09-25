using Microsoft.JSInterop;

namespace RistWorld.Components;

public partial class WorldBuilderStudio
{
    double _lastStackPickX = double.NaN;
    double _lastStackPickY = double.NaN;
    int _stackPickCursor;

    /// <summary>
    /// Resolve a viewer tap against world-space tile footprints. For
    /// RIST_RECURSIVE_SCOPE_V1 content, visual Layer is the front/back
    /// authority and Tier is deliberately excluded from ordinary draw order.
    /// Legacy content keeps its historical SceneZ ordering until migration.
    /// Repeated taps at the same world point cycle through the visible stack.
    /// </summary>
    [JSInvokable]
    public Task<int[]> SelectPlacedTileAtWorldPoint(double x, double y, bool additive)
    {
        EnsureWorldBuilderHistory();
        if (!double.IsFinite(x) || !double.IsFinite(y) || x < 0 || x > 1 || y < 0 || y > 1)
        {
            if (!additive) ClearWorldBuilderSelection();
            ResetStackPickCycle();
            return Task.FromResult(_selectedPlacedTileIndices.Order().ToArray());
        }

        var viewerSceneZ = Session.SceneZ;
        var hits = new List<WorldBuilderPickHit>();

        for (var index = 0; index < Session.PlacedTiles.Count; index++)
        {
            var tile = Session.PlacedTiles[index];

            if (tile.CubeX != Session.CubeX ||
                tile.CubeY != Session.CubeY ||
                tile.CubeZ != Session.CubeZ ||
                tile.PlaneIndex != Session.PlaneIndex)
                continue;

            var recursive = Session.RecursiveWorldPlacement(tile);
            if (recursive is { Visible: false })
                continue;

            var sceneZ = WorldSession.SceneZOf(tile);

            // Composite view renders the full depth stack. In a single-depth
            // compatibility view the viewer cutoff still determines whether a
            // tile can be hit, but never determines canonical visual front/back.
            if (!Session.CompositeZView && sceneZ > viewerSceneZ)
                continue;

            var footprint = AssetKeyboardFootprint(tile);
            var width = Math.Min(footprint.Width, WorldSession.GridColumns) / (double)WorldSession.GridColumns;
            var height = Math.Min(footprint.Height, WorldSession.GridRows) / (double)WorldSession.GridRows;

            const double epsilon = 1e-9;
            if (x + epsilon < tile.X || x - epsilon > tile.X + width ||
                y + epsilon < tile.Y || y - epsilon > tile.Y + height)
                continue;

            hits.Add(new WorldBuilderPickHit(
                index,
                recursive?.Layer ?? 1,
                sceneZ,
                recursive is not null));
        }

        hits.Sort((a, b) =>
        {
            var visual = b.VisualLayer.CompareTo(a.VisualLayer);
            if (visual != 0) return visual;

            // Only two legacy hits at the same compatibility Layer consult
            // SceneZ. Canonical Tier never participates in visual ordering.
            if (!a.Canonical && !b.Canonical)
            {
                var legacyDepth = b.LegacySceneZ.CompareTo(a.LegacySceneZ);
                if (legacyDepth != 0) return legacyDepth;
            }

            return b.Index.CompareTo(a.Index);
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

    sealed record WorldBuilderPickHit(
        int Index,
        int VisualLayer,
        int LegacySceneZ,
        bool Canonical);
}
