using System.Text.Json;
using System.Net.Http.Json;
using Microsoft.JSInterop;

namespace RistWorld;

public sealed partial class WorldSession(HttpClient http, IJSRuntime js)
{
    private const string SaveKey = "rist.world.blazor.v1";
    private const string VerifiedWorldMap = "https://d2d6rnm6fnsp89.cloudfront.net/worlds/naeja/world.png?v=20260813-refresh";
    public event Action? Changed;
    public List<AtlasTile> AtlasTiles { get; } = [];
    public List<CardItem> Cards { get; } = [];
    public List<PieceItem> Pieces { get; private set; } = [];
    public List<TileItem> PlacedTiles { get; private set; } = [];
    public List<StagedAsset> StagedAssets { get; } = [];
    public List<RollItem> Rolls { get; } = [];
    public List<GemItem> Gems { get; } = [];

    // Use the verified CDN PNG directly at runtime. The Pages build still carries
    // a same-origin copy as a packaging backup, but Safari no longer has to
    // resolve a repository-relative image URL.
    public string WorldMapUrl { get; private set; } = VerifiedWorldMap;

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
    public int[] Dice { get; } = [4,6,8,10,12,20,30,100];
    public void Notify() => Changed?.Invoke();
    public void CalibrateGrid(){GridDistance=Math.Max(0.01,GridDistance);GridCalibrationZoom=Math.Max(0.01,ViewZoom);Notify();}

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

    public async Task InitializeAsync(){await LoadAssetConfigAsync();await LoadAtlasAsync();await LoadCardsAsync();Notify();}

    async Task LoadAssetConfigAsync()
    {
        try
        {
            var cfg = await http.GetFromJsonAsync<AssetConfig>("data/asset-config.json");
            if (!string.IsNullOrWhiteSpace(cfg?.WorldMapUrl) && cfg.WorldMapUrl.StartsWith("http", StringComparison.OrdinalIgnoreCase))
                WorldMapUrl = cfg.WorldMapUrl;
        }
        catch (Exception ex) when (ex is HttpRequestException or JsonException or NotSupportedException)
        {
            WorldMapUrl = VerifiedWorldMap;
        }
    }

    async Task LoadAtlasAsync(){var rows=await http.GetFromJsonAsync<List<AtlasTile>>("data/atlas-public.json");if(rows is not null)AtlasTiles.AddRange(rows);}
    async Task LoadCardsAsync(){var rows=await http.GetFromJsonAsync<List<CardItem>>("data/cards-public.json");if(rows is not null)Cards.AddRange(rows);}

    public void StagePiece(string kind)
    {
        if (Role != "GM") return;
        if (kind is not ("pin" or "token")) return; // coin art is intentionally withheld for now.
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

    public void MovePiece(PieceItem piece,double x,double y)
    {
        var i=Pieces.IndexOf(piece);if(i<0)return;
        Pieces[i]=piece with { X=Math.Clamp(x,0,1),Y=Math.Clamp(y,0,1) };Notify();
    }
    public void RemovePiece(PieceItem piece){Pieces.Remove(piece);Notify();}
    public void MoveTile(TileItem tile,double x,double y)
    {
        var i=PlacedTiles.IndexOf(tile);if(i<0)return;
        PlacedTiles[i]=tile with { X=Math.Clamp(x,0,1),Y=Math.Clamp(y,0,1) };Notify();
    }
    public void RemoveTile(TileItem tile){PlacedTiles.Remove(tile);Notify();}

    // Direct tap placement is intentionally disabled. Assets enter through the
    // staging tray so the tabletop behaves like a physical work surface.
    public void MapTap(double x,double y) { }
    public void PlacePin(double x,double y,double placementZoom)=>Pieces.Add(new("pin",Math.Clamp(x,0,1),Math.Clamp(y,0,1),Math.Max(placementZoom,.01)));
    public void Roll(int sides){var value=Random.Shared.Next(1,sides+1);Rolls.Add(new($"D{sides}",value,.18+Random.Shared.NextDouble()*.64,.18+Random.Shared.NextDouble()*.64));Notify();}
    public void AddGem(int value){Gems.Add(new(value,.20+Random.Shared.NextDouble()*.60,.20+Random.Shared.NextDouble()*.60));Notify();}
    public void ClearRolls(){Rolls.Clear();Gems.Clear();Notify();}
    sealed record AssetConfig(string WorldMapUrl);
}
