using Microsoft.JSInterop;

namespace RistWorld.Components;

public partial class WorldBuilderStudio
{
    /// <summary>
    /// Canonical World Builder picker. The viewer supplies a normalized world-space X/Y point;
    /// the world model decides which placed tile occupies that point. DOM stacking is not authoritative.
    /// </summary>
    [JSInvokable]
    public Task<int[]> SelectPlacedTileAtWorldPoint(double worldX, double worldY, bool additive)
    {
        worldX = Math.Clamp(worldX, 0d, 1d);
        worldY = Math.Clamp(worldY, 0d, 1d);

        var candidates = Session.PlacedTiles
            .Select((tile, index) => new
            {
                Tile = tile,
                Index = index,
                Footprint = FootprintFor(tile)
            })
            .Where(x =>
                x.Tile.PlaneIndex == Session.PlaneIndex &&
                x.Tile.CubeX == Session.CubeX &&
                x.Tile.CubeY == Session.CubeY &&
                x.Tile.CubeZ == Session.CubeZ)
            .Where(x =>
            {
                var width = x.Footprint / (double)WorldSession.GridColumns;
                var height = x.Footprint / (double)WorldSession.GridRows;
                return worldX >= x.Tile.X && worldX < x.Tile.X + width &&
                       worldY >= x.Tile.Y && worldY < x.Tile.Y + height;
            })
            // Mahjong/parallax rule: nearest visible surface wins. Tier and layer are
            // world depth authorities; insertion order only breaks an exact depth tie.
            .OrderByDescending(x => x.Tile.TierIndex)
            .ThenByDescending(x => x.Tile.LayerOffset)
            .ThenByDescending(x => x.Index)
            .ToArray();

        if (!additive)
            _selectedPlacedTileIndices.Clear();

        if (candidates.Length == 0)
            return Task.FromResult(_selectedPlacedTileIndices.Order().ToArray());

        var picked = candidates[0].Index;
        if (additive && _selectedPlacedTileIndices.Contains(picked))
            _selectedPlacedTileIndices.Remove(picked);
        else
            _selectedPlacedTileIndices.Add(picked);

        return Task.FromResult(_selectedPlacedTileIndices.Order().ToArray());
    }
}
