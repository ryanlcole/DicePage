using System.Globalization;
using Microsoft.AspNetCore.Components;
using Microsoft.AspNetCore.Components.Web;
using Microsoft.AspNetCore.Components.Forms;
using Microsoft.JSInterop;
using System.Text.Json;
namespace RistWorld.Components;
public partial class WorldMap:IDisposable
{
 [Inject] public WorldSession Session{get;set;}=default!;
 [Inject] public IJSRuntime JS{get;set;}=default!;
 readonly MapGestureState G=new();
 ElementReference MapElement;
  ElementReference WorldBoundsElement;
 AtlasTile? AtlasDragging;
 StagedAsset? TrayDragging;
 PieceItem? PieceDragging;
 TileItem? TileDragging;
 double DragClientX;
 double DragClientY;
 double DragStartX;
 double DragStartY;
 bool DragMoved;
 CancellationTokenSource? TileHoldCts;
 double TileHoldStartX;
 double TileHoldStartY;
 bool TileHoldTriggered;
 string BrowserLayer="WORLD";
 string BrowserDirectory="Terrain";
 string BrowserFolder="";
 bool ImportingTileset;
 string ImportStatus="";
 string SelectedSavedFilter="";
 string SelectedTileTool="draw";
 readonly List<SavedTileFilter> SavedFilters=[];
 bool FilterStateLoaded;
 const string FilterSaveKey="rist.tile.filters.v1";
 bool Dragging=>AtlasDragging is not null||TrayDragging is not null||PieceDragging is not null||TileDragging is not null;

 IEnumerable<string> BrowserLayers=>Session.AtlasTiles.Select(x=>x.Layer).Distinct(StringComparer.OrdinalIgnoreCase).Order();
 IEnumerable<AtlasTile> LayerTiles=>Session.AtlasTiles.Where(x=>x.Layer.Equals(BrowserLayer,StringComparison.OrdinalIgnoreCase));
 IEnumerable<string> BrowserDirectories=>LayerTiles.Select(x=>x.Directory).Distinct(StringComparer.OrdinalIgnoreCase).Order();
 IEnumerable<AtlasTile> DirectoryTiles=>LayerTiles.Where(x=>x.Directory.Equals(BrowserDirectory,StringComparison.OrdinalIgnoreCase));
 IEnumerable<string> BrowserFolders=>DirectoryTiles.Select(x=>x.Folder).Distinct(StringComparer.OrdinalIgnoreCase).Order();
 IEnumerable<AtlasTile> BrowserTiles=>string.IsNullOrWhiteSpace(BrowserFolder)?Enumerable.Empty<AtlasTile>():DirectoryTiles.Where(x=>x.Folder.Equals(BrowserFolder,StringComparison.OrdinalIgnoreCase));

