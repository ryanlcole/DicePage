namespace RistWorld;
public sealed partial class WorldSession
{
 public static string[] TableLayers => RecursionTiers;
 public string Layer { get; private set; } = "WORLD";
 public bool EncounterActive { get; private set; }
 public string? RecurseTarget { get; private set; }
 public string TableMode { get; private set; } = "worldbuilder";
 public string TableModeLabel=>TableMode switch{"forge"=>"Forge","test"=>"Test","encounter"=>"Encounter","play"=>"Let's Roll!",_=>"Worldbuilder"};
 public bool PlayActive=>TableMode=="play";
 public bool MapLocked { get; private set; } = true;
 public bool CanEditTiles=>Role=="GM"&&TableMode=="worldbuilder";
 public bool LockedTileMenuOpen { get; private set; }
 public bool RecursiveRegionSelectionMode { get; private set; }
 public bool RegionPlayerPickerOpen { get; private set; }
 public TileItem? HeldLockedTile { get; private set; }
 readonly List<TileItem> recursiveRegionTiles=[];
 readonly HashSet<(int X,int Y)> recursiveRegionKeys=[];
 readonly Stack<RecursiveMapState> recursiveParents=[];
 readonly Dictionary<string,RecursiveMapState> recursiveChildren=new(StringComparer.Ordinal);
 readonly Dictionary<string,string> recursiveTileRoutes=new(StringComparer.Ordinal);
 readonly Dictionary<string,HashSet<string>> recursiveRegionPlayers=new(StringComparer.Ordinal);
 static readonly IReadOnlySet<string> EmptyRegionPlayers=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
 string? activeRecursiveKey;
 public bool HasRecursiveRegionSelection=>recursiveRegionTiles.Count>0;
 public int RecursiveRegionSelectionCount=>recursiveRegionTiles.Count;
 public string NextRecursiveLayer
 {
  get{var i=Array.IndexOf(TableLayers,Layer);return i>=0&&i<TableLayers.Length-1?TableLayers[i+1]:Layer;}
 }
 public bool CanEnterHeldRegion=>HeldLockedTile is not null&&recursiveTileRoutes.ContainsKey(RecursiveTileRouteKey(Layer,HeldLockedTile));
 public IReadOnlyList<string> RegionPlayerChoices
 {
  get
  {
   var name=CharacterName.Trim();
   if(string.IsNullOrWhiteSpace(name)||name.Equals("Player 1",StringComparison.OrdinalIgnoreCase))return ["Player 1"];
   return [name,"Player 1"];
  }
 }
 public IReadOnlySet<string> AssignedRegionPlayers
 {
  get
  {
   var key=HeldRegionKey();
   return key is not null&&recursiveRegionPlayers.TryGetValue(key,out var players)?players:EmptyRegionPlayers;
  }
 }
 readonly List<TileItem> selectedZoneTiles=[];
 readonly HashSet<(int X,int Y)> selectedZoneKeys=[];
 public bool HasSelectedZone=>selectedZoneTiles.Count>0;
 public bool SelectedZoneLocked=>HasSelectedZone&&selectedZoneTiles.All(x=>x.Locked);
 public string SelectedZoneTerrain=>selectedZoneTiles
  .Select(TileTerrain).GroupBy(x=>x,StringComparer.OrdinalIgnoreCase)
  .OrderByDescending(x=>x.Count()).ThenBy(x=>x.Key).Select(x=>x.Key).FirstOrDefault()??"Terrain";
 public string SelectedZoneLabel=>selectedZoneTiles.Select(x=>x.ZoneLabel).FirstOrDefault(x=>!string.IsNullOrWhiteSpace(x))??"";
 public IReadOnlyList<MapZoneLabel> MapZoneLabels=>PlacedTiles
  .Where(x=>!string.IsNullOrWhiteSpace(x.ZoneId)&&!string.IsNullOrWhiteSpace(x.ZoneLabel))
  .GroupBy(x=>x.ZoneId).Select(g=>new MapZoneLabel(g.Key,g.First().ZoneLabel,
   g.Select(TileTerrain).GroupBy(x=>x).OrderByDescending(x=>x.Count()).First().Key,
   g.Average(x=>x.X)+GridCellWidthPercent/2,g.Average(x=>x.Y)+GridCellHeightPercent/2,g.All(x=>x.Locked))).ToList();

