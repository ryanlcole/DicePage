using System.Text.Json;
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
    public List<RollItem> Rolls { get; } = [];
    public List<GemItem> Gems { get; } = [];
    public string WorldMapUrl { get; private set; } = "assets/naeja.jpg";
    public string SelectedTile { get; set; } = "";
    public string PieceKind { get; set; } = "coin";
    public string Role { get; set; } = "GM";
    public string GridStyle { get; set; } = "square";
    public const int GridColumns = 20;
    public const int GridRows = 20;
    public int GridDiameter { get; set; } = 48;
    public double GridDistance { get; set; } = 5;
    public double GridCalibrationZoom { get; set; } = 1;
    public double ViewZoom { get; set; } = 1;
    public double GridCellWidthPercent => 100.0 / GridColumns;
    public double GridCellHeightPercent => 100.0 / GridRows;
    public double EffectiveGridDistance => GridDistance * GridCalibrationZoom / Math.Max(ViewZoom, 0.01);
    public string Mode { get; set; } = "piece";
    public CardItem? OpenCard { get; set; }
    public int Total => Rolls.Sum(x => x.Value) + Gems.Sum(x => x.Value);
    public int[] Dice { get; } = [4,6,8,10,12,20,30,100];
    public void Notify() => Changed?.Invoke();
    public void CalibrateGrid(){GridDistance=Math.Max(0.01,GridDistance);GridCalibrationZoom=Math.Max(0.01,ViewZoom);Notify();}
    public async Task InitializeAsync(){await LoadAssetConfigAsync();await LoadAtlasAsync();await LoadCardsAsync();Notify();}
    async Task LoadAssetConfigAsync(){try{var cfg=await http.GetFromJsonAsync<AssetConfig>("data/asset-config.json");if(!string.IsNullOrWhiteSpace(cfg?.WorldMapUrl))WorldMapUrl=cfg.WorldMapUrl;}catch(HttpRequestException){}}
    async Task LoadAtlasAsync(){var rows=await http.GetFromJsonAsync<List<AtlasTile>>("data/atlas-public.json");if(rows is not null)AtlasTiles.AddRange(rows);}
    async Task LoadCardsAsync(){var rows=await http.GetFromJsonAsync<List<CardItem>>("data/cards-public.json");if(rows is not null)Cards.AddRange(rows);}
    public void MapTap(double x,double y){x=Math.Clamp(x,0,1);y=Math.Clamp(y,0,1);if(Mode=="tile"&&!string.IsNullOrWhiteSpace(SelectedTile)){var tile=AtlasTiles.FirstOrDefault(t=>t.Id==SelectedTile);if(tile is not null)PlacedTiles.Add(new(tile.Id,tile.Name,tile.Image,x,y));}else Pieces.Add(new(PieceKind,x,y));Notify();}
    public void Roll(int sides){var value=Random.Shared.Next(1,sides+1);Rolls.Add(new($"D{sides}",value,.18+Random.Shared.NextDouble()*.64,.18+Random.Shared.NextDouble()*.64));Notify();}
    public void AddGem(int value){Gems.Add(new(value,.20+Random.Shared.NextDouble()*.60,.20+Random.Shared.NextDouble()*.60));Notify();}
    public void ClearRolls(){Rolls.Clear();Gems.Clear();Notify();}
    sealed record AssetConfig(string WorldMapUrl);
}
