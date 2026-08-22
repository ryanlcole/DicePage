using System.Text.Json;

namespace RistWorld;

public sealed partial class WorldSession
{
    public bool StandardGameActive { get; private set; }
    public bool StandardDrawOnly { get; private set; }
    public List<CardItem> StandardHandCards { get; } = [];
    public Dictionary<string,int> StandardTypeCounts { get; } = new(StringComparer.OrdinalIgnoreCase);
    private readonly List<CardItem> _standardDrawPile = [];

    public IEnumerable<string> StandardCardTypes
        => Cards.Select(x=>x.Type).Where(x=>!string.IsNullOrWhiteSpace(x)).Distinct(StringComparer.OrdinalIgnoreCase).OrderBy(x=>x);

    public int StandardTypeCount(string type)
        => StandardTypeCounts.TryGetValue(type,out var count)?count:0;

    public void SetStandardTypeCount(string type,int count)
    {
        StandardTypeCounts[type]=Math.Clamp(count,0,120);
        Notify();
    }

    public void SetStandardDrawOnly(bool value)
    {
        StandardDrawOnly=value;
        Notify();
    }

    public void StartStandardGame()
    {
        _standardDrawPile.Clear();
        StandardHandCards.Clear();
        foreach(var type in StandardCardTypes)
        {
            var requested=StandardTypeCount(type);
            if(requested<=0)continue;
            var source=Cards.Where(x=>x.Type.Equals(type,StringComparison.OrdinalIgnoreCase)).ToList();
            if(source.Count==0)continue;
            for(var i=0;i<requested;i++)_standardDrawPile.Add(source[i%source.Count]);
        }
        ShuffleStandardPile();
        StandardGameActive=true;
        HandOpen=false;
        Notify();
    }

    public void EndStandardGame()
    {
        StandardGameActive=false;
        StandardHandCards.Clear();
        _standardDrawPile.Clear();
        HandOpen=true;
        Notify();
    }

    public void StandardDeckClick()
    {
        if(StandardGameActive&&StandardDrawOnly)DrawRandomStandardCard();
        else ToggleHand();
    }

    public void DrawRandomStandardCard()
    {
        if(!StandardGameActive||_standardDrawPile.Count==0)return;
        var index=Random.Shared.Next(_standardDrawPile.Count);
        StandardHandCards.Add(_standardDrawPile[index]);
        _standardDrawPile.RemoveAt(index);
        Notify();
    }

    public string SaveStandardDeckJson()
        => JsonSerializer.Serialize(new StandardDeckSave{DrawOnly=StandardDrawOnly,TypeCounts=new(StandardTypeCounts)});

    public void LoadStandardDeckJson(string json)
    {
        try
        {
            var save=JsonSerializer.Deserialize<StandardDeckSave>(json);
            if(save is null)return;
            StandardDrawOnly=save.DrawOnly;
            StandardTypeCounts.Clear();
            foreach(var pair in save.TypeCounts)StandardTypeCounts[pair.Key]=Math.Clamp(pair.Value,0,120);
            Notify();
        }
        catch { }
    }

    private void ShuffleStandardPile()
    {
        for(var i=_standardDrawPile.Count-1;i>0;i--)
        {
            var j=Random.Shared.Next(i+1);
            (_standardDrawPile[i],_standardDrawPile[j])=(_standardDrawPile[j],_standardDrawPile[i]);
        }
    }

    private sealed class StandardDeckSave
    {
        public bool DrawOnly { get; set; }
        public Dictionary<string,int> TypeCounts { get; set; } = new(StringComparer.OrdinalIgnoreCase);
    }
}
