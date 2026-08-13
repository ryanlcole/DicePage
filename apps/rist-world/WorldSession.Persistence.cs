using System.Text.Json;
namespace RistWorld;
public sealed partial class WorldSession
{
 public async Task SaveAsync(){var json=JsonSerializer.Serialize(new SavedWorld{Role=Role,GridStyle=GridStyle,GridDiameter=GridDiameter,GridDistance=GridDistance,Pieces=[..Pieces],Tiles=[..PlacedTiles]});await js.InvokeVoidAsync("localStorage.setItem",SaveKey,json);}
 public async Task LoadAsync(){var json=await js.InvokeAsync<string?>("localStorage.getItem",SaveKey);if(string.IsNullOrWhiteSpace(json))return;var save=JsonSerializer.Deserialize<SavedWorld>(json);if(save is null)return;Role=save.Role;GridStyle=save.GridStyle;GridDiameter=save.GridDiameter;GridDistance=save.GridDistance;Pieces=save.Pieces??[];PlacedTiles=save.Tiles??[];Notify();}
 public void ShowCard(CardItem card){OpenCard=card;Notify();}
 public void CloseCard(){OpenCard=null;Notify();}
}
