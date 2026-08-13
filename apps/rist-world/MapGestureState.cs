namespace RistWorld;
public sealed class MapGestureState
{
 public double PanX{get;set;} public double PanY{get;set;} public double Zoom{get;set;}=1;
 public Dictionary<long,(double X,double Y)> Pointers{get;}=[];
 public double LastX{get;set;} public double LastY{get;set;} public double LastDistance{get;set;} public bool Moved{get;set;}
 public double Distance(){var p=Pointers.Values.Take(2).ToArray();if(p.Length<2)return 0;var dx=p[0].X-p[1].X;var dy=p[0].Y-p[1].Y;return Math.Sqrt(dx*dx+dy*dy);}
}
