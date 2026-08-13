namespace RistWorld;

public sealed record AtlasTile(string Id, string Name, string Image);
public sealed record PieceItem(string Kind, double X, double Y);
public sealed record TileItem(string Id, string Name, string Image, double X, double Y);
public sealed record RollItem(string Label, int Value, double X, double Y);
public sealed record GemItem(int Value, double X, double Y);
public sealed record CardItem(string Id, string Name, string Type, string Text);

public sealed class SavedWorld
{
    public string Role { get; set; } = "GM";
    public string GridStyle { get; set; } = "square";
    public int GridDiameter { get; set; } = 48;
    public double GridDistance { get; set; } = 5;
    public List<PieceItem> Pieces { get; set; } = [];
    public List<TileItem> Tiles { get; set; } = [];
}
