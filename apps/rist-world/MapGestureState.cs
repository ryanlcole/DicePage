namespace RistWorld;

public sealed class MapGestureState
{
    public double PanX { get; set; }
    public double PanY { get; set; }
    public double Zoom { get; set; } = 1;
    public Dictionary<long,(double X,double Y)> Pointers { get; } = [];
    public double LastX { get; set; }
    public double LastY { get; set; }
    public double LastDistance { get; set; }
    public bool Moved { get; set; }

    public double Distance()
    {
        if (Pointers.Count < 2) return 0;
        using var points = Pointers.Values.GetEnumerator();
        if (!points.MoveNext()) return 0;
        var first = points.Current;
        if (!points.MoveNext()) return 0;
        var second = points.Current;
        var dx = first.X - second.X;
        var dy = first.Y - second.Y;
        return Math.Sqrt(dx*dx + dy*dy);
    }
}
