namespace RistWorld;

public sealed partial class WorldSession
{
    public void EnsureGianaphWorld()
    {
        if (AtlasTiles.Count == 0) return;

        // The shared AWS world now begins as open ocean for everyone: public
        // visitors and authenticated users see the same neutral starting surface.
        // A tile at this view represents one square mile.
        GridDistance = 1;
        DistanceUnit = "mi";
        GridCalibrationZoom = 1;

        if (PlacedTiles.Count > 0 && PlacedTiles.All(tile =>
                tile.Name.StartsWith("Gianaph · Ocean ·", StringComparison.OrdinalIgnoreCase)))
        {
            MapName = "Gianaph";
            return;
        }

        // Replace only old generated defaults (legacy Naeja or the temporary
        // generated Pangea). Never erase a map the user has actually authored.
        var isLegacyDefault = PlacedTiles.Count == 0
            || PlacedTiles.All(tile => tile.Id.StartsWith("naeja-map-", StringComparison.OrdinalIgnoreCase))
            || PlacedTiles.All(tile => tile.Name.StartsWith("Gianaph · State ", StringComparison.OrdinalIgnoreCase));

        if (!isLegacyDefault) return;

        PlacedTiles.Clear();
        MapName = "Gianaph";
        BuildDefaultOceanSurface();
    }

    void BuildDefaultOceanSurface()
    {
        var waterTiles = GianaphPalette(AtlasTiles,
            "ocean", "open ocean", "sea", "water", "deep water", "deep-sea", "deep sea");

        // Avoid accidental shoreline/river artwork when a broad word such as
        // "water" matches transition assets.
        waterTiles = waterTiles.Where(tile =>
        {
            var text = $"{tile.Id} {tile.Name} {tile.Directory} {tile.Folder}";
            return !text.Contains("coast", StringComparison.OrdinalIgnoreCase)
                && !text.Contains("beach", StringComparison.OrdinalIgnoreCase)
                && !text.Contains("shore", StringComparison.OrdinalIgnoreCase)
                && !text.Contains("river", StringComparison.OrdinalIgnoreCase)
                && !text.Contains("swamp", StringComparison.OrdinalIgnoreCase)
                && !text.Contains("marsh", StringComparison.OrdinalIgnoreCase);
        }).ToList();

        if (waterTiles.Count == 0)
        {
            waterTiles = AtlasTiles.Where(tile =>
            {
                var text = $"{tile.Id} {tile.Name} {tile.Directory} {tile.Folder}";
                return text.Contains("ocean", StringComparison.OrdinalIgnoreCase)
                    || text.Contains("sea", StringComparison.OrdinalIgnoreCase);
            }).ToList();
        }

        if (waterTiles.Count == 0) return;

        for (var row = 0; row < GridRows; row++)
        {
            for (var column = 0; column < GridColumns; column++)
            {
                // Deterministic variation keeps the surface from looking stamped
                // while remaining entirely water.
                var index = Math.Abs(GianaphSeed(column, row)) % waterTiles.Count;
                var tile = waterTiles[index];
                PlacedTiles.Add(new(tile.Id,
                    $"Gianaph · Ocean · {column + 1},{row + 1} · 1 mi²",
                    tile.Image,
                    column / (double)GridColumns,
                    row / (double)GridRows,
                    tile.SourceWidth, tile.SourceHeight,
                    tile.CropX, tile.CropY, tile.CropWidth, tile.CropHeight,
                    1,
                    Locked: true));
            }
        }

        MapLocked = true;
    }
}
