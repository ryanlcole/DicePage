namespace RistWorld;

public sealed partial class WorldSession
{
    public void EnsureGianaphWorld()
    {
        if (AtlasTiles.Count == 0) return;
        if (MapName.Equals("Gianaph", StringComparison.OrdinalIgnoreCase) && PlacedTiles.Count > 0) return;

        // Preserve authored/custom maps. Replace only the legacy default Naeja
        // tilemap (or an empty map) when Gianaph becomes the world default.
        if (PlacedTiles.Count > 0 && PlacedTiles.Any(tile =>
                !tile.Id.StartsWith("naeja-map-", StringComparison.OrdinalIgnoreCase)))
            return;

        PlacedTiles.Clear();
        MapName = "Gianaph";
        BuildGianaphWorld();
    }
}
