namespace RistWorld;

public sealed partial class WorldSession
{
    public const int GianaphStateColumns = 20;
    public const int GianaphStateRows = 13;
    public const int GianaphStatesAcross = 4;
    public const int GianaphStatesDown = 4;
    public const int GianaphTierStride = 5;
    public const int GianaphTierGap = 4;

    public List<GianaphCell> GianaphCells { get; } = [];
    public IReadOnlyList<GianaphLayerSpec> GianaphLayers { get; } =
    [
        new(-1, 1, -5, "Ocean floor"),
        new( 1, 1,  0, "Ocean surface"),
        new( 1, 2,  1, "Beach / shore"),
        new( 2, 1,  5, "Land"),
        new( 2, 2,  6, "Raised land / hills"),
        new( 2, 3,  7, "Mountains / high terrain")
    ];

    public static int GianaphLayerZ(int tier, int layer)
    {
        if (layer < 1) throw new ArgumentOutOfRangeException(nameof(layer));
        var tierBase = tier < 0 ? tier * GianaphTierStride : (tier - 1) * GianaphTierStride;
        return tierBase + layer - 1;
    }

    void BuildGianaphWorld()
    {
        if (PlacedTiles.Count > 0) return;

        MapName = "Gianaph";
        GianaphCells.Clear();

        const int worldColumns = GianaphStateColumns * GianaphStatesAcross;
        const int worldRows = GianaphStateRows * GianaphStatesDown;
        const double placementZoom = GianaphStatesAcross;

        var terrainTiles = AtlasTiles
            .Where(t => !t.Id.StartsWith("naeja-map-", StringComparison.OrdinalIgnoreCase))
            .Where(t => t.Layer.Equals("WORLD", StringComparison.OrdinalIgnoreCase)
                     || t.Directory.Contains("Terrain", StringComparison.OrdinalIgnoreCase)
                     || t.Folder.Contains("Terrain", StringComparison.OrdinalIgnoreCase))
            .GroupBy(t => t.Id, StringComparer.OrdinalIgnoreCase)
            .Select(g => g.First())
            .ToList();

        if (terrainTiles.Count == 0)
        {
            terrainTiles = AtlasTiles
                .Where(t => !t.Id.StartsWith("naeja-map-", StringComparison.OrdinalIgnoreCase))
                .GroupBy(t => t.Id, StringComparer.OrdinalIgnoreCase)
                .Select(g => g.First())
                .ToList();
        }
        if (terrainTiles.Count == 0) return;

        var ocean = GianaphPalette(terrainTiles, "ocean", "sea", "water", "deep", "blue");
        var shore = GianaphPalette(terrainTiles, "coast", "beach", "shore", "sand", "cliff");
        var wet = GianaphPalette(terrainTiles, "river", "swamp", "pond", "lake", "bridge", "marsh");
        var high = GianaphPalette(terrainTiles, "mountain", "hill", "volcano", "ice", "snow", "ridge");
        var forest = GianaphPalette(terrainTiles, "forest", "woods", "tree", "jungle", "glade");
        var settled = GianaphPalette(terrainTiles, "city", "town", "village", "road", "farm", "building", "crossroad", "maze", "interior");
        var generalLand = terrainTiles
            .Where(t => !ocean.Contains(t) && !shore.Contains(t))
            .ToList();
        if (generalLand.Count == 0) generalLand = terrainTiles;

        var roleCounters = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
        AtlasTile Next(string role, List<AtlasTile> palette, int seed)
        {
            if (palette.Count == 0) palette = terrainTiles;
            roleCounters.TryGetValue(role, out var counter);
            roleCounters[role] = counter + 1;
            return palette[Math.Abs(counter + seed) % palette.Count];
        }

        // Generation order is state-by-state. Each 20x13 block is one state-sized
        // area; after a block is complete the builder moves to the next state.
        for (var stateRow = 0; stateRow < GianaphStatesDown; stateRow++)
        {
            for (var stateColumn = 0; stateColumn < GianaphStatesAcross; stateColumn++)
            {
                for (var localRow = 0; localRow < GianaphStateRows; localRow++)
                {
                    for (var localColumn = 0; localColumn < GianaphStateColumns; localColumn++)
                    {
                        var column = stateColumn * GianaphStateColumns + localColumn;
                        var row = stateRow * GianaphStateRows + localRow;
                        var nx = (column + .5) / worldColumns * 2.0 - 1.0;
                        var ny = (row + .5) / worldRows * 2.0 - 1.0;
                        var seed = GianaphSeed(column, row);
                        var land = GianaphLandField(nx, ny, seed) > 0.0;
                        var coast = land && IsGianaphCoast(column, row, worldColumns, worldRows);
                        var latitude = Math.Abs(ny);
                        var mountainBand = land && Math.Abs(ny - (.48 * nx + .02)) < .11 + ((seed >> 5) & 7) * .006;
                        var wetland = land && !coast && ((seed % 29 == 0) || (nx > .18 && ny > .12 && ny < .55 && seed % 11 == 0));
                        var wooded = land && !coast && !mountainBand && (latitude > .28 || seed % 5 <= 1);
                        var settlement = land && !coast && !mountainBand && seed % 17 == 0;

                        // Tier -1, layer 1: ocean floor at z=-5. The tier data is
                        // retained even when the surface overview is showing.
                        var floorTile = Next("floor", ocean.Count > 0 ? ocean : terrainTiles, seed);
                        GianaphCells.Add(new(column, row, stateColumn, stateRow, -1, 1, GianaphLayerZ(-1, 1), "Ocean floor", floorTile.Id));

                        AtlasTile visible;
                        int tier;
                        int layer;
                        int z;
                        string terrain;

                        if (!land)
                        {
                            visible = Next("ocean", ocean.Count > 0 ? ocean : terrainTiles, seed);
                            tier = 1; layer = 1; z = GianaphLayerZ(1, 1); terrain = "Ocean surface";
                        }
                        else if (coast)
                        {
                            visible = Next("shore", shore.Count > 0 ? shore : generalLand, seed);
                            tier = 1; layer = 2; z = GianaphLayerZ(1, 2); terrain = "Beach / shore";
                        }
                        else if (mountainBand)
                        {
                            visible = Next("high", high.Count > 0 ? high : generalLand, seed);
                            tier = 2; layer = 3; z = GianaphLayerZ(2, 3); terrain = "Mountain / high terrain";
                        }
                        else if (wetland)
                        {
                            visible = Next("wet", wet.Count > 0 ? wet : generalLand, seed);
                            tier = 2; layer = 1; z = GianaphLayerZ(2, 1); terrain = "River / wetland";
                        }
                        else if (settlement)
                        {
                            visible = Next("settled", settled.Count > 0 ? settled : generalLand, seed);
                            tier = 2; layer = 1; z = GianaphLayerZ(2, 1); terrain = "Settlement / road";
                        }
                        else if (wooded)
                        {
                            visible = Next("forest", forest.Count > 0 ? forest : generalLand, seed);
                            tier = 2; layer = 2; z = GianaphLayerZ(2, 2); terrain = "Forest / raised land";
                        }
                        else
                        {
                            // Rotate the full usable land palette here so no tileset
                            // becomes a forgotten island of assets as Gianaph grows.
                            visible = Next("land", generalLand, seed);
                            tier = 2; layer = 1; z = GianaphLayerZ(2, 1); terrain = "Land";
                        }

                        GianaphCells.Add(new(column, row, stateColumn, stateRow, tier, layer, z, terrain, visible.Id));
                        PlacedTiles.Add(new(visible.Id,
                            $"Gianaph · State {stateRow * GianaphStatesAcross + stateColumn + 1:00} · {terrain} · z={z}",
                            visible.Image,
                            column / (double)worldColumns,
                            row / (double)worldRows,
                            visible.SourceWidth, visible.SourceHeight,
                            visible.CropX, visible.CropY, visible.CropWidth, visible.CropHeight,
                            placementZoom,
                            Locked: true));
                    }
                }
            }
        }

        MapLocked = true;
    }

