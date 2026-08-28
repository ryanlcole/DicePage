namespace RistWorld;

public sealed partial class WorldSession
{
    // Giamaph test-world extent: flattened Earth-scale rectangle. One world tile = 1 mile.
    public const int GianaphEarthWidthMiles = 24901;
    public const int GianaphEarthHeightMiles = 12436;
    bool _giamaphResetApplied;

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

        // Current public-test reset: every browser/login starts from the same
        // canonical open-water surface at one mile per square. Existing saved
        // map state is intentionally discarded once when the map first mounts.
        GridDistance = 1;
        DistanceUnit = "mi";
        GridCalibrationZoom = 1;
        ViewZoom = 1;

        if (_giamaphResetApplied)
        {
            MapName = UsesOwnerEarthScale
                ? $"Giamaph · Earth-scale ocean · {GianaphEarthWidthMiles:N0}×{GianaphEarthHeightMiles:N0} mi"
                : "Giamaph";
            return;
        }

        _giamaphResetApplied = true;
        PlacedTiles.Clear();
        Pieces.Clear();
        Rolls.Clear();
        Gems.Clear();
        StagedAssets.Clear();
        MapName = UsesOwnerEarthScale
            ? $"Giamaph · Earth-scale ocean · {GianaphEarthWidthMiles:N0}×{GianaphEarthHeightMiles:N0} mi"
            : "Giamaph";
        BuildDefaultOceanSurface();
        MapLocked = true;
        Notify();
    }

    void BuildDefaultOceanSurface()
    {
        var waterTiles = GianaphPalette(AtlasTiles,
            "ocean", "open ocean", "sea", "water", "deep water", "deep-sea", "deep sea");

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
                    || text.Contains("sea", StringComparison.OrdinalIgnoreCase)
                    || text.Contains("water", StringComparison.OrdinalIgnoreCase);
            }).ToList();
        }

        if (waterTiles.Count == 0) return;

        // Only the visible 20×13 one-mile window is materialized. The owner's
        // Earth-scale logical world remains 24,901×12,436 miles without creating
        // hundreds of millions of DOM tiles.
        for (var row = 0; row < GridRows; row++)
        {
            for (var column = 0; column < GridColumns; column++)
            {
                var index = Math.Abs(GianaphSeed(column, row)) % waterTiles.Count;
                var tile = waterTiles[index];
                PlacedTiles.Add(new(tile.Id,
                    $"Giamaph · Ocean · {column + 1},{row + 1} · 1 mi²",
                    tile.Image,
                    column / (double)GridColumns,
                    row / (double)GridRows,
                    tile.SourceWidth, tile.SourceHeight,
                    tile.CropX, tile.CropY, tile.CropWidth, tile.CropHeight,
                    1,
                    Locked: true));
            }
        }
    }
}
