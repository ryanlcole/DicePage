namespace RistWorld;

public sealed partial class WorldSession
{
    /// <summary>
    /// Describes the canonical Z address of every World Builder drawable that is
    /// already present in the composite page. The browser uses this metadata only
    /// for presentation: lower layers stay below the construction grid, the
    /// current layer sits above it, and higher layers are hidden until the viewer
    /// reaches their Z address. World truth remains in the normal tile/piece lists.
    /// </summary>
    public WorldBuilderLayerFrame GetWorldBuilderLayerFrame()
    {
        var tiles = PlacedTiles
            .Select((tile, index) => new WorldBuilderLayerItem(index, SceneZOf(tile)))
            .ToList();
        var pieces = Pieces
            .Select((piece, index) => new WorldBuilderLayerItem(index, SceneZOf(piece)))
            .ToList();

        return new WorldBuilderLayerFrame(tiles, pieces);
    }
}

public sealed record WorldBuilderLayerFrame(
    IReadOnlyList<WorldBuilderLayerItem> Tiles,
    IReadOnlyList<WorldBuilderLayerItem> Pieces);

public sealed record WorldBuilderLayerItem(int Index, int SceneZ);
