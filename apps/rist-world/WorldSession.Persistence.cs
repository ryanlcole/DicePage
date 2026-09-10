using System.Text.Json;
namespace RistWorld;
public sealed partial class WorldSession
{
 const string LegacyPrivateWorldCheckpointKey="maps/Shaelvien-current.ristmap";
 const string OceanResetVersion="2026-08-28-topology-v2";
 const string OceanResetMarkerKey="rist.world.reset.2026-08-28-topology-v2";
 static readonly JsonSerializerOptions MapWriteOptions=new(){WriteIndented=true};
 static readonly JsonSerializerOptions MapReadOptions=new(){PropertyNameCaseInsensitive=true};
 string _lastPrivateSnapshot="";

 object SavePayload()
 {
  var terrain=ExportSpatialTerrain();
  var pieces=ExportSpatialPieces();
  return new
  {
   Format="RISTMAP",
   Version=6,
   WorldId,
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
 public async Task SaveAsync(){await js.InvokeVoidAsync("localStorage.setItem",WorldLocalSaveKey,ExportMapJson());}
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
   await EnsureWorldRelationshipAsync();
   var json=snapshot??ExportMapJson();
   await js.InvokeVoidAsync("localStorage.setItem",WorldLocalSaveKey,json);
   await auth.UploadTextAsync(WorldCheckpointKey,json,"application/json");
   _lastPrivateSnapshot=json;
   if(showSuccess)PrivateStorageStatus=$"{WorldDisplayName} progress synced to your private AWS storage.";
  }
  catch(Exception ex){PrivateStorageStatus="Private save failed: "+ex.Message;}
  if(showSuccess)Notify();
 }
 public async Task LoadPrivateCheckpointAsync()
 {
  if(!IsLoggedIn)return;
  try
  {
   await EnsureWorldRelationshipAsync();
   var saved=await auth.DownloadJsonAsync<SavedWorld>(WorldCheckpointKey);
   var migratedLegacy=false;

   // First-world migration only: older alpha builds stored one unscoped map per account.
   // Adopt that save only when no world-scoped checkpoint exists.
   if(saved is null)
   {
    saved=await auth.DownloadJsonAsync<SavedWorld>(LegacyPrivateWorldCheckpointKey);
    migratedLegacy=saved is not null && OwnsSavedWorld(saved);
   }

   if(saved is null || !OwnsSavedWorld(saved) || !string.Equals(saved.Reset,OceanResetVersion,StringComparison.Ordinal))
   {
    ResetToCanonicalOrigin();
    await SavePrivateCheckpointAsync(showSuccess:false);
    await js.InvokeVoidAsync("localStorage.setItem",WorldResetMarkerKey,"1");
    PrivateStorageStatus=saved is null
      ?$"Private AWS storage initialized for {WorldDisplayName}."
      :!OwnsSavedWorld(saved)
        ?"Stored world identity did not match the active world; the active world was initialized safely."
        :$"Private {WorldDisplayName} world reset once to the canonical World/Plane/Tier origin.";
    Notify();
    return;
   }

   var json=JsonSerializer.Serialize(saved);
   LoadMapJson(json);
   await js.InvokeVoidAsync("localStorage.setItem",WorldLocalSaveKey,ExportMapJson());
   await js.InvokeVoidAsync("localStorage.setItem",WorldResetMarkerKey,"1");
   _lastPrivateSnapshot=ExportMapJson();

   if(migratedLegacy)
   {
    // Write the adopted legacy save into the canonical world namespace. The legacy
    // object is deliberately left untouched as a recovery copy during alpha.
    await SavePrivateCheckpointAsync(showSuccess:false,snapshot:_lastPrivateSnapshot);
    PrivateStorageStatus=$"{WorldDisplayName} migrated to its World ID storage and was restored from private AWS storage.";
   }
   else
   {
    PrivateStorageStatus=$"{WorldDisplayName} progress restored from private AWS storage.";
   }
  }
  catch(Exception ex){PrivateStorageStatus="Private restore failed; using local world: "+ex.Message;}
  Notify();
 }
 public async Task AutoSavePrivateAsync()
 {
  if(!IsLoggedIn)return;
  var json=ExportMapJson();
  if(string.Equals(json,_lastPrivateSnapshot,StringComparison.Ordinal))return;
  await SavePrivateCheckpointAsync(showSuccess:false,snapshot:json);
 }
 public async Task DownloadMapAsync(){var json=ExportMapJson();await js.InvokeVoidAsync("ristWorld.downloadText",$"rist-map-{WorldId}-{DateTime.UtcNow:yyyyMMdd-HHmm}.ristmap",json,"application/json");}
 public async Task ShareMapAsync(){var json=ExportMapJson();await js.InvokeVoidAsync("ristWorld.shareTextFile",$"rist-map-{WorldId}-{DateTime.UtcNow:yyyyMMdd-HHmm}.ristmap",json,"application/json");}
 public async Task<bool> TryLoadSavedMapAsync()
 {
  var resetApplied=await js.InvokeAsync<string?>("localStorage.getItem",WorldResetMarkerKey);
  if(resetApplied!="1")
  {
   var legacyJson=await js.InvokeAsync<string?>("localStorage.getItem",SaveKey);
   if(!string.IsNullOrWhiteSpace(legacyJson))
   {
    var legacy=JsonSerializer.Deserialize<SavedWorld>(legacyJson,MapReadOptions);
    if(OwnsSavedWorld(legacy))
    {
     LoadMapJson(legacyJson);
     await js.InvokeVoidAsync("localStorage.setItem",WorldLocalSaveKey,ExportMapJson());
     await js.InvokeVoidAsync("localStorage.setItem",WorldResetMarkerKey,"1");
     return true;
    }
   }

   ResetToCanonicalOrigin();
   await js.InvokeVoidAsync("localStorage.setItem",WorldLocalSaveKey,ExportMapJson());
   await js.InvokeVoidAsync("localStorage.setItem",WorldResetMarkerKey,"1");
   return true;
  }

  var json=await js.InvokeAsync<string?>("localStorage.getItem",WorldLocalSaveKey);
  if(string.IsNullOrWhiteSpace(json))
  {
   ResetToCanonicalOrigin();
   await js.InvokeVoidAsync("localStorage.setItem",WorldLocalSaveKey,ExportMapJson());
   return true;
  }

  var saved=JsonSerializer.Deserialize<SavedWorld>(json,MapReadOptions);
  if(!OwnsSavedWorld(saved))
  {
   ResetToCanonicalOrigin();
   await js.InvokeVoidAsync("localStorage.setItem",WorldLocalSaveKey,ExportMapJson());
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
  DistanceUnit="km";
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
  var save=JsonSerializer.Deserialize<SavedWorld>(json,MapReadOptions);if(save is null||!OwnsSavedWorld(save))return;
  EncounterActive=false;RestoreOperatingMode(save.OperatingMode);Role=save.Role;Layer=NormalizeRecursionTier(save.Layer);
  GridStyle=save.GridStyle is "square" or "hex" or "none" ? save.GridStyle : "square";
  var metric=MetricDistance(save.DistanceUnit,Math.Max(.01,save.GridDistance));
  DistanceUnit=metric.Unit;
  GridDiameter=save.GridDiameter;GridDistance=metric.Distance;GridCalibrationZoom=Math.Max(.01,save.GridCalibrationZoom);
  CubeX=save.CubeX;CubeY=save.CubeY;CubeZ=save.CubeZ;CubeRole=save.CubeRole;PlaneIndex=save.PlaneIndex;TierIndex=save.TierIndex;LayerOffset=Math.Clamp(save.LayerOffset,0,LayersPerTier-1);
  NpcBoundaryExchanges=save.NpcBoundaryExchanges??[];
  var pieces=(save.Pieces??[]).Where(x=>x.Kind!="coin").ToList();
  ImportSpatialContent(save.Tiles??[],pieces);
  MapLocked=true;CloseHeaderMenus();Notify();
 }

 static (string Unit,double Distance) MetricDistance(string? unit,double distance)=>unit switch
 {
  "km"=>("km",distance),
  "m"=>("m",distance),
  "mi"=>("km",distance*1.609344),
  "yd"=>("m",distance*.9144),
  "ft"=>("m",distance*.3048),
  _=>("km",distance)
 };

 public void ShowCard(CardItem card){OpenCard=card;Notify();}
 public void CloseCard(){OpenCard=null;Notify();}
}
