using System.Text.Json;
namespace RistWorld;
public sealed partial class WorldSession
{
 const string PrivateWorldCheckpointKey="maps/Shaelvien-current.ristmap";
 const string CampaignCurrentKey="rist.campaign.current.v1";
 const string OceanResetVersion="2026-08-28-topology-v2";
 const string OceanResetMarkerKey="rist.world.reset.2026-08-28-topology-v2";
 static readonly JsonSerializerOptions MapWriteOptions=new(){WriteIndented=true};
 static readonly JsonSerializerOptions MapReadOptions=new(){PropertyNameCaseInsensitive=true};
 string _lastPrivateSnapshot="";

 async Task<string> ActiveCampaignCodeAsync()
 {
  var raw=await js.InvokeAsync<string?>("localStorage.getItem",CampaignCurrentKey);
  if(string.IsNullOrWhiteSpace(raw))return "";
  var safe=new string(raw.Where(c=>char.IsLetterOrDigit(c)||c is '-' or '_').Take(64).ToArray());
  return safe;
 }
 async Task<string> LocalCampaignSaveKeyAsync()
 {
  var code=await ActiveCampaignCodeAsync();
  return string.IsNullOrWhiteSpace(code)?SaveKey:$"{SaveKey}.{code}";
 }
 async Task<string> CampaignResetMarkerKeyAsync()
 {
  var code=await ActiveCampaignCodeAsync();
  return string.IsNullOrWhiteSpace(code)?OceanResetMarkerKey:$"{OceanResetMarkerKey}.{code}";
 }
 async Task<string> PrivateCampaignCheckpointKeyAsync()
 {
  var code=await ActiveCampaignCodeAsync();
  return string.IsNullOrWhiteSpace(code)?PrivateWorldCheckpointKey:$"maps/campaigns/{code}.ristmap";
 }

 object SavePayload()
 {
  var terrain=ExportSpatialTerrain();
  var pieces=ExportSpatialPieces();
  return new
  {
   Format="RISTMAP",
   Version=5,
   Reset=OceanResetVersion,
   OperatingMode,
   Role,
   Layer,
   GridStyle,
   DistanceUnit,
   GridDiameter,
   GridDistance,
   GridCalibrationZoom,
   CubeX,
   CubeY,
   CubeZ,
   CubeRole,
   PlaneIndex,
   TierIndex,
   LayerOffset,
   Pieces=pieces,
   TileItems=terrain,
   Tiles=terrain,
   NpcBoundaryExchanges
  };
 }
 public string ExportMapJson()=>JsonSerializer.Serialize(SavePayload(),MapWriteOptions);
 public async Task SaveAsync(){await js.InvokeVoidAsync("localStorage.setItem",await LocalCampaignSaveKeyAsync(),ExportMapJson());}
 public async Task SaveAndToggleExportAsync(){await SaveAsync();SaveMenuOpen=!SaveMenuOpen;LoadMenuOpen=false;Notify();}
 public async Task SaveRistAsync()
 {
  if(!IsLoggedIn){PrivateStorageStatus="Log in with Discord to use private AWS storage.";Notify();return;}
  await SavePrivateCheckpointAsync(showSuccess:true);
 }
 async Task SavePrivateCheckpointAsync(bool showSuccess,string? snapshot=null)
 {
  try
  {
   var json=snapshot??ExportMapJson();
   var localKey=await LocalCampaignSaveKeyAsync();
   var privateKey=await PrivateCampaignCheckpointKeyAsync();
   await js.InvokeVoidAsync("localStorage.setItem",localKey,json);
   await auth.UploadTextAsync(privateKey,json,"application/json");
   _lastPrivateSnapshot=json;
   if(showSuccess)PrivateStorageStatus="Campaign state synced to your private AWS storage.";
  }
  catch(Exception ex){PrivateStorageStatus="Private save failed: "+ex.Message;}
  if(showSuccess)Notify();
 }
 public async Task LoadPrivateCheckpointAsync()
 {
  if(!IsLoggedIn)return;
  try
  {
   var privateKey=await PrivateCampaignCheckpointKeyAsync();
   var localKey=await LocalCampaignSaveKeyAsync();
   var resetKey=await CampaignResetMarkerKeyAsync();
   var saved=await auth.DownloadJsonAsync<SavedWorld>(privateKey);
   if(saved is null || !string.Equals(saved.Reset,OceanResetVersion,StringComparison.Ordinal))
   {
    ResetToCanonicalOrigin();
    await SavePrivateCheckpointAsync(showSuccess:false);
    await js.InvokeVoidAsync("localStorage.setItem",resetKey,"1");
    PrivateStorageStatus=saved is null
      ?"Campaign storage initialized with the canonical origin."
      :"Campaign state reset once to the canonical World/Plane/Tier origin.";
    Notify();
    return;
   }

   var json=JsonSerializer.Serialize(saved);
   LoadMapJson(json);
   await js.InvokeVoidAsync("localStorage.setItem",localKey,json);
   await js.InvokeVoidAsync("localStorage.setItem",resetKey,"1");
   _lastPrivateSnapshot=ExportMapJson();
   PrivateStorageStatus="Campaign state restored from your private AWS storage.";
  }
  catch(Exception ex){PrivateStorageStatus="Private restore failed; using local campaign cache: "+ex.Message;}
  Notify();
 }
 public async Task AutoSavePrivateAsync()
 {
  if(!IsLoggedIn)return;
  var json=ExportMapJson();
  if(string.Equals(json,_lastPrivateSnapshot,StringComparison.Ordinal))return;
  await SavePrivateCheckpointAsync(showSuccess:false,snapshot:json);
 }
 public async Task DownloadMapAsync(){var json=ExportMapJson();await js.InvokeVoidAsync("ristWorld.downloadText",$"rist-map-{DateTime.UtcNow:yyyyMMdd-HHmm}.ristmap",json,"application/json");}
 public async Task ShareMapAsync(){var json=ExportMapJson();await js.InvokeVoidAsync("ristWorld.shareTextFile",$"rist-map-{DateTime.UtcNow:yyyyMMdd-HHmm}.ristmap",json,"application/json");}
 public async Task<bool> TryLoadSavedMapAsync()
 {
  var localKey=await LocalCampaignSaveKeyAsync();
  var resetKey=await CampaignResetMarkerKeyAsync();
  var resetApplied=await js.InvokeAsync<string?>("localStorage.getItem",resetKey);
  if(resetApplied!="1")
  {
   ResetToCanonicalOrigin();
   await js.InvokeVoidAsync("localStorage.setItem",localKey,ExportMapJson());
   await js.InvokeVoidAsync("localStorage.setItem",resetKey,"1");
   return true;
  }

  var json=await js.InvokeAsync<string?>("localStorage.getItem",localKey);
  if(string.IsNullOrWhiteSpace(json))
  {
   ResetToCanonicalOrigin();
   await js.InvokeVoidAsync("localStorage.setItem",localKey,ExportMapJson());
   return true;
  }
  LoadMapJson(json);return true;
 }
 public async Task LoadAsync(){await TryLoadSavedMapAsync();}

