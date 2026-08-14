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
 bool PinDragging;
 long? PinPointerId;
 double PinScreenX;
 double PinScreenY;

 protected override void OnInitialized(){Session.ViewZoom=G.Zoom;Session.Changed+=Refresh;}
 void Refresh()=>InvokeAsync(StateHasChanged);
 string StageTransform=>$"translate({G.PanX:0.##}px,{G.PanY:0.##}px) scale({G.Zoom:0.###})";
 string StatusText=>Session.EncounterActive?"ENCOUNTER • 5 ft/hex":Session.GridStyle=="none"?$"{Session.Layer} • grid off":$"{Session.Layer} • {WorldSession.GridColumns}×{WorldSession.GridRows} • {Session.EffectiveGridDistance:0.##} {Session.EffectiveGridUnit}/sq";
 static string Pct(double v)=>$"{v*100:0.###}%";
 static string PinStyle(PieceItem p)=>$"left:{Pct(p.X)};top:{Pct(p.Y)};--placement-zoom:{Math.Max(p.PlacementZoom,.01).ToString("0.###",CultureInfo.InvariantCulture)}";
 bool IsPinPlacement=>Session.Role=="GM"&&Session.Mode=="piece"&&Session.PieceKind=="pin";

 async Task<double[]> ScreenPoint(PointerEventArgs e)=>await JS.InvokeAsync<double[]>("ristWorld.point",MapElement,e.ClientX,e.ClientY);
 async Task<double[]> WorldPoint(PointerEventArgs e)=>await JS.InvokeAsync<double[]>("ristWorld.worldPoint",MapElement,e.ClientX,e.ClientY,G.PanX,G.PanY,G.Zoom);

 async Task UpdatePinPreview(PointerEventArgs e)
 {
  var p=await ScreenPoint(e);
  PinScreenX=Math.Clamp(p[0],0,1);
  PinScreenY=Math.Clamp(p[1],0,1);
  await InvokeAsync(StateHasChanged);
 }

 async Task Down(PointerEventArgs e)
 {
  if(IsPinPlacement&&G.Pointers.Count==0)
  {
   PinDragging=true;
   PinPointerId=e.PointerId;
   await UpdatePinPreview(e);
   return;
  }
  G.Pointers[e.PointerId]=(e.ClientX,e.ClientY);G.Moved=false;
  if(G.Pointers.Count==1){G.LastX=e.ClientX;G.LastY=e.ClientY;}
  if(G.Pointers.Count==2)G.LastDistance=G.Distance();
 }

 async Task Move(PointerEventArgs e)
 {
  if(PinDragging&&PinPointerId==e.PointerId){await UpdatePinPreview(e);return;}
  if(!G.Pointers.ContainsKey(e.PointerId))return;
  G.Pointers[e.PointerId]=(e.ClientX,e.ClientY);
  if(G.Pointers.Count==1)Pan(e);else if(G.Pointers.Count>=2)Pinch();
 }

 void Pan(PointerEventArgs e){var dx=e.ClientX-G.LastX;var dy=e.ClientY-G.LastY;if(Math.Abs(dx)+Math.Abs(dy)>1){G.PanX+=dx;G.PanY+=dy;G.Moved=true;}G.LastX=e.ClientX;G.LastY=e.ClientY;}
 void Pinch(){var d=G.Distance();if(G.LastDistance>0){G.Zoom=Math.Clamp(G.Zoom*(d/G.LastDistance),.5,5);Session.ViewZoom=G.Zoom;Session.Notify();G.Moved=true;}G.LastDistance=d;}

 async Task Up(PointerEventArgs e)
 {
  if(PinDragging&&PinPointerId==e.PointerId)
  {
   var p=await WorldPoint(e);
   Session.PlacePin(p[0],p[1],G.Zoom);
   PinDragging=false;PinPointerId=null;
   await InvokeAsync(StateHasChanged);
   return;
  }
  var wasTracked=G.Pointers.ContainsKey(e.PointerId);
  var wasMoved=G.Moved;
  G.Pointers.Remove(e.PointerId);G.LastDistance=0;
  if(wasTracked&&!wasMoved&&G.Pointers.Count==0)
  {
   var p=await WorldPoint(e);
   Session.MapTap(p[0],p[1]);
  }
 }

 void Cancel(PointerEventArgs e)
 {
  if(PinDragging&&PinPointerId==e.PointerId){PinDragging=false;PinPointerId=null;}
  G.Pointers.Remove(e.PointerId);G.LastDistance=0;
 }
 void PinTap(PieceItem p)=>Session.PinTap(p);
 public void Dispose()=>Session.Changed-=Refresh;
}
