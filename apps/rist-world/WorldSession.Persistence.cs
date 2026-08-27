using System.Text.Json;
namespace RistWorld;
public sealed partial class WorldSession
{
 const string PrivateWorldCheckpointKey="maps/Shaelvien-current.ristmap";
 string _lastPrivateSnapshot="";
 object SavePayload()=>new{Format="RISTMAP",Version=1,Role,Layer,GridStyle,DistanceUnit,GridDiameter,GridDistance,GridCalibrationZoom,Pieces,TileItems=PlacedTiles,Tiles=PlacedTiles};
 public string ExportMapJson()=>JsonSerializer.Serialize(SavePayload(),new JsonSerializerOptions{WriteIndented=true});
 public async Task SaveAsync(){await js.InvokeVoidAsync("localStorage.setItem",SaveKey,ExportMapJson());}
 public async Task SaveAndToggleExportAsync(){await SaveAsync();SaveMenuOpen=!SaveMenuOpen;LoadMenuOpen=false;Notify();}
 public async Task SaveRistAsync()
 {
  if(!IsLoggedIn){PrivateStorageStatus="Log in with Discord to use private AWS storage.";Notify();return;}
  await SavePrivateCheckpointAsync(showSuccess:true);
 }
 async Task SavePrivateCheckpointAsync(bool showSuccess)
 {
  try
  {
   var json=ExportMapJson();
   await js.InvokeVoidAsync("localStorage.setItem",SaveKey,json);
   await auth.UploadTextAsync(PrivateWorldCheckpointKey,json,"application/json");
   _lastPrivateSnapshot=json;
   if(showSuccess)PrivateStorageStatus="Shaelvien progress synced to your private AWS storage.";
  }
  catch(Exception ex){PrivateStorageStatus="Private save failed: "+ex.Message;}
  if(showSuccess)Notify();
 }
 public async Task LoadPrivateCheckpointAsync()
 {
  if(!IsLoggedIn)return;
  try
  {
   var saved=await auth.DownloadJsonAsync<SavedWorld>(PrivateWorldCheckpointKey);
   if(saved is null)
   {
    _lastPrivateSnapshot=ExportMapJson();
    PrivateStorageStatus="Private AWS storage ready. New Shaelvien world will sync automatically.";
    Notify();return;
   }
   var json=JsonSerializer.Serialize(saved);
   LoadMapJson(json);
   await js.InvokeVoidAsync("localStorage.setItem",SaveKey,json);
   _lastPrivateSnapshot=ExportMapJson();
   PrivateStorageStatus="Shaelvien progress restored from your private AWS storage.";
  }
  catch(Exception ex){PrivateStorageStatus="Private restore failed; using local world: "+ex.Message;}
  Notify();
 }
 public async Task AutoSavePrivateAsync()
 {
  if(!IsLoggedIn)return;
  var json=ExportMapJson();
  if(string.Equals(json,_lastPrivateSnapshot,StringComparison.Ordinal))return;
  await SavePrivateCheckpointAsync(showSuccess:false);
 }
 public async Task DownloadMapAsync(){var json=ExportMapJson();await js.InvokeVoidAsync("ristWorld.downloadText",$"rist-map-{DateTime.UtcNow:yyyyMMdd-HHmm}.ristmap",json,"application/json");}
 public async Task ShareMapAsync(){var json=ExportMapJson();await js.InvokeVoidAsync("ristWorld.shareTextFile",$"rist-map-{DateTime.UtcNow:yyyyMMdd-HHmm}.ristmap",json,"application/json");}
 public async Task<bool> TryLoadSavedMapAsync()
 {
  var json=await js.InvokeAsync<string?>("localStorage.getItem",SaveKey);
  if(string.IsNullOrWhiteSpace(json))
  {
   // A fresh public session begins in canonical Shaelvien. Naeja remains
   // registered as legacy/importable map content for existing saved worlds.
   BuildShaelvienPangaea();
   MapLocked=true;
   return true;
  }
  LoadMapJson(json);return true;
 }
 public async Task LoadAsync(){await TryLoadSavedMapAsync();}
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
