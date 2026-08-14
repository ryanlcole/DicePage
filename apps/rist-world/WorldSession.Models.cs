namespace RistWorld;

public sealed record AtlasTile(string Id, string Name, string Image);
public sealed record PieceItem(string Kind, double X, double Y, double PlacementZoom = 1.0);
public sealed record TileItem(string Id, string Name, string Image, double X, double Y);
public sealed record StagedAsset(string Key, string Kind, string Name, string Image = "");
public sealed record DiceSpec(string Key, string Label, string Image, int Sides, int Columns, int Rows, int FrameCount, int RestFrame, int ValueOffset = 1, int Sign = 1);
public sealed record RollItem(string Key, string Label, int Value, int Frame, double X, double Y);
public sealed record GemItem(int Value, double X, double Y);
public sealed record CardItem(string Id, string Name, string Type, string Text);
public sealed class MixerChannel(string name,int current,int max)
{
    public string Name { get; } = name;
    public int Current { get; set; } = current;
    public int Max { get; set; } = max;
}

public sealed class SavedWorld
{
    public string Role { get; set; } = "GM";
    public string Layer { get; set; } = "WORLD";
    public string GridStyle { get; set; } = "square";
    public string DistanceUnit { get; set; } = "mi";
    public int GridDiameter { get; set; } = 48;
    public double GridDistance { get; set; } = 5;
    public double GridCalibrationZoom { get; set; } = 1;
    public List<PieceItem> Pieces { get; set; } = [];
    public List<TileItem> Tiles { get; set; } = [];
}
