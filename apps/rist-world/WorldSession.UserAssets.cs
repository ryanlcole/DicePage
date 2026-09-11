namespace RistWorld;

public sealed partial class WorldSession
{
    public List<AtlasTile> UserAssetTiles { get; } = [];

    public void ReplaceUserAssetTiles(IEnumerable<AtlasTile> tiles)
    {
        UserAssetTiles.Clear();
        UserAssetTiles.AddRange(tiles);
        Notify();
    }
}
