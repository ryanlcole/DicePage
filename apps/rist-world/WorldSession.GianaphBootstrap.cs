namespace RistWorld;

public sealed partial class WorldSession
{
    // Owner world extent: flattened Earth-scale rectangle. One world tile = 1 mile.
    // The dimensions use Earth's equatorial circumference and pole-to-pole half-circumference,
    // which keeps the canvas approximately 2:1 like a flat equirectangular world map.
    public const int GianaphEarthWidthMiles = 24901;
    public const int GianaphEarthHeightMiles = 12436;
    public bool UsesOwnerEarthScale => auth.IsOwnerDiscordAccount;
    public int GianaphWorldWidthMiles => UsesOwnerEarthScale ? GianaphEarthWidthMiles : GridColumns;
    public int GianaphWorldHeightMiles => UsesOwnerEarthScale ? GianaphEarthHeightMiles : GridRows;
    public long GianaphWorldTileCapacity => (long)GianaphWorldWidthMiles * GianaphWorldHeightMiles;
    public string GianaphWorldExtentLabel => UsesOwnerEarthScale
        ? $"{GianaphEarthWidthMiles:N0}×{GianaphEarthHeightMiles:N0} mi · 1 mi/tile"
        : $"{GridColumns}×{GridRows} mi · 1 mi/tile";

    public void EnsureGianaphWorld()
    {
        if (AtlasTiles.Count == 0) return;

        // The shared AWS world begins as open ocean. Public visitors and ordinary
        // authenticated accounts keep the lightweight 20×13 water viewport.
        // The owner account receives an Earth-scale logical ocean canvas while
        // still rendering only the current 20×13 tile window at one mile per tile.
        // This avoids materializing ~310 million DOM/image tiles at once.
        GridDistance = 1;
        DistanceUnit = "mi";
        GridCalibrationZoom = 1;

        if (PlacedTiles.Count > 0 && PlacedTiles.All(tile =>
                tile.Name.StartsWith("Gianaph · Ocean ·", StringComparison.OrdinalIgnoreCase)))
        {
            MapName = UsesOwnerEarthScale
                ? $"Gianaph · Earth-scale ocean · {GianaphEarthWidthMiles:N0}×{GianaphEarthHeightMiles:N0} mi"
                : "Gianaph";
            return;
        }

        // Replace only old generated defaults (legacy Naeja or the temporary
        // generated Pangea). Never erase a map the user has actually authored.
        var isLegacyDefault = PlacedTiles.Count == 0
            || PlacedTiles.All(tile => tile.Id.StartsWith("naeja-map-", StringComparison.OrdinalIgnoreCase))
            || PlacedTiles.All(tile => tile.Name.StartsWith("Gianaph · State ", StringComparison.OrdinalIgnoreCase));

        if (!isLegacyDefault) return;

        PlacedTiles.Clear();
        MapName = UsesOwnerEarthScale
            ? $"Gianaph · Earth-scale ocean · {GianaphEarthWidthMiles:N0}×{GianaphEarthHeightMiles:N0} mi"
            : "Gianaph";
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

        // Render one 20×13 tile window. For the owner account, this is a movable
        // window into the 24,901×12,436-mile logical world rather than the full world.
        for (var row = 0; row < GridRows; row++)
        {
            for (var column = 0; column < GridColumns; column++)
            {
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
