namespace RistWorld;

public sealed partial class WorldSession
{
    public IReadOnlyList<WorldBuilderUnderlayTile> GetWorldBuilderUnderlayTiles()
    {
        var currentSceneZ = SceneZ;
        return _terrainByAddress
            .Where(entry =>
                entry.Key.CubeX == CubeX &&
                entry.Key.CubeY == CubeY &&
                entry.Key.CubeZ == CubeZ &&
                entry.Key.PlaneIndex == PlaneIndex &&
                checked((entry.Key.TierIndex * LayersPerTier) + entry.Key.LayerOffset) < currentSceneZ)
            .OrderBy(entry => checked((entry.Key.TierIndex * LayersPerTier) + entry.Key.LayerOffset))
            .SelectMany(entry =>
            {
                var sceneZ = checked((entry.Key.TierIndex * LayersPerTier) + entry.Key.LayerOffset);
                return entry.Value.Select(tile => new WorldBuilderUnderlayTile(
                    tile.Image,
                    tile.X,
                    tile.Y,
                    tile.SourceWidth,
                    tile.SourceHeight,
                    tile.CropX,
                    tile.CropY,
                    tile.CropWidth,
                    tile.CropHeight,
                    tile.PlacementZoom,
                    tile.RotationQuarterTurns,
                    entry.Key.TierIndex,
                    entry.Key.LayerOffset,
                    sceneZ));
            })
            .ToList();
    }
}

public sealed record WorldBuilderUnderlayTile(
    string Image,
    double X,
    double Y,
    int SourceWidth,
    int SourceHeight,
    int CropX,
    int CropY,
    int CropWidth,
    int CropHeight,
    double PlacementZoom,
    int RotationQuarterTurns,
    int TierIndex,
    int LayerOffset,
    int SceneZ);