 void ClearRecursiveSelection(){recursiveRegionTiles.Clear();recursiveRegionKeys.Clear();}
 void AddRecursiveTile(TileItem tile){recursiveRegionTiles.Add(tile);recursiveRegionKeys.Add(TileGridKey(tile));}
 void RemoveRecursiveTile(TileItem tile){recursiveRegionTiles.Remove(tile);recursiveRegionKeys.Remove(TileGridKey(tile));}
 void ClearSelectedZone(){selectedZoneTiles.Clear();selectedZoneKeys.Clear();}
 void RebuildSelectedZoneKeys(){selectedZoneKeys.Clear();foreach(var tile in selectedZoneTiles)selectedZoneKeys.Add(TileGridKey(tile));}
 void SyncGameModeFromTableMode()=>GameMode=TableMode switch{"test"=>"Test","play" or "encounter"=>"Live",_=>"Build"};

 public void ToggleMapLock()
 {
  if(!CanEditTiles)return;
  MapLocked=!MapLocked;
  ClearSelectedZone();CloseLockedTileMenu(false);RecursiveRegionSelectionMode=false;RegionPlayerPickerOpen=false;HeldLockedTile=null;ClearRecursiveSelection();Notify();
 }
 public void OpenLockedTileMenu(TileItem tile)
 {
  if(!CanEditTiles||!tile.Locked)return;
  HeldLockedTile=tile;LockedTileMenuOpen=true;RecursiveRegionSelectionMode=false;RegionPlayerPickerOpen=false;ClearRecursiveSelection();Notify();
 }
 public void CloseLockedTileMenu(bool notify=true)
 {
  LockedTileMenuOpen=false;RegionPlayerPickerOpen=false;HeldLockedTile=null;
  if(notify)Notify();
 }
 public void BeginRecursiveRegionSelection()
 {
  if(!CanEditTiles||HeldLockedTile is null||!HeldLockedTile.Locked)return;
  ClearRecursiveSelection();AddRecursiveTile(HeldLockedTile);LockedTileMenuOpen=false;RecursiveRegionSelectionMode=true;Notify();
 }
 public void ToggleRecursiveRegionTile(TileItem tile)
 {
  if(!CanEditTiles||!RecursiveRegionSelectionMode||!tile.Locked)return;
  var seed=recursiveRegionTiles.FirstOrDefault();
  if(seed is not null&&!string.Equals(seed.ZoneId,tile.ZoneId,StringComparison.Ordinal))return;
  if(recursiveRegionTiles.Contains(tile))RemoveRecursiveTile(tile);else AddRecursiveTile(tile);
  Notify();
 }
 public bool IsRecursiveRegionTile(TileItem tile)=>recursiveRegionKeys.Contains(TileGridKey(tile));
 public string RecursiveRegionBoundaryClasses(TileItem tile)
 {
  var key=TileGridKey(tile);if(!recursiveRegionKeys.Contains(key))return "";
  var parts=new List<string>{"recursive-region-selected"};
  if(!recursiveRegionKeys.Contains((key.X,key.Y-1)))parts.Add("recursive-edge-top");
  if(!recursiveRegionKeys.Contains((key.X+1,key.Y)))parts.Add("recursive-edge-right");
  if(!recursiveRegionKeys.Contains((key.X,key.Y+1)))parts.Add("recursive-edge-bottom");
  if(!recursiveRegionKeys.Contains((key.X-1,key.Y)))parts.Add("recursive-edge-left");
  return string.Join(" ",parts);
 }
 public void CancelRecursiveRegionSelection(){RecursiveRegionSelectionMode=false;ClearRecursiveSelection();HeldLockedTile=null;Notify();}
 public void CommitRecursiveRegion()
 {
  if(!CanEditTiles||!HasRecursiveRegionSelection)return;
  var parentLayer=Layer;var targetLayer=NextRecursiveLayer;if(targetLayer==parentLayer)return;
  var key=RecursiveSelectionKey(parentLayer,recursiveRegionTiles);
  SaveCurrentRecursiveState(key);
  foreach(var tile in recursiveRegionTiles)recursiveTileRoutes[RecursiveTileRouteKey(parentLayer,tile)]=key;
  EnterRecursiveChild(key,targetLayer);
 }
 public void EnterHeldRegion()
 {
  var key=HeldRegionKey();if(!CanEditTiles||key is null||!recursiveChildren.TryGetValue(key,out var child))return;
  SaveCurrentRecursiveState(key);EnterRecursiveChild(key,child.Layer);
 }
 public void OpenSendPlayersToRegion()
 {
  if(!CanEditTiles||HeldRegionKey() is null)return;LockedTileMenuOpen=false;RegionPlayerPickerOpen=true;Notify();
 }
 public void TogglePlayerInHeldRegion(string player)
 {
  var key=HeldRegionKey();if(!CanEditTiles||key is null)return;
  if(!recursiveRegionPlayers.TryGetValue(key,out var players))recursiveRegionPlayers[key]=players=new(StringComparer.OrdinalIgnoreCase);
  if(!players.Add(player))players.Remove(player);Notify();
 }
 public void CloseRegionPlayerPicker(){RegionPlayerPickerOpen=false;HeldLockedTile=null;Notify();}
 void SaveCurrentRecursiveState(string childKey)
 {
  if(activeRecursiveKey is not null)recursiveChildren[activeRecursiveKey]=new(Layer,activeRecursiveKey,PlacedTiles.ToList(),Pieces.ToList());
  recursiveParents.Push(new(Layer,childKey,PlacedTiles.ToList(),Pieces.ToList()));
 }
 void EnterRecursiveChild(string key,string targetLayer)
 {
  if(recursiveChildren.TryGetValue(key,out var child)){PlacedTiles=child.Tiles.ToList();Pieces=child.Pieces.ToList();}
  else{PlacedTiles=[];Pieces=[];recursiveChildren[key]=new(NormalizeRecursionTier(targetLayer),key,[],[]);}
  activeRecursiveKey=key;Layer=NormalizeRecursionTier(targetLayer);RecurseTarget=key;TableMode="worldbuilder";SyncGameModeFromTableMode();
  LockedTileMenuOpen=false;RecursiveRegionSelectionMode=false;RegionPlayerPickerOpen=false;HeldLockedTile=null;ClearRecursiveSelection();MapLocked=true;ClearSelectedZone();Notify();
 }
 string? HeldRegionKey()=>HeldLockedTile is null?null:recursiveTileRoutes.GetValueOrDefault(RecursiveTileRouteKey(Layer,HeldLockedTile));
 static string RecursiveTileRouteKey(string layer,TileItem tile){var k=TileGridKey(tile);return $"{layer}:{k.X}:{k.Y}";}
 static string RecursiveSelectionKey(string layer,IEnumerable<TileItem> tiles)=>$"{layer}>{string.Join(",",tiles.Select(TileGridKey).OrderBy(x=>x.Y).ThenBy(x=>x.X).Select(x=>$"{x.X}.{x.Y}"))}";
 sealed record RecursiveMapState(string Layer,string Key,List<TileItem> Tiles,List<PieceItem> Pieces);
 public void SelectTileZone(TileItem tile)
 {
  if(!CanEditTiles||MapLocked)return;
  ClearSelectedZone();
  var all=PlacedTiles.GroupBy(TileGridKey).ToDictionary(x=>x.Key,x=>x.Last());
  var open=new Queue<TileItem>();var seen=new HashSet<(int X,int Y)>();open.Enqueue(tile);
  while(open.Count>0)
  {
   var current=open.Dequeue();var key=TileGridKey(current);if(!seen.Add(key))continue;selectedZoneTiles.Add(current);selectedZoneKeys.Add(key);
   foreach(var next in new[]{(key.X-1,key.Y),(key.X+1,key.Y),(key.X,key.Y-1),(key.X,key.Y+1)})
    if(all.TryGetValue(next,out var adjacent))open.Enqueue(adjacent);
  }
  Notify();
 }
 public void ToggleSelectedZoneLock()
 {
  if(!CanEditTiles||!HasSelectedZone)return;
  var lockTiles=!SelectedZoneLocked;var zoneId=selectedZoneTiles.Select(x=>x.ZoneId).FirstOrDefault(x=>!string.IsNullOrWhiteSpace(x))??Guid.NewGuid().ToString("N");
  var replacements=new List<TileItem>();
  foreach(var tile in selectedZoneTiles){var index=PlacedTiles.IndexOf(tile);if(index<0)continue;var replacement=tile with{ZoneId=zoneId,Locked=lockTiles};PlacedTiles[index]=replacement;replacements.Add(replacement);}
  selectedZoneTiles.Clear();selectedZoneTiles.AddRange(replacements);RebuildSelectedZoneKeys();Notify();
 }
 public void SetSelectedZoneLabel(string label)
 {
  if(!CanEditTiles||!HasSelectedZone)return;label=label.Trim();
  var zoneId=selectedZoneTiles.Select(x=>x.ZoneId).FirstOrDefault(x=>!string.IsNullOrWhiteSpace(x))??Guid.NewGuid().ToString("N");
  var replacements=new List<TileItem>();
  foreach(var tile in selectedZoneTiles){var index=PlacedTiles.IndexOf(tile);if(index<0)continue;var replacement=tile with{ZoneId=zoneId,ZoneLabel=label};PlacedTiles[index]=replacement;replacements.Add(replacement);}
  selectedZoneTiles.Clear();selectedZoneTiles.AddRange(replacements);RebuildSelectedZoneKeys();Notify();
 }
 public bool IsSelectedZoneTile(TileItem tile)=>selectedZoneKeys.Contains(TileGridKey(tile));
 public string ZoneBoundaryClasses(TileItem tile)
 {
  var key=TileGridKey(tile);if(!selectedZoneKeys.Contains(key))return "";
  var parts=new List<string>{"zone-selected"};
  if(!selectedZoneKeys.Contains((key.X,key.Y-1)))parts.Add("zone-edge-top");
  if(!selectedZoneKeys.Contains((key.X+1,key.Y)))parts.Add("zone-edge-right");
  if(!selectedZoneKeys.Contains((key.X,key.Y+1)))parts.Add("zone-edge-bottom");
  if(!selectedZoneKeys.Contains((key.X-1,key.Y)))parts.Add("zone-edge-left");
  return string.Join(" ",parts);
 }
 static (int X,int Y) TileGridKey(TileItem tile)=>((int)Math.Round(tile.X*GridColumns),(int)Math.Round(tile.Y*GridRows));
 static string TileTerrain(TileItem tile){var parts=tile.Name.Split(" · ",StringSplitOptions.RemoveEmptyEntries);return parts.Length>2?parts[^1]:"Terrain";}
 public bool ChatComposerOpen { get; private set; }
 public bool DialogueOpen { get; private set; }
 public string ChatDraft { get; set; } = "";
 public string DialogueText { get; private set; } = "";
 public string DialogueSpeaker=>string.IsNullOrWhiteSpace(CharacterName)?"Player":CharacterName;