 protected override void OnInitialized(){Session.ViewZoom=G.Zoom;Session.Changed+=Refresh;}
 protected override async Task OnAfterRenderAsync(bool firstRender)
 {
  if(!firstRender||FilterStateLoaded)return;FilterStateLoaded=true;
  var json=await JS.InvokeAsync<string?>("localStorage.getItem",FilterSaveKey);
  if(!string.IsNullOrWhiteSpace(json))
  {
   var saved=JsonSerializer.Deserialize<List<SavedTileFilter>>(json);
   if(saved is not null)SavedFilters.AddRange(saved.Where(x=>!string.IsNullOrWhiteSpace(x.Folder)));
  }
  StateHasChanged();
 }
 void Refresh()=>InvokeAsync(StateHasChanged);
 string StageTransform=>$"translate({G.PanX:0.##}px,{G.PanY:0.##}px) scale({G.Zoom:0.###})";
 string StatusText=>Session.EncounterActive?"ENCOUNTER • 5 ft/hex":Session.GridStyle=="none"?$"{Session.Layer} • grid off":$"{Session.Layer} • {WorldSession.GridColumns}×{WorldSession.GridRows} • {Session.EffectiveGridDistance:0.##} {Session.EffectiveGridUnit}/sq";
 static string Pct(double v)=>$"{v*100:0.###}%";
 static string PinStyle(PieceItem p)=>$"left:{Pct(p.X)};top:{Pct(p.Y)};--placement-zoom:{Math.Max(p.PlacementZoom,.01).ToString("0.###",CultureInfo.InvariantCulture)}";
 static string PieceStyle(PieceItem p)=>$"left:{Pct(p.X)};top:{Pct(p.Y)}";
 static string TileStyle(TileItem t)
 {
  var zoom=Math.Max(t.PlacementZoom,.01);var inv=CultureInfo.InvariantCulture;
  return $"left:{Pct(t.X)};top:{Pct(t.Y)};width:{(100.0/WorldSession.GridColumns/zoom).ToString("0.###",inv)}%;height:{(100.0/WorldSession.GridRows/zoom).ToString("0.###",inv)}%";
 }
 static string CropStyle(int sourceWidth,int sourceHeight,int cropX,int cropY,int cropWidth,int cropHeight)
 {
  if(sourceWidth<=0||sourceHeight<=0||cropWidth<=0||cropHeight<=0)return "";
  var inv=CultureInfo.InvariantCulture;
  return $"width:{(sourceWidth*100.0/cropWidth).ToString("0.###",inv)}%;height:{(sourceHeight*100.0/cropHeight).ToString("0.###",inv)}%;left:{(-cropX*100.0/cropWidth).ToString("0.###",inv)}%;top:{(-cropY*100.0/cropHeight).ToString("0.###",inv)}%;max-width:none;max-height:none";
 }
 static string CropStyle(AtlasTile t)=>CropStyle(t.SourceWidth,t.SourceHeight,t.CropX,t.CropY,t.CropWidth,t.CropHeight);
 static string CropStyle(StagedAsset t)=>CropStyle(t.SourceWidth,t.SourceHeight,t.CropX,t.CropY,t.CropWidth,t.CropHeight);
 static string CropBoxStyle(StagedAsset t)
 {
  if(t.CropWidth<=0||t.CropHeight<=0)return "";
  var scale=Math.Min(60.0/t.CropWidth,42.0/t.CropHeight);
  var inv=CultureInfo.InvariantCulture;
  return $"--crop-box-w:{(t.CropWidth*scale).ToString("0.###",inv)}px;--crop-box-h:{(t.CropHeight*scale).ToString("0.###",inv)}px";
 }
 static string CropStyle(TileItem t)=>CropStyle(t.SourceWidth,t.SourceHeight,t.CropX,t.CropY,t.CropWidth,t.CropHeight);
 static string RollStyle(RollItem r,DiceSpec die)
 {
  var col=r.Frame%die.Columns;var row=r.Frame/die.Columns;
  var bx=die.Columns<=1?0:col*100.0/(die.Columns-1);
  var by=die.Rows<=1?0:row*100.0/(die.Rows-1);
  return $"left:{Pct(r.X)};top:{Pct(r.Y)};background-image:url('{die.Image}?v=normalized-2');background-size:{die.Columns*100}% {die.Rows*100}%;background-position:{bx.ToString("0.###",CultureInfo.InvariantCulture)}% {by.ToString("0.###",CultureInfo.InvariantCulture)}%";
 }
 string DragPreviewStyle=>$"left:{DragClientX:0.#}px;top:{DragClientY:0.#}px";

 async Task<double[]> WorldPoint(PointerEventArgs e)=>await JS.InvokeAsync<double[]>("ristWorld.boundedWorldPoint",WorldBoundsElement,e.ClientX,e.ClientY);
 async Task<double[]> DropPoint(PointerEventArgs e)=>await JS.InvokeAsync<double[]>("ristWorld.boundedDropPoint",WorldBoundsElement,e.ClientX,e.ClientY);
 async Task<double[]> TileDropPoint(PointerEventArgs e)=>await JS.InvokeAsync<double[]>("ristWorld.boundedTileDropPoint",WorldBoundsElement,e.ClientX,e.ClientY,WorldSession.GridColumns,WorldSession.GridRows);
 async Task DropHeaderPin(DragEventArgs e){if(!Session.HeaderPinDragging)return;var p=await JS.InvokeAsync<double[]>("ristWorld.boundedDropPoint",WorldBoundsElement,e.ClientX,e.ClientY);if(p.Length>=3&&p[0]>.5)Session.PlaceHeaderPin(p[1],p[2]);else Session.EndHeaderPinDrag();}

