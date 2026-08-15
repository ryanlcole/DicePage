using System.Globalization;
using Microsoft.AspNetCore.Components;
using Microsoft.AspNetCore.Components.Web;
using Microsoft.JSInterop;
namespace RistWorld.Components;
public partial class WorldMap:IDisposable
{
 [Inject] public WorldSession Session{get;set;}=default!;
 [Inject] public IJSRuntime JS{get;set;}=default!;
 readonly MapGestureState G=new();
 ElementReference MapElement;
 StagedAsset? TrayDragging;
 PieceItem? PieceDragging;
 TileItem? TileDragging;
 double DragClientX;
 double DragClientY;
 bool Dragging=>TrayDragging is not null||PieceDragging is not null||TileDragging is not null;

 protected override void OnInitialized(){Session.ViewZoom=G.Zoom;Session.Changed+=Refresh;}
 void Refresh()=>InvokeAsync(StateHasChanged);
 string StageTransform=>$"translate({G.PanX:0.##}px,{G.PanY:0.##}px) scale({G.Zoom:0.###})";
 string StatusText=>Session.EncounterActive?"ENCOUNTER • 5 ft/hex":Session.GridStyle=="none"?$"{Session.Layer} • grid off":$"{Session.Layer} • {WorldSession.GridColumns}×{WorldSession.GridRows} • {Session.EffectiveGridDistance:0.##} {Session.EffectiveGridUnit}/sq";
 static string Pct(double v)=>$"{v*100:0.###}%";
 static string PinStyle(PieceItem p)=>$"left:{Pct(p.X)};top:{Pct(p.Y)};--placement-zoom:{Math.Max(p.PlacementZoom,.01).ToString("0.###",CultureInfo.InvariantCulture)}";
 static string PieceStyle(PieceItem p)=>$"left:{Pct(p.X)};top:{Pct(p.Y)}";
 static string TileStyle(TileItem t)=>$"left:{Pct(t.X)};top:{Pct(t.Y)}";
 static string RollStyle(RollItem r,DiceSpec die)
 {
  var col=r.Frame%die.Columns;var row=r.Frame/die.Columns;
  var bx=die.Columns<=1?0:col*100.0/(die.Columns-1);
  var by=die.Rows<=1?0:row*100.0/(die.Rows-1);
  return $"left:{Pct(r.X)};top:{Pct(r.Y)};--die-aspect:{die.VisualAspect.ToString("0.###",CultureInfo.InvariantCulture)};background-image:url('{die.Image}?v=normalized-2');background-size:{die.Columns*100}% {die.Rows*100}%;background-position:{bx.ToString("0.###",CultureInfo.InvariantCulture)}% {by.ToString("0.###",CultureInfo.InvariantCulture)}%";
 }
 string DragPreviewStyle=>$"left:{DragClientX:0.#}px;top:{DragClientY:0.#}px";

 async Task<double[]> WorldPoint(PointerEventArgs e)=>await JS.InvokeAsync<double[]>("ristWorld.worldPoint",MapElement,e.ClientX,e.ClientY,G.PanX,G.PanY,G.Zoom);
 async Task<double[]> DropPoint(PointerEventArgs e)=>await JS.InvokeAsync<double[]>("ristWorld.dropPoint",MapElement,e.ClientX,e.ClientY,G.PanX,G.PanY,G.Zoom);

 void BeginTrayDrag(StagedAsset staged,PointerEventArgs e){TrayDragging=staged;PieceDragging=null;TileDragging=null;DragClientX=e.ClientX;DragClientY=e.ClientY;}
 void BeginPieceDrag(PieceItem piece,PointerEventArgs e){PieceDragging=piece;TrayDragging=null;TileDragging=null;DragClientX=e.ClientX;DragClientY=e.ClientY;}
 void BeginTileDrag(TileItem tile,PointerEventArgs e){TileDragging=tile;TrayDragging=null;PieceDragging=null;DragClientX=e.ClientX;DragClientY=e.ClientY;}
 void DragMove(PointerEventArgs e){if(!Dragging)return;DragClientX=e.ClientX;DragClientY=e.ClientY;StateHasChanged();}

 async Task DragEnd(PointerEventArgs e)
 {
  if(!Dragging)return;
  DragClientX=e.ClientX;DragClientY=e.ClientY;
  var p=await DropPoint(e);
  var inside=p.Length>=3&&p[0]>.5;
  if(TrayDragging is not null){if(inside)Session.PlaceStaged(TrayDragging,p[1],p[2],G.Zoom);}
  else if(PieceDragging is not null){if(inside)Session.MovePiece(PieceDragging,p[1],p[2]);else Session.RemovePiece(PieceDragging);}
  else if(TileDragging is not null){if(inside)Session.MoveTile(TileDragging,p[1],p[2]);else Session.RemoveTile(TileDragging);}
  ClearDrag();
  await InvokeAsync(StateHasChanged);
 }
 void DragCancel(PointerEventArgs e){if(Dragging){ClearDrag();StateHasChanged();}}
 void ClearDrag(){TrayDragging=null;PieceDragging=null;TileDragging=null;}

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
  if(Dragging){await DragEnd(e);return;}
  var wasTracked=G.Pointers.ContainsKey(e.PointerId);var wasMoved=G.Moved;
  G.Pointers.Remove(e.PointerId);G.LastDistance=0;
  if(wasTracked&&!wasMoved&&G.Pointers.Count==0){var p=await WorldPoint(e);Session.MapTap(p[0],p[1]);}
 }
 void Cancel(PointerEventArgs e){G.Pointers.Remove(e.PointerId);G.LastDistance=0;}
 void PinTap(PieceItem p)=>Session.PinTap(p);
 public void Dispose()=>Session.Changed-=Refresh;
}
