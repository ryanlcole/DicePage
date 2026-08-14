using System.Net.Http.Json;
using Microsoft.JSInterop;

namespace RistWorld;

public sealed partial class WorldSession(HttpClient http, IJSRuntime js)
{
    private const string SaveKey = "rist.world.blazor.v1";
    public event Action? Changed;
    public List<AtlasTile> AtlasTiles { get; } = [];
    public List<CardItem> Cards { get; } = [];
    public List<PieceItem> Pieces { get; private set; } = [];
    public List<TileItem> PlacedTiles { get; private set; } = [];
    public List<StagedAsset> StagedAssets { get; } = [];
    public List<RollItem> Rolls { get; } = [];
    public List<GemItem> Gems { get; } = [];

    public string WorldMapUrl { get; } = "assets/world/naeja.png";

    public IReadOnlyList<DiceSpec> DiceSet { get; } =
    [
        new("d4", "D4", "assets/dice/d4.png", 4, 8, 1, 8, 6, VisualAspect:1.06),
        new("d5-bonus", "+D5", "assets/dice/d5-bonus.png", 5, 10, 1, 10, 8, VisualAspect:.77),
        new("d5-penalty", "-D5", "assets/dice/d5-penalty.png", 5, 10, 1, 10, 8, 1, -1, .73),
        new("d6", "D6", "assets/dice/d6.png", 6, 12, 1, 12, 10, VisualAspect:.83),
        new("d8", "D8", "assets/dice/d8.png", 8, 16, 1, 16, 14, VisualAspect:.92),
        new("d10", "D10", "assets/dice/d10.png", 10, 10, 2, 20, 18, 0, 1, .87),
        new("d10-inverse", "D10 dark", "assets/dice/d10-inverse.png", 10, 10, 2, 20, 18, 0, 1, .88),
        new("d12", "D12", "assets/dice/d12.png", 12, 12, 2, 24, 22, VisualAspect:.92),
        new("d20", "D20", "assets/dice/d20.png", 20, 10, 4, 40, 38, VisualAspect:.79)
    ];

    public int BonusD5Value { get; set; } = 1;
    public int PenaltyD5Value { get; set; } = 1;

    public bool MixerOpen { get; set; }
    public string CharacterName { get; set; } = "";
    public string CharacterSpecies { get; set; } = "";
    public string CharacterAge { get; set; } = "";
    public string CharacterAlignment { get; set; } = "";
    public string CharacterDescription { get; set; } = "";
    public List<MixerChannel> MixerChannels { get; } =
    [
        new("Knowledge", 0, 20),
        new("Swim", 0, 20),
        new("Perception", 0, 20),
        new("Athletics", 0, 20),
        new("Stealth", 0, 20),
        new("Insight", 0, 20),
        new("Survival", 0, 20),
        new("Craft", 0, 20)
    ];

    public string SelectedTile { get; set; } = "";
    public string PieceKind { get; set; } = "pin";
    public string Role { get; set; } = "GM";
    public string GridStyle { get; set; } = "square";
    public string DistanceUnit { get; private set; } = "mi";
    public const int GridColumns = 20;
    public const int GridRows = 20;
    public int GridDiameter { get; set; } = 48;
    public double GridDistance { get; set; } = 5;
    public double GridCalibrationZoom { get; set; } = 1;
    public double ViewZoom { get; set; } = 1;
    public double GridCellWidthPercent => 100.0 / GridColumns;
    public double GridCellHeightPercent => 100.0 / GridRows;
    public double EffectiveGridDistance => GridDistance * GridCalibrationZoom / Math.Max(ViewZoom, 0.01);
    public string EffectiveGridUnit => DistanceUnit;
    public string Mode { get; set; } = "piece";
    public CardItem? OpenCard { get; set; }
    public int Total => Rolls.Sum(x => x.Value) + Gems.Sum(x => x.Value);
    public void Notify() => Changed?.Invoke();
    public void CalibrateGrid(){GridDistance=Math.Max(0.01,GridDistance);GridCalibrationZoom=Math.Max(0.01,ViewZoom);Notify();}

    public void OpenMixer(){MixerOpen=true;Notify();}
    public void CloseMixer(){MixerOpen=false;Notify();}
    public void SetMixerChannel(string name,int current,int max)
    {
        var channel=MixerChannels.FirstOrDefault(x=>x.Name==name);
        if(channel is null)return;
        max=Math.Clamp(max,0,999);
        current=Math.Clamp(current,0,max);
        channel.Current=current;
        channel.Max=max;
        Notify();
    }

    public void SetDistanceUnit(string unit)
    {
        if (EncounterActive) return;
        unit = unit switch { "mi" or "km" or "m" or "yd" or "ft" => unit, _ => DistanceUnit };
        if (unit == DistanceUnit) return;
        var meters = GridDistance * MetersPerUnit(DistanceUnit);
        GridDistance = meters / MetersPerUnit(unit);
        DistanceUnit = unit;
        Notify();
    }