 async Task StartDrag(PointerEventArgs e){DragClientX=DragStartX=e.ClientX;DragClientY=DragStartY=e.ClientY;DragMoved=false;await JS.InvokeVoidAsync("ristWorld.capturePointer",e.PointerId,e.ClientX,e.ClientY);}
 async Task BeginAtlasDrag(AtlasTile tile,PointerEventArgs e){AtlasDragging=tile;TrayDragging=null;PieceDragging=null;TileDragging=null;await StartDrag(e);}
 async Task BeginTrayDrag(StagedAsset staged,PointerEventArgs e){AtlasDragging=null;TrayDragging=staged;PieceDragging=null;TileDragging=null;await StartDrag(e);}
 async Task BeginPieceDrag(PieceItem piece,PointerEventArgs e){AtlasDragging=null;PieceDragging=piece;TrayDragging=null;TileDragging=null;await StartDrag(e);}
 async Task BeginTileDrag(TileItem tile,PointerEventArgs e)
 {
  if(!Session.CanEditTiles||Session.MapLocked)return;
  if(Session.RecursiveRegionSelectionMode){Session.ToggleRecursiveRegionTile(tile);return;}
  if(tile.Locked){Session.SelectTileZone(tile);return;}
  AtlasDragging=null;TileDragging=tile;TrayDragging=null;PieceDragging=null;await StartDrag(e);
 }
 async Task StartLockedTileHold(TileItem tile,PointerEventArgs e)
 {
  CancelTileHold();TileHoldCts=new();TileHoldStartX=e.ClientX;TileHoldStartY=e.ClientY;TileHoldTriggered=false;
  await JS.InvokeVoidAsync("ristWorld.capturePointer",e.PointerId,e.ClientX,e.ClientY);
  try
  {
   await Task.Delay(560,TileHoldCts.Token);
   TileHoldTriggered=true;
   ClearDrag();
   Session.OpenLockedTileMenu(tile);
   await InvokeAsync(StateHasChanged);
  }
  catch(OperationCanceledException){}
 }
 void CancelTileHold(){TileHoldCts?.Cancel();TileHoldCts?.Dispose();TileHoldCts=null;}
 void DragMove(PointerEventArgs e)
 {
  if(TileHoldCts is not null&&Math.Abs(e.ClientX-TileHoldStartX)+Math.Abs(e.ClientY-TileHoldStartY)>8)CancelTileHold();
  if(!Dragging)return;DragClientX=e.ClientX;DragClientY=e.ClientY;if(Math.Abs(DragClientX-DragStartX)+Math.Abs(DragClientY-DragStartY)>7)DragMoved=true;StateHasChanged();
 }

 async Task DragEnd(PointerEventArgs e)
 {
  CancelTileHold();
  if(!Dragging)return;
  DragClientX=e.ClientX;DragClientY=e.ClientY;
  if(!DragMoved){ClearDrag();await InvokeAsync(StateHasChanged);return;}
  var droppingTile=TrayDragging?.Kind=="tile"||TileDragging is not null;
  var p=droppingTile?await TileDropPoint(e):await DropPoint(e);
  var inside=p.Length>=3&&p[0]>.5;
  var overPallet=await JS.InvokeAsync<bool>("ristWorld.overPallet",e.ClientX,e.ClientY);
  if(AtlasDragging is not null){if(overPallet)Session.StageTile(AtlasDragging);}
  else if(TrayDragging is not null){if(inside)Session.PlaceStaged(TrayDragging,p[1],p[2],G.Zoom);else if(!overPallet)Session.RemoveStaged(TrayDragging.Key);}
  else if(PieceDragging is not null){if(inside)Session.MovePiece(PieceDragging,p[1],p[2]);else Session.RemovePiece(PieceDragging);}
  else if(TileDragging is not null){if(inside)Session.MoveTile(TileDragging,p[1],p[2]);else Session.RemoveTile(TileDragging);}
  ClearDrag();
  await InvokeAsync(StateHasChanged);
 }
 void DragCancel(PointerEventArgs e){CancelTileHold();if(Dragging){ClearDrag();StateHasChanged();}}
 void ClearDrag(){AtlasDragging=null;TrayDragging=null;PieceDragging=null;TileDragging=null;DragMoved=false;}

