namespace RistWorld;

public sealed record AtlasTile(
    string Id,
    string Name,
    string Image,
    string Layer = "UNIVERSAL",
    string Directory = "Tiles",
    string Folder = "General",
    string Author = "Shaelvien");
public sealed record PieceItem(string Kind, double X, double Y, double PlacementZoom = 1.0);
public sealed record TileItem(string Id, string Name, string Image, double X, double Y);
public sealed record StagedAsset(string Key, string Kind, string Name, string Image = "");
public sealed record DiceSpec(string Key, string Label, string Image, int Sides, int Columns, int Rows, int FrameCount, int RestFrame, int ValueOffset = 1, int Sign = 1, double VisualAspect = 1.0);
public sealed record RollItem(string Key, string Label, int Value, int Frame, double X, double Y);
public sealed record GemItem(int Value, double X, double Y);
public sealed record CardItem(string Id, string Name, string Type, string Text);
public sealed record CharacterFieldOption(string Name, string Kind, string Group);

public sealed class CharacterField(string name,string kind,string group)
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string Name { get; set; } = name;
    public string Kind { get; set; } = kind;
    public string Group { get; set; } = group;
    public int BaseValue { get; set; }
    public int Current { get; set; }
    public int Max { get; set; } = kind switch { "TRACKER" or "TRACK" or "POOL" => 100, "ATTRIBUTE" or "LIMIT" => 10, "FLARE" => 0, _ => 999 };
    public string Color { get; set; } = "gold";
    public string Description { get; set; } = "";
    public string NameplateDescription { get; set; } = "";
    public string Subtitle { get; set; } = "";
    public bool DescriptionEnabled { get; set; } = true;
    public string ImageDataUrl { get; set; } = "";
    public string ShortName { get; set; } = AutoShortName(name);
    public bool ShortNameOverridden { get; set; }
    public List<DiceBagEntry> DiceBag { get; } = [];

    public static string AutoShortName(string? value)
    {
        var cleaned = new string((value ?? "").Trim().Where(char.IsLetterOrDigit).Take(3).ToArray());
        return cleaned.ToUpperInvariant();
    }

    public void Rename(string? value)
    {
        Name = value?.Trim() ?? "";
        if (!ShortNameOverridden) ShortName = AutoShortName(Name);
    }

    public void SetShortName(string? value)
    {
        var cleaned = new string((value ?? "").Trim().Where(char.IsLetterOrDigit).Take(3).ToArray()).ToUpperInvariant();
        ShortName = cleaned;
        ShortNameOverridden = !string.Equals(cleaned, AutoShortName(Name), StringComparison.Ordinal);
    }

    public void ResetShortName()
    {
        ShortNameOverridden = false;
        ShortName = AutoShortName(Name);
    }
}

public sealed class DiceBagEntry(string dieKey,int count=1,int selectedMagnitude=1)
{
    public string DieKey { get; set; } = dieKey;
    public int Count { get; set; } = Math.Clamp(count,1,20);
    public int SelectedMagnitude { get; set; } = Math.Clamp(selectedMagnitude,1,5);
}

public sealed class HandCard(CharacterField field)
{
    public string Id { get; } = Guid.NewGuid().ToString("N");
    public CharacterField Field { get; } = field;
    public List<DiceBagEntry> DiceBag => Field.DiceBag;
    public string Name => Field.Name;
    public string ShortName => string.IsNullOrWhiteSpace(Field.ShortName) ? CharacterField.AutoShortName(Field.Name) : Field.ShortName;
    public string Subtitle => Field.Subtitle;
    public string Type => WorldSession.IsTrackerField(Field) ? "Tracker" : WorldSession.IsAttributeField(Field) ? "Attribute" : WorldSession.IsLimitField(Field) ? "Limit" : Field.Group == "Skills" ? "Skill" : WorldSession.IsFlareField(Field) ? "Flare" : Field.Group;
    public int Value => Field.Current;
    public int BaseValue => Field.BaseValue;
    public int Max => Field.Max;
}

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
