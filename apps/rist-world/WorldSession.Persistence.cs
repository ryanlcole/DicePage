using System.Text.Json;
namespace RistWorld;
public sealed partial class WorldSession
{
 public async Task SaveAsync(){var payload=new{Role,GridStyle,GridDiameter,GridDistance,GridCalibrationZoom,Pieces,TileItems=PlacedTiles,Tiles=PlacedTiles};var json=JsonSerializer.Serialize(payload);await js.InvokeVoidAsync("localStorage.setItem",SaveKey,json);}
 public async Task LoadAsync(){var json=await js.InvokeAsync<string?>("localStorage.getItem",SaveKey);if(string.IsNullOrWhiteSpace(json))return;var save=JsonSerializer.Deserialize<SavedWorld>(json);if(save is null)return;Role=save.Role;GridStyle=save.GridStyle;GridDiameter=save.GridDiameter;GridDistance=save.GridDistance;Pieces=save.Pieces??[];PlacedTiles=save.Tiles??[];using var doc=JsonDocument.Parse(json);if(doc.RootElement.TryGetProperty("GridCalibrationZoom",out var z)&&z.TryGetDouble(out var zoom))GridCalibrationZoom=Math.Max(0.01,zoom);Notify();}
 public void ShowCard(CardItem card){OpenCard=card;Notify();}
 public void CloseCard(){OpenCard=null;Notify();}
}