 void LayerChanged(ChangeEventArgs e){BrowserLayer=e.Value?.ToString()??"WORLD";BrowserDirectory=BrowserDirectories.FirstOrDefault()??"";BrowserFolder="";}
 void DirectoryChanged(ChangeEventArgs e){BrowserDirectory=e.Value?.ToString()??"";BrowserFolder="";}
 void FolderChanged(ChangeEventArgs e)=>BrowserFolder=e.Value?.ToString()??"";
 void TileToolChanged(ChangeEventArgs e)=>SelectedTileTool=e.Value?.ToString()??"draw";
 async Task SaveCurrentFilter()
 {
  if(string.IsNullOrWhiteSpace(BrowserFolder))return;
  var filter=new SavedTileFilter(BrowserLayer,BrowserDirectory,BrowserFolder);
  SavedFilters.RemoveAll(x=>x.Key==filter.Key);SavedFilters.Add(filter);SelectedSavedFilter=filter.Key;
  await JS.InvokeVoidAsync("localStorage.setItem",FilterSaveKey,JsonSerializer.Serialize(SavedFilters));
 }
 void ApplySavedFilter(ChangeEventArgs e)
 {
  SelectedSavedFilter=e.Value?.ToString()??"";var filter=SavedFilters.FirstOrDefault(x=>x.Key==SelectedSavedFilter);if(filter is null)return;
  BrowserLayer=filter.Layer;BrowserDirectory=filter.Directory;BrowserFolder=filter.Folder;
 }
 async Task ImportTileset(InputFileChangeEventArgs e)
 {
  ImportingTileset=true;ImportStatus="Analyzing tileset…";StateHasChanged();
  try
  {
   var file=e.File;
   await using var stream=file.OpenReadStream(12*1024*1024);
   using var memory=new MemoryStream();await stream.CopyToAsync(memory);
   var dataUrl=$"data:{file.ContentType};base64,{Convert.ToBase64String(memory.ToArray())}";
   var slices=await JS.InvokeAsync<string[]>("ristWorld.splitTileset",dataUrl);
   var stem=Path.GetFileNameWithoutExtension(file.Name);
   var folder=string.IsNullOrWhiteSpace(stem)?"Uploaded tileset":stem;
   var added=Session.ImportTileset(folder,slices);
   BrowserLayer="UNIVERSAL";BrowserDirectory="Imported";BrowserFolder=folder;
   ImportStatus=added==0?"No separate tiles were detected.":$"Added {added} tile{(added==1?"":"s")} to Imported › {folder}.";
  }
  catch(Exception ex){ImportStatus=ex.Message.Contains("maximum",StringComparison.OrdinalIgnoreCase)?"Tileset is larger than the 12 MB upload limit.":"This image could not be analyzed.";}
  finally{ImportingTileset=false;StateHasChanged();}
 }
 static string Pretty(string value)=>System.Globalization.CultureInfo.InvariantCulture.TextInfo.ToTitleCase(value.ToLowerInvariant());