 void ResetToCanonicalOrigin()
 {
  EncounterActive=false;
  RestoreOperatingMode("mmo");
  Layer="WORLD";
  GridStyle="square";
  DistanceUnit="mi";
  GridDiameter=48;
  GridDistance=1;
  GridCalibrationZoom=1;
  ViewZoom=1;
  Pieces=[];
  PlacedTiles=[];
  ResetTopologyToCanonicalOrigin();
  MapLocked=true;
  CloseHeaderMenus();
  Notify();
 }

 public void LoadMapJson(string json)
 {
  var save=JsonSerializer.Deserialize<SavedWorld>(json,MapReadOptions);if(save is null)return;
  EncounterActive=false;RestoreOperatingMode(save.OperatingMode);Role=save.Role;Layer=NormalizeRecursionTier(save.Layer);GridStyle=save.GridStyle;
  DistanceUnit=save.DistanceUnit switch{"mi" or "km" or "m" or "yd" or "ft"=>save.DistanceUnit,_=>"mi"};
  GridDiameter=save.GridDiameter;GridDistance=Math.Max(.01,save.GridDistance);GridCalibrationZoom=Math.Max(.01,save.GridCalibrationZoom);
  CubeX=save.CubeX;CubeY=save.CubeY;CubeZ=save.CubeZ;CubeRole=save.CubeRole;PlaneIndex=save.PlaneIndex;TierIndex=save.TierIndex;LayerOffset=Math.Clamp(save.LayerOffset,0,LayersPerTier-1);
  NpcBoundaryExchanges=save.NpcBoundaryExchanges??[];
  var pieces=(save.Pieces??[]).Where(x=>x.Kind!="coin").ToList();
  ImportSpatialContent(save.Tiles??[],pieces);
  MapLocked=true;CloseHeaderMenus();Notify();
 }
 public void ShowCard(CardItem card){OpenCard=card;Notify();}
 public void CloseCard(){OpenCard=null;Notify();}
}
