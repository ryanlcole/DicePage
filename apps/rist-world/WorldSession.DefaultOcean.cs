namespace RistWorld;

public sealed partial class WorldSession
{
    public const int DefaultOceanColumns = 30;
    public const int DefaultOceanRows = 30;

    public bool ReplaceDefaultMapWithRandomOcean30()
    {
        if (AtlasTiles.Count == 0) return false;
        if (PlacedTiles.Count > 0 && PlacedTiles.All(tile => tile.Id.StartsWith("default-ocean-", StringComparison.Ordinal)))
        {
            GridStyle = "square";
            DistanceUnit = "mi";
            GridDistance = 1;
            GridCalibrationZoom = 1;
            return false;
        }

        var existingIsDefault = PlacedTiles.Count == 0 ||
            PlacedTiles.All(tile => tile.Id.StartsWith("naeja-map-", StringComparison.Ordinal));
        if (!existingIsDefault) return false;

        var oceanTiles = AtlasTiles
            .Where(tile => tile.Name.Contains("ocean", StringComparison.OrdinalIgnoreCase) ||
                           tile.Folder.Contains("ocean", StringComparison.OrdinalIgnoreCase))
            .Where(tile => !string.IsNullOrWhiteSpace(tile.Image))
            .ToList();
        if (oceanTiles.Count == 0) return false;

        PlacedTiles.Clear();
        Pieces.Clear();
        GridStyle = "square";
        DistanceUnit = "mi";
        GridDistance = 1;
        GridCalibrationZoom = 1;
        ViewZoom = 1;

        for (var row = 0; row < DefaultOceanRows; row++)
        {
            for (var column = 0; column < DefaultOceanColumns; column++)
            {
                var source = oceanTiles[Random.Shared.Next(oceanTiles.Count)];
                var id = $"default-ocean-{row:D2}-{column:D2}-{source.Id}";
                PlacedTiles.Add(new TileItem(
                    id,
                    source.Name,
                    source.Image,
                    column / (double)DefaultOceanColumns,
                    row / (double)DefaultOceanRows,
                    source.SourceWidth,
                    source.SourceHeight,
                    source.CropX,
                    source.CropY,
                    source.CropWidth,
                    source.CropHeight,
                    1,
                    Locked: true));
            }
        }

        MapLocked = true;
        Notify();
        return true;
    }
}