    static double MetersPerUnit(string unit) => unit switch
    {
        "mi" => 1609.344,
        "km" => 1000.0,
        "m" => 1.0,
        "yd" => 0.9144,
        "ft" => 0.3048,
        _ => 1.0
    };

    public async Task InitializeAsync(){await LoadAtlasAsync();await LoadCardsAsync();Notify();}
    async Task LoadAtlasAsync(){var rows=await http.GetFromJsonAsync<List<AtlasTile>>("data/atlas-public.json");if(rows is not null)AtlasTiles.AddRange(rows);}
    async Task LoadCardsAsync(){var rows=await http.GetFromJsonAsync<List<CardItem>>("data/cards-public.json");if(rows is not null)Cards.AddRange(rows);}

    public DiceSpec? Dice(string key) => DiceSet.FirstOrDefault(x => x.Key == key);

    public Task RollAsync(string key)=>RollAsync(key,null);

    public async Task RollAsync(string key,int? selectedMagnitude)
    {
        var die = Dice(key);
        if (die is null) return;
        var x = .16 + Random.Shared.NextDouble() * .68;
        var y = .16 + Random.Shared.NextDouble() * .68;
        var item = new RollItem(die.Key, die.Label, 0, Random.Shared.Next(die.FrameCount), x, y);
        Rolls.Add(item);
        Notify();

        var steps = Random.Shared.Next(13, 23);
        for (var n = 0; n < steps; n++)
        {
            var i = Rolls.IndexOf(item);
            if (i < 0) return;
            item = item with { Frame = (item.Frame + 1) % die.FrameCount };
            Rolls[i] = item;
            Notify();
            await Task.Delay(52 + Math.Min(n * 3, 34));
        }

        var face = selectedMagnitude.HasValue && (die.Key is "d5-bonus" or "d5-penalty")
            ? Math.Clamp(selectedMagnitude.Value,1,5)-1
            : Random.Shared.Next(die.Sides);
        var value = (face + die.ValueOffset) * die.Sign;
        var finalFrame = face * 2;
        var finalIndex = Rolls.IndexOf(item);
        if (finalIndex >= 0) Rolls[finalIndex] = item with { Value = value, Frame = finalFrame };
        Notify();
    }

    public void StagePiece(string kind)
    {
        if (Role != "GM") return;
        if (kind is not ("pin" or "token")) return;
        var key = $"piece:{kind}";
        if (StagedAssets.All(x => x.Key != key)) StagedAssets.Add(new(key, kind, kind == "pin" ? "Pin" : "Token"));
        Notify();
    }

    public void StageSelectedTile()
    {
        if (Role != "GM" || string.IsNullOrWhiteSpace(SelectedTile)) return;
        var tile = AtlasTiles.FirstOrDefault(t => t.Id == SelectedTile);
        if (tile is null) return;
        var key = $"tile:{tile.Id}";
        if (StagedAssets.All(x => x.Key != key)) StagedAssets.Add(new(key, "tile", tile.Name, tile.Image));
        Notify();
    }

    public void RemoveStaged(string key){StagedAssets.RemoveAll(x=>x.Key==key);Notify();}
    public void PlaceStaged(StagedAsset staged,double x,double y,double placementZoom)
    {
        x=Math.Clamp(x,0,1);y=Math.Clamp(y,0,1);
        if(staged.Kind=="tile") PlacedTiles.Add(new(staged.Key[5..],staged.Name,staged.Image,x,y));
        else Pieces.Add(new(staged.Kind,x,y,staged.Kind=="pin"?Math.Max(placementZoom,.01):1));
        Notify();
    }
    public void MovePiece(PieceItem piece,double x,double y){var i=Pieces.IndexOf(piece);if(i<0)return;Pieces[i]=piece with { X=Math.Clamp(x,0,1),Y=Math.Clamp(y,0,1) };Notify();}
    public void RemovePiece(PieceItem piece){Pieces.Remove(piece);Notify();}
    public void MoveTile(TileItem tile,double x,double y){var i=PlacedTiles.IndexOf(tile);if(i<0)return;PlacedTiles[i]=tile with { X=Math.Clamp(x,0,1),Y=Math.Clamp(y,0,1) };Notify();}
    public void RemoveTile(TileItem tile){PlacedTiles.Remove(tile);Notify();}
    public void MapTap(double x,double y) { }
    public void PlacePin(double x,double y,double placementZoom)=>Pieces.Add(new("pin",Math.Clamp(x,0,1),Math.Clamp(y,0,1),Math.Max(placementZoom,.01)));
    public void AddGem(int value){Gems.Add(new(value,.20+Random.Shared.NextDouble()*.60,.20+Random.Shared.NextDouble()*.60));Notify();}
    public void ClearRolls(){Rolls.Clear();Gems.Clear();Notify();}
}
