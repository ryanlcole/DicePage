using Microsoft.JSInterop;

namespace RistWorld.Components;

public partial class WorldBuilderStudio
{
    /// <summary>
    /// Resolve a viewer tap against canonical world-space tile footprints.
    /// X/Y are normalized to the fixed viewer grid; Z is resolved from the
    /// tile's tier/layer through WorldSession.SceneZOf. The nearest visible
    /// tile to the current viewer Z wins, with later placement winning ties.
    /// </summary>
    [JSInvokable]
    public Task<int[]> SelectPlacedTileAtWorldPoint(double x, double y, bool additive)
    {
        if (!double.IsFinite(x) || !double.IsFinite(y) || x < 0 || x > 1 || y < 0 || y > 1)
        {
            if (!additive) ClearWorldBuilderSelection();
            return Task.FromResult(_selectedPlacedTileIndices.Order().ToArray());
        }

        var hitIndex = -1;
        var hitSceneZ = int.MinValue;
        var viewerSceneZ = Session.SceneZ;

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

            if (sceneZ > hitSceneZ || (sceneZ == hitSceneZ && index > hitIndex))
            {
                hitSceneZ = sceneZ;
                hitIndex = index;
            }
        }

        if (!additive)
            ClearWorldBuilderSelection();

        if (hitIndex >= 0)
        {
            if (additive && !_selectedPlacedTileIndices.Add(hitIndex))
                _selectedPlacedTileIndices.Remove(hitIndex);
            else
                _selectedPlacedTileIndices.Add(hitIndex);
        }

        return Task.FromResult(_selectedPlacedTileIndices.Order().ToArray());
    }
}
