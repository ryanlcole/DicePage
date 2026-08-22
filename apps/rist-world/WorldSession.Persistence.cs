using System.Text.Json;
namespace RistWorld;
public sealed partial class WorldSession
{
 object SavePayload()=>new{Format="RISTMAP",Version=1,Role,Layer,GridStyle,DistanceUnit,GridDiameter,GridDistance,GridCalibrationZoom,Pieces,TileItems=PlacedTiles,Tiles=PlacedTiles};
 public string ExportMapJson()=>JsonSerializer.Serialize(SavePayload(),new JsonSerializerOptions{WriteIndented=true});
 public async Task SaveAsync(){await js.InvokeVoidAsync("localStorage.setItem",SaveKey,ExportMapJson());}
 public async Task DownloadMapAsync(){var json=ExportMapJson();await js.InvokeVoidAsync("ristWorld.downloadText",$"rist-map-{DateTime.UtcNow:yyyyMMdd-HHmm}.ristmap",json,"application/json");}
 public async Task ShareMapAsync(){var json=ExportMapJson();await js.InvokeVoidAsync("ristWorld.shareTextFile",$"rist-map-{DateTime.UtcNow:yyyyMMdd-HHmm}.ristmap",json,"application/json");}
 public async Task LoadAsync(){var json=await js.InvokeAsync<string?>("localStorage.getItem",SaveKey);if(!string.IsNullOrWhiteSpace(json))LoadMapJson(json);}
 public void LoadMapJson(string json)
 {
  var save=JsonSerializer.Deserialize<SavedWorld>(json,new JsonSerializerOptions{PropertyNameCaseInsensitive=true});if(save is null)return;
  EncounterActive=false;Role=save.Role;Layer=TableLayers.Contains(save.Layer)?save.Layer:"WORLD";GridStyle=save.GridStyle;
  DistanceUnit=save.DistanceUnit switch{"mi" or "km" or "m" or "yd" or "ft"=>save.DistanceUnit,_=>"mi"};
  GridDiameter=save.GridDiameter;GridDistance=Math.Max(.01,save.GridDistance);GridCalibrationZoom=Math.Max(.01,save.GridCalibrationZoom);
  Pieces=(save.Pieces??[]).Where(x=>x.Kind!="coin").ToList();PlacedTiles=save.Tiles??[];MapLocked=true;CloseHeaderMenus();Notify();
 }
 public void ShowCard(CardItem card){OpenCard=card;Notify();}
 public void CloseCard(){OpenCard=null;Notify();}
}
