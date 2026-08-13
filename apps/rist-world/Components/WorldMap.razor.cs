using Microsoft.AspNetCore.Components;
using Microsoft.AspNetCore.Components.Web;
namespace RistWorld.Components;
public partial class WorldMap:IDisposable
{
 [Inject] public WorldSession Session{get;set;}=default!;
 readonly MapGestureState G=new();
 protected override void OnInitialized(){Session.ViewZoom=G.Zoom;Session.Changed+=Refresh;}
 void Refresh()=>InvokeAsync(StateHasChanged);
 string StageTransform=>$"translate({G.PanX:0.##}px,{G.PanY:0.##}px) scale({G.Zoom:0.###})";
 string GridStatus=>Session.GridStyle=="none"?"grid off":$"10×20 • {Session.EffectiveGridDistance:0.##} mi/cell";
 static string Pct(double v)=>$"{v*100:0.###}%";
 void Down(PointerEventArgs e){G.Pointers[e.PointerId]=(e.ClientX,e.ClientY);G.Moved=false;if(G.Pointers.Count==1){G.LastX=e.ClientX;G.LastY=e.ClientY;}if(G.Pointers.Count==2)G.LastDistance=G.Distance();}
 void Move(PointerEventArgs e){if(!G.Pointers.ContainsKey(e.PointerId))return;G.Pointers[e.PointerId]=(e.ClientX,e.ClientY);if(G.Pointers.Count==1)Pan(e);else if(G.Pointers.Count>=2)Pinch();}
 void Pan(PointerEventArgs e){var dx=e.ClientX-G.LastX;var dy=e.ClientY-G.LastY;if(Math.Abs(dx)+Math.Abs(dy)>1){G.PanX+=dx;G.PanY+=dy;G.Moved=true;}G.LastX=e.ClientX;G.LastY=e.ClientY;}
 void Pinch(){var d=G.Distance();if(G.LastDistance>0){G.Zoom=Math.Clamp(G.Zoom*(d/G.LastDistance),.5,5);Session.ViewZoom=G.Zoom;Session.Notify();G.Moved=true;}G.LastDistance=d;}
 void Up(PointerEventArgs e){G.Pointers.Remove(e.PointerId);G.LastDistance=0;}
 void Cancel(PointerEventArgs e){G.Pointers.Remove(e.PointerId);G.LastDistance=0;}
 void PinTap(PieceItem p)=>Session.PinTap(p);
 public void Dispose()=>Session.Changed-=Refresh;
}