 public PieceItem? SelectedPin { get; private set; }
 readonly System.Diagnostics.Stopwatch encounterClock=new();
 System.Threading.Timer? encounterTimer;
 public bool EncounterTimerRunning=>encounterClock.IsRunning;
 public TimeSpan EncounterElapsed=>encounterClock.Elapsed;
 public string EncounterElapsedText=>$"{(int)EncounterElapsed.TotalHours:00}:{EncounterElapsed.Minutes:00}:{EncounterElapsed.Seconds:00}";
 public string EncounterElapsedIso=>$"PT{(int)EncounterElapsed.TotalHours}H{EncounterElapsed.Minutes}M{EncounterElapsed.Seconds}S";

 string preEncounterGridStyle = "square";
 string preEncounterUnit = "mi";
 double preEncounterDistance = 5;
 double preEncounterCalibrationZoom = 1;

 public void SetTableMode(string mode)
 {
  mode=mode switch{"worldbuilder" or "forge" or "test" or "encounter" or "play"=>mode,_=>"worldbuilder"};
  if(mode is "encounter" or "play"){if(!EncounterActive)EnterEncounter();}
  else if(EncounterActive)ExitEncounter();
  TableMode=mode;SyncGameModeFromTableMode();
  if(mode!="worldbuilder"){MapLocked=true;ClearSelectedZone();LockedTileMenuOpen=false;RecursiveRegionSelectionMode=false;RegionPlayerPickerOpen=false;HeldLockedTile=null;ClearRecursiveSelection();}
  if(mode!="play"){encounterClock.Stop();encounterTimer?.Dispose();encounterTimer=null;}
  Notify();
 }
 public void ToggleChatComposer(){ChatComposerOpen=!ChatComposerOpen;if(ChatComposerOpen)DialogueOpen=false;Notify();}
 public void CloseChat(){ChatComposerOpen=false;DialogueOpen=false;Notify();}
 public void SendChat()
 {
  var message=ChatDraft.Trim();
  if(message.Length==0)return;
  DialogueText=message;ChatDraft="";ChatComposerOpen=false;DialogueOpen=true;Notify();
 }
 public void AdvanceDialogue(){DialogueOpen=false;Notify();}