    static List<AtlasTile> GianaphPalette(IEnumerable<AtlasTile> source, params string[] words)
        => source.Where(tile =>
        {
            var text = $"{tile.Id} {tile.Name} {tile.Directory} {tile.Folder}";
            return words.Any(word => text.Contains(word, StringComparison.OrdinalIgnoreCase));
        }).ToList();

    static int GianaphSeed(int column, int row)
    {
        unchecked
        {
            var value = column * 73856093 ^ row * 19349663 ^ 0x5A17BEEF;
            value ^= value << 13;
            value ^= value >> 17;
            value ^= value << 5;
            return value & 0x7fffffff;
        }
    }

    static bool IsGianaphCoast(int column, int row, int width, int height)
    {
        for (var dy = -1; dy <= 1; dy++)
        for (var dx = -1; dx <= 1; dx++)
        {
            if (dx == 0 && dy == 0) continue;
            var x = column + dx;
            var y = row + dy;
            if (x < 0 || y < 0 || x >= width || y >= height) return true;
            var nx = (x + .5) / width * 2.0 - 1.0;
            var ny = (y + .5) / height * 2.0 - 1.0;
            if (GianaphLandField(nx, ny, GianaphSeed(x, y)) <= 0.0) return true;
        }
        return false;
    }

    static double GianaphLandField(double x, double y, int seed)
    {
        static double Ellipse(double px, double py, double cx, double cy, double rx, double ry)
        {
            var dx = (px - cx) / rx;
            var dy = (py - cy) / ry;
            return 1.0 - dx * dx - dy * dy;
        }

        // One connected Pangea-like supercontinent with asymmetrical lobes,
        // peninsulas, inland bites and a long southern taper.
        var field = Math.Max(
            Ellipse(x, y, -.10, -.04, .62, .58),
            Math.Max(Ellipse(x, y, -.48, -.34, .34, .30), Ellipse(x, y, .42, -.25, .34, .28)));
        field = Math.Max(field, Ellipse(x, y, -.28, .42, .35, .34));
        field = Math.Max(field, Ellipse(x, y, .28, .42, .30, .40));
        field = Math.Max(field, Ellipse(x, y, .04, .72, .24, .28));
        field = Math.Max(field, Ellipse(x, y, -.67, .06, .20, .25));

        var gulf = Ellipse(x, y, .48, .13, .25, .22);
        if (gulf > .15) field -= gulf * .48;
        var westernBite = Ellipse(x, y, -.63, .25, .18, .18);
        if (westernBite > .2) field -= westernBite * .28;

        var noise = ((seed % 2001) - 1000) / 1000.0;
        return field + noise * .075 - .025;
    }
}

public sealed record GianaphLayerSpec(int Tier, int Layer, int Z, string Name);
public sealed record GianaphCell(int Column, int Row, int StateColumn, int StateRow, int Tier, int Layer, int Z, string Terrain, string AtlasTileId);
