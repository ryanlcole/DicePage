namespace RistWorld;

public readonly record struct MapCell(int Column,int Row);

public sealed partial class WorldSession
{
    const string ImplicitOceanTerrain = "__ocean071__";

    public MapCell CellFromNormalized(double x,double y)
    {
        var column=Math.Clamp((int)Math.Floor(Math.Clamp(x,0,.999999)*GridColumns),0,GridColumns-1);
        var row=Math.Clamp((int)Math.Floor(Math.Clamp(y,0,.999999)*GridRows),0,GridRows-1);
        return new(column,row);
    }

    public (double X,double Y) CellCenter(MapCell cell)=>
        ((Math.Clamp(cell.Column,0,GridColumns-1)+.5)/GridColumns,
         (Math.Clamp(cell.Row,0,GridRows-1)+.5)/GridRows);

    public bool ApplyTileTool(string tool,StagedAsset? staged,MapCell start,MapCell end,double placementZoom)
    {
        if(!CanEditTiles||MapLocked)return false;
        tool=(tool??"draw").Trim().ToLowerInvariant();
        if(tool!="erase"&&(staged is null||staged.Kind!="tile"))return false;
        if(staged is not null&&Role=="PC"&&staged.ApprovalStatus!=HandCard.Approved)return false;

        IReadOnlyCollection<MapCell> cells=tool switch
        {
            "brush"=>BrushPath(start,end,1),
            "fill"=>FloodRegion(start),
            "line"=>LineCells(start,end),
            "square"=>RectanglePerimeter(start,end),
            "circle"=>CirclePerimeter(start,end),
            "erase"=>LineCells(start,end),
            _=>LineCells(start,end)
        };

        var changed=tool=="erase"?EraseCells(cells):PaintCells(staged!,cells,placementZoom);
        if(changed)Notify();
        return changed;
    }

    bool PaintCells(StagedAsset staged,IEnumerable<MapCell> cells,double placementZoom)
    {
        var changed=false;
        foreach(var cell in cells.Distinct())
        {
            if(!ValidCell(cell))continue;
            var existing=TilesAtCell(cell).ToList();
            if(existing.Any(x=>x.Locked))continue;
            var same=existing.Count==1&&existing[0].Id.Equals(staged.Key[5..],StringComparison.Ordinal);
            if(same)continue;
            foreach(var tile in existing)PlacedTiles.Remove(tile);
            var (x,y)=CellCenter(cell);
            PlacedTiles.Add(new(staged.Key[5..],staged.Name,staged.Image,x,y,staged.SourceWidth,staged.SourceHeight,staged.CropX,staged.CropY,staged.CropWidth,staged.CropHeight,Math.Max(placementZoom,.01)));
            changed=true;
        }
        return changed;
    }

    bool EraseCells(IEnumerable<MapCell> cells)
    {
        var changed=false;
        foreach(var cell in cells.Distinct())
        {
            foreach(var tile in TilesAtCell(cell).Where(x=>!x.Locked).ToList())
            {
                PlacedTiles.Remove(tile);
                changed=true;
            }
        }
        return changed;
    }

    IEnumerable<TileItem> TilesAtCell(MapCell cell)=>PlacedTiles.Where(tile=>CellFromNormalized(tile.X,tile.Y)==cell);

    string TerrainAt(MapCell cell)
    {
        var tile=TilesAtCell(cell).LastOrDefault();
        return tile?.Id??ImplicitOceanTerrain;
    }

    IReadOnlyCollection<MapCell> FloodRegion(MapCell start)
    {
        if(!ValidCell(start))return Array.Empty<MapCell>();
        var terrain=TerrainAt(start);
        var result=new HashSet<MapCell>();
        var queue=new Queue<MapCell>();
        queue.Enqueue(start);result.Add(start);
        ReadOnlySpan<(int X,int Y)> directions=[(1,0),(-1,0),(0,1),(0,-1)];
        while(queue.Count>0)
        {
            var current=queue.Dequeue();
            foreach(var (dx,dy) in directions)
            {
                var next=new MapCell(current.Column+dx,current.Row+dy);
                if(!ValidCell(next)||result.Contains(next)||TerrainAt(next)!=terrain)continue;
                result.Add(next);queue.Enqueue(next);
            }
        }
        return result;
    }

    static IReadOnlyCollection<MapCell> LineCells(MapCell a,MapCell b)
    {
        var result=new List<MapCell>();
        var x0=a.Column;var y0=a.Row;var x1=b.Column;var y1=b.Row;
        var dx=Math.Abs(x1-x0);var sx=x0<x1?1:-1;var dy=-Math.Abs(y1-y0);var sy=y0<y1?1:-1;var error=dx+dy;
        while(true)
        {
            result.Add(new(x0,y0));if(x0==x1&&y0==y1)break;
            var twice=2*error;if(twice>=dy){error+=dy;x0+=sx;}if(twice<=dx){error+=dx;y0+=sy;}
        }
        return result;
    }

    static IReadOnlyCollection<MapCell> BrushPath(MapCell a,MapCell b,int radius)
    {
        var result=new HashSet<MapCell>();
        foreach(var center in LineCells(a,b))
            for(var y=-radius;y<=radius;y++)for(var x=-radius;x<=radius;x++)result.Add(new(center.Column+x,center.Row+y));
        return result;
    }

    static IReadOnlyCollection<MapCell> RectanglePerimeter(MapCell a,MapCell b)
    {
        var result=new HashSet<MapCell>();
        var left=Math.Min(a.Column,b.Column);var right=Math.Max(a.Column,b.Column);var top=Math.Min(a.Row,b.Row);var bottom=Math.Max(a.Row,b.Row);
        for(var x=left;x<=right;x++){result.Add(new(x,top));result.Add(new(x,bottom));}
        for(var y=top;y<=bottom;y++){result.Add(new(left,y));result.Add(new(right,y));}
        return result;
    }

    static IReadOnlyCollection<MapCell> CirclePerimeter(MapCell center,MapCell edge)
    {
        var result=new HashSet<MapCell>();
        var radius=Math.Max(1,(int)Math.Round(Math.Sqrt(Math.Pow(edge.Column-center.Column,2)+Math.Pow(edge.Row-center.Row,2))));
        var x=radius;var y=0;var error=1-radius;
        while(x>=y)
        {
            AddCircleOctants(result,center,x,y);y++;
            if(error<0)error+=2*y+1;else{x--;error+=2*(y-x)+1;}
        }
        return result;
    }

    static void AddCircleOctants(HashSet<MapCell> cells,MapCell c,int x,int y)
    {
        cells.Add(new(c.Column+x,c.Row+y));cells.Add(new(c.Column+y,c.Row+x));cells.Add(new(c.Column-y,c.Row+x));cells.Add(new(c.Column-x,c.Row+y));
        cells.Add(new(c.Column-x,c.Row-y));cells.Add(new(c.Column-y,c.Row-x));cells.Add(new(c.Column+y,c.Row-x));cells.Add(new(c.Column+x,c.Row-y));
    }

    static bool ValidCell(MapCell cell)=>cell.Column>=0&&cell.Column<GridColumns&&cell.Row>=0&&cell.Row<GridRows;
}
