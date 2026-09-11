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

 object SavePayload(long? revision=null)
 {
  if(!HasActiveWorld)throw new InvalidOperationException("Choose or create a world before saving.");
  var terrain=ExportSpatialTerrain();
  var pieces=ExportSpatialPieces();
  return new
  {
   Format="RISTMAP",
   Version=7,
   Revision=revision??_worldRevision,
   WorldId,
   WorldName=WorldDisplayName,
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
 public string ExportMapJson(long? revision=null)=>JsonSerializer.Serialize(SavePayload(revision),MapWriteOptions);
 public async Task SaveAsync(){if(!HasActiveWorld)return;await js.InvokeVoidAsync("localStorage.setItem",WorldLocalSaveKey,ExportMapJson(_worldRevision));}
 public async Task SaveAndToggleExportAsync(){if(!HasActiveWorld)return;await SaveAsync();SaveMenuOpen=!SaveMenuOpen;LoadMenuOpen=false;Notify();}
 public async Task SaveRistAsync()
 {
  if(!HasActiveWorld){PrivateStorageStatus="Choose or create a world before saving.";Notify();return;}
  if(!IsLoggedIn){PrivateStorageStatus="Log in with Discord to use private AWS storage.";Notify();return;}
  await SavePrivateDeltaAsync(showSuccess:true);
 }
 async Task SavePrivateCheckpointAsync(bool showSuccess,string? snapshot=null)
 {
  if(!HasActiveWorld)return;
  try
  {
   await EnsureWorldRelationshipAsync();
   var json=snapshot??ExportMapJson(_worldRevision);
   var saved=JsonSerializer.Deserialize<SavedWorld>(json,MapReadOptions);
   if(saved is null||!OwnsSavedWorld(saved))
    throw new InvalidOperationException("The canonical checkpoint does not match the active world.");

   // A checkpoint is a materialized revision, never a silent revision change.
   _worldRevision=Math.Max(0,saved.Revision);
   if(saved.Revision!=_worldRevision)json=ExportMapJson(_worldRevision);

   await js.InvokeVoidAsync("localStorage.setItem",WorldLocalSaveKey,json);
   await CommitCheckpointHeadAsync(json);
   _lastPrivateSnapshot=json;
   if(showSuccess)PrivateStorageStatus=$"{WorldDisplayName} canonical checkpoint synced at revision {_worldRevision}.";
  }
  catch(Exception ex){PrivateStorageStatus="Private save failed: "+ex.Message;}
  if(showSuccess)Notify();
 }
 public async Task LoadPrivateCheckpointAsync()
 {
  if(!IsLoggedIn||!HasActiveWorld)return;
  try
  {
   await EnsureWorldRelationshipAsync();
   var saved=await auth.DownloadJsonAsync<SavedWorld>(WorldCheckpointKey);
   var migratedLegacy=false;

   // Original-world migration only: older alpha builds stored one unscoped map per account.
   if(saved is null&&string.Equals(WorldId,LegacyAlphaWorldId,StringComparison.Ordinal))
   {
    saved=await auth.DownloadJsonAsync<SavedWorld>(LegacyPrivateWorldCheckpointKey);
    migratedLegacy=saved is not null && OwnsSavedWorld(saved);
   }

   if(saved is null || !OwnsSavedWorld(saved) || !string.Equals(saved.Reset,OceanResetVersion,StringComparison.Ordinal))
   {
    ResetDeltaPersistenceState();
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

   // current.ristmap is the latest complete checkpoint. delta-head.json names any
   // immutable revisions after it. Materialize those before exposing the world to the client.
   saved=await LoadPrivateDeltaChainAsync(saved);
   var json=JsonSerializer.Serialize(saved,MapWriteOptions);
   LoadMapJson(json);
   _worldRevision=Math.Max(0,saved.Revision);
   var geonaphAuthorityNormalized=EnsureGeonaphOriginLayerInvariant();
   var materialized=ExportMapJson(_worldRevision);
   await js.InvokeVoidAsync("localStorage.setItem",WorldLocalSaveKey,materialized);
   await js.InvokeVoidAsync("localStorage.setItem",WorldResetMarkerKey,"1");
   _lastPrivateSnapshot=materialized;

   if(migratedLegacy||geonaphAuthorityNormalized)
   {
    await SavePrivateCheckpointAsync(showSuccess:false,snapshot:_lastPrivateSnapshot);
    PrivateStorageStatus=migratedLegacy
      ?$"{WorldDisplayName} migrated to revisioned World ID storage and was restored from private AWS storage."
      :$"{WorldDisplayName} origin authority was normalized at canonical revision {_worldRevision}.";
   }
   else
   {
    PrivateStorageStatus=$"{WorldDisplayName} canonical revision {_worldRevision} restored from private AWS storage.";
   }
  }
  catch(Exception ex){PrivateStorageStatus="Private restore failed; using local world: "+ex.Message;}
  Notify();
 }
 public async Task AutoSavePrivateAsync()
 {
  if(!IsLoggedIn||!HasActiveWorld)return;
  try{await SavePrivateDeltaAsync(showSuccess:false);}
  catch(Exception ex){PrivateStorageStatus="Private autosave failed: "+ex.Message;Notify();}
 }
 public async Task DownloadMapAsync(){if(!HasActiveWorld)return;var json=ExportMapJson(_worldRevision);await js.InvokeVoidAsync("ristWorld.downloadText",$"rist-map-{WorldId}-{DateTime.UtcNow:yyyyMMdd-HHmm}.ristmap",json,"application/json");}
 public async Task ShareMapAsync(){if(!HasActiveWorld)return;var json=ExportMapJson(_worldRevision);await js.InvokeVoidAsync("ristWorld.shareTextFile",$"rist-map-{WorldId}-{DateTime.UtcNow:yyyyMMdd-HHmm}.ristmap",json,"application/json");}
 public async Task<bool> TryLoadSavedMapAsync()
 {
  if(!HasActiveWorld)return false;
  var resetApplied=await js.InvokeAsync<string?>("localStorage.getItem",WorldResetMarkerKey);
  if(resetApplied!="1")
  {
   if(string.Equals(WorldId,LegacyAlphaWorldId,StringComparison.Ordinal))
   {
    var legacyJson=await js.InvokeAsync<string?>("localStorage.getItem",SaveKey);
    if(!string.IsNullOrWhiteSpace(legacyJson))
    {
     var legacy=JsonSerializer.Deserialize<SavedWorld>(legacyJson,MapReadOptions);
     if(OwnsSavedWorld(legacy))
     {
      LoadMapJson(legacyJson);
      _worldRevision=Math.Max(0,legacy?.Revision??0);
      EnsureGeonaphOriginLayerInvariant();
      await js.InvokeVoidAsync("localStorage.setItem",WorldLocalSaveKey,ExportMapJson(_worldRevision));
      await js.InvokeVoidAsync("localStorage.setItem",WorldResetMarkerKey,"1");
      return true;
     }
    }
   }

   ResetDeltaPersistenceState();
   ResetToCanonicalOrigin();
   await js.InvokeVoidAsync("localStorage.setItem",WorldLocalSaveKey,ExportMapJson(_worldRevision));
   await js.InvokeVoidAsync("localStorage.setItem",WorldResetMarkerKey,"1");
   return true;
  }

  var json=await js.InvokeAsync<string?>("localStorage.getItem",WorldLocalSaveKey);
  if(string.IsNullOrWhiteSpace(json))
  {
   ResetDeltaPersistenceState();
   ResetToCanonicalOrigin();
   await js.InvokeVoidAsync("localStorage.setItem",WorldLocalSaveKey,ExportMapJson(_worldRevision));
   return true;
  }

  var saved=JsonSerializer.Deserialize<SavedWorld>(json,MapReadOptions);
  if(!OwnsSavedWorld(saved))
  {
   ResetDeltaPersistenceState();
   ResetToCanonicalOrigin();
   await js.InvokeVoidAsync("localStorage.setItem",WorldLocalSaveKey,ExportMapJson(_worldRevision));
   return true;
  }

  _worldRevision=Math.Max(0,saved?.Revision??0);
  LoadMapJson(json);
  if(EnsureGeonaphOriginLayerInvariant())
   await js.InvokeVoidAsync("localStorage.setItem",WorldLocalSaveKey,ExportMapJson(_worldRevision));
  return true;
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
  EnsureGeonaphOriginLayerInvariant();
  MapLocked=true;
  CloseHeaderMenus();
  Notify();
 }

 public void LoadMapJson(string json)
 {
  var save=JsonSerializer.Deserialize<SavedWorld>(json,MapReadOptions);if(save is null||!OwnsSavedWorld(save))return;
  if(string.IsNullOrWhiteSpace(_worldDisplayName)&&!string.IsNullOrWhiteSpace(save.WorldName)){_worldDisplayName=save.WorldName.Trim();MapName=_worldDisplayName;}
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