 async Task ZoomAt(double? clientX,double? clientY,double targetZoom)
 {
  var next=Math.Clamp(targetZoom,.5,5);
  if(Math.Abs(next-G.Zoom)<.0001)return;
  var pan=await JS.InvokeAsync<double[]>("ristWorld.zoomPan",MapElement,clientX,clientY,G.PanX,G.PanY,G.Zoom,next);
  if(pan.Length>=2){G.PanX=pan[0];G.PanY=pan[1];}
  G.Zoom=next;Session.ViewZoom=G.Zoom;Session.Notify();
 }
 async Task ZoomIn()=>await ZoomAt(null,null,G.Zoom*1.2);
 async Task ZoomOut()=>await ZoomAt(null,null,G.Zoom/1.2);
 async Task Wheel(WheelEventArgs e)
 {
  if(Dragging)return;
  var factor=Math.Exp(-e.DeltaY*.0015);
  await ZoomAt(e.ClientX,e.ClientY,G.Zoom*factor);
 }
 async Task KeyDown(KeyboardEventArgs e)
 {
  if(e.Key=="Escape")
  {
   CancelTileHold();ClearDrag();G.Pointers.Clear();G.LastDistance=0;
   if(Session.RecursiveRegionSelectionMode)Session.CancelRecursiveRegionSelection();
   if(Session.LockedTileMenuOpen)Session.CloseLockedTileMenu();
   await InvokeAsync(StateHasChanged);return;
  }
  if(await JS.InvokeAsync<bool>("ristWorld.isTyping"))return;
  var key=(e.Key??string.Empty).ToLowerInvariant();
  var step=e.ShiftKey?120:48;
  switch(key)
  {
   case "arrowleft":case "a":G.PanX+=step;break;
   case "arrowright":case "d":G.PanX-=step;break;
   case "arrowup":case "w":G.PanY+=step;break;
   case "arrowdown":case "s":G.PanY-=step;break;
   case "+":case "=":await ZoomAt(null,null,G.Zoom*1.2);return;
   case "-":case "_":await ZoomAt(null,null,G.Zoom/1.2);return;
   case "0":G.PanX=0;G.PanY=0;G.Zoom=1;Session.ViewZoom=1;Session.Notify();return;
   default:return;
  }
  Session.Notify();
 }

 async Task Down(PointerEventArgs e)
 {
  if(Dragging)return;
  G.Pointers[e.PointerId]=(e.ClientX,e.ClientY);G.Moved=false;
  if(G.Pointers.Count==1){G.LastX=e.ClientX;G.LastY=e.ClientY;}
  if(G.Pointers.Count==2)G.LastDistance=G.Distance();
 }
 Task Move(PointerEventArgs e)
 {
  if(Dragging)return Task.CompletedTask;
  if(!G.Pointers.ContainsKey(e.PointerId))return Task.CompletedTask;
  G.Pointers[e.PointerId]=(e.ClientX,e.ClientY);
  if(G.Pointers.Count==1)Pan(e);else if(G.Pointers.Count>=2)Pinch();
  return Task.CompletedTask;
 }
 void Pan(PointerEventArgs e){var dx=e.ClientX-G.LastX;var dy=e.ClientY-G.LastY;if(Math.Abs(dx)+Math.Abs(dy)>1){G.PanX+=dx;G.PanY+=dy;G.Moved=true;}G.LastX=e.ClientX;G.LastY=e.ClientY;}
 void Pinch(){var d=G.Distance();if(G.LastDistance>0){G.Zoom=Math.Clamp(G.Zoom*(d/G.LastDistance),.5,5);Session.ViewZoom=G.Zoom;Session.Notify();G.Moved=true;}G.LastDistance=d;}
 async Task Up(PointerEventArgs e)
 {
  var held=TileHoldTriggered;CancelTileHold();TileHoldTriggered=false;if(held)return;
  if(Session.HeaderPinDragging)
  {
   var pinDrop=await DropPoint(e);
   if(pinDrop.Length>=3&&pinDrop[0]>.5)Session.PlaceHeaderPin(pinDrop[1],pinDrop[2]);else Session.EndHeaderPinDrag();
   return;
  }
  if(Dragging){await DragEnd(e);return;}
  var wasTracked=G.Pointers.ContainsKey(e.PointerId);var wasMoved=G.Moved;
  G.Pointers.Remove(e.PointerId);G.LastDistance=0;
  if(wasTracked&&!wasMoved&&G.Pointers.Count==0){var p=await WorldPoint(e);Session.MapTap(p[0],p[1]);}
 }
 void Cancel(PointerEventArgs e){CancelTileHold();G.Pointers.Remove(e.PointerId);G.LastDistance=0;}
 void PinTap(PieceItem p)=>Session.PinTap(p);
 public void Dispose(){CancelTileHold();Session.Changed-=Refresh;}
}
public sealed record SavedTileFilter(string Layer,string Directory,string Folder)
{
 public string Key=>$"{Layer}|{Directory}|{Folder}";
 public string Label=>$"{CultureInfo.InvariantCulture.TextInfo.ToTitleCase(Layer.ToLowerInvariant())} › {Directory} › {Folder}";
}
