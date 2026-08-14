using System.Text.Json;
namespace RistWorld;
public sealed partial class WorldSession
{
 public async Task SaveAsync(){var payload=new{Role,Layer,GridStyle,DistanceUnit,GridDiameter,GridDistance,GridCalibrationZoom,Pieces,TileItems=PlacedTiles,Tiles=PlacedTiles};var json=JsonSerializer.Serialize(payload);await js.InvokeVoidAsync("localStorage.setItem",SaveKey,json);}
 public async Task LoadAsync(){var json=await js.InvokeAsync<string?>("localStorage.getItem",SaveKey);if(string.IsNullOrWhiteSpace(json))return;var save=JsonSerializer.Deserialize<SavedWorld>(json);if(save is null)return;EncounterActive=false;Role=save.Role;Layer=TableLayers.Contains(save.Layer)?save.Layer:"WORLD";GridStyle=save.GridStyle;DistanceUnit=save.DistanceUnit switch{"mi" or "km" or "m" or "yd" or "ft"=>save.DistanceUnit,_=>"mi"};GridDiameter=save.GridDiameter;GridDistance=Math.Max(.01,save.GridDistance);GridCalibrationZoom=Math.Max(.01,save.GridCalibrationZoom);Pieces=save.Pieces??[];PlacedTiles=save.Tiles??[];Notify();}
 public void ShowCard(CardItem card){OpenCard=card;Notify();}
 public void CloseCard(){OpenCard=null;Notify();}
}