 public void SetLayer(string layer)
 {
  if(EncounterActive)return;
  Layer=NormalizeRecursionTier(layer);
  Notify();
 }

 public void EnterEncounter()
 {
  if(EncounterActive)return;
  preEncounterGridStyle=GridStyle;
  preEncounterUnit=DistanceUnit;
  preEncounterDistance=GridDistance;
  preEncounterCalibrationZoom=GridCalibrationZoom;
  EncounterActive=true;
  GridStyle="hex";
  DistanceUnit="ft";
  GridDistance=5;
  GridCalibrationZoom=Math.Max(ViewZoom,.01);
  Notify();
 }

 public void ExitEncounter()
 {
  if(!EncounterActive)return;
  encounterClock.Stop();
  encounterTimer?.Dispose();
  encounterTimer=null;
  EncounterActive=false;
  if(TableMode is "encounter" or "play")TableMode="worldbuilder";
  SyncGameModeFromTableMode();
  GridStyle=preEncounterGridStyle;
  DistanceUnit=preEncounterUnit;
  GridDistance=preEncounterDistance;
  GridCalibrationZoom=preEncounterCalibrationZoom;
  Notify();
 }

 public void ToggleEncounterTimer()
 {
  if(encounterClock.IsRunning)
  {
   encounterClock.Stop();
   encounterTimer?.Dispose();
   encounterTimer=null;
  }
  else
  {
   encounterClock.Start();
   encounterTimer=new System.Threading.Timer(_=>Notify(),null,TimeSpan.Zero,TimeSpan.FromSeconds(1));
  }
  Notify();
 }
 public void ResetEncounterTimer(){encounterClock.Reset();Notify();}
 public void PinTap(PieceItem piece)
 {
  if(piece.Kind!="pin")return;
  SelectedPin=piece;
  var tile=PlacedTiles
   .Where(x=>x.Locked
    && piece.X>=x.X && piece.X<x.X+1.0/(GridColumns*Math.Max(x.PlacementZoom,.01))
    && piece.Y>=x.Y && piece.Y<x.Y+1.0/(GridRows*Math.Max(x.PlacementZoom,.01)))
   .OrderByDescending(x=>x.PlacementZoom)
   .FirstOrDefault();
  if(CanEditTiles&&tile is not null){OpenLockedTileMenu(tile);return;}
  Notify();
 }
 public void SetSelectedPinLabel(string label)
 {
  if(SelectedPin is null)return;
  var index=Pieces.IndexOf(SelectedPin);if(index<0)return;
  var updated=SelectedPin with{Label=label.Trim()};Pieces[index]=updated;SelectedPin=updated;Notify();
 }
 public void RemoveSelectedPin(){if(SelectedPin is null)return;Pieces.Remove(SelectedPin);SelectedPin=null;CloseLockedTileMenu(false);Notify();}
 public void DismissPin(){SelectedPin=null;Notify();}
 public void ReturnToWorld()
 {
  if(activeRecursiveKey is not null)recursiveChildren[activeRecursiveKey]=new(Layer,activeRecursiveKey,PlacedTiles.ToList(),Pieces.ToList());
  if(recursiveParents.Count>0)
  {
   var parent=recursiveParents.Pop();PlacedTiles=parent.Tiles.ToList();Pieces=parent.Pieces.ToList();Layer=NormalizeRecursionTier(parent.Layer);
   activeRecursiveKey=recursiveParents.Count>0?recursiveParents.Peek().Key:null;RecurseTarget=activeRecursiveKey;
  }
  else{Layer="WORLD";RecurseTarget=null;activeRecursiveKey=null;}
  SelectedPin=null;EncounterActive=false;TableMode="worldbuilder";SyncGameModeFromTableMode();MapLocked=true;LockedTileMenuOpen=false;RecursiveRegionSelectionMode=false;RegionPlayerPickerOpen=false;HeldLockedTile=null;ClearRecursiveSelection();ClearSelectedZone();Notify();
 }
}
