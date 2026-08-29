namespace RistWorld;

public sealed partial class WorldSession
{
    public List<RollHistoryBatch> RollHistoryBatches { get; } = [];
    public string ActiveRollCardName { get; private set; } = "";
    private RollHistoryBatch? _activeRollBatch;

    private RollHistoryBatch EnsureRollHistoryBatch()
    {
        if(_activeRollBatch is not null)return _activeRollBatch;
        _activeRollBatch = new RollHistoryBatch
        {
            CharacterName = string.IsNullOrWhiteSpace(CharacterName) ? "Character" : CharacterName.Trim()
        };
        RollHistoryBatches.Add(_activeRollBatch);
        return _activeRollBatch;
    }

    private void RecordRollHistory(DiceSpec die,int value)
    {
        var batch=EnsureRollHistoryBatch();
        if(!string.IsNullOrWhiteSpace(ActiveRollCardName) && !batch.CardNames.Contains(ActiveRollCardName,StringComparer.Ordinal))batch.CardNames.Add(ActiveRollCardName);
        var term=die.Key=="d10-inverse"?$"({Math.Abs(value)} × 10)":value.ToString(System.Globalization.CultureInfo.InvariantCulture);
        batch.Terms.Add(term);
        batch.Total=Total;
    }

    public async Task RollWithHistoryAsync(string key,int? selectedMagnitude=null)
    {
        var before=Rolls.Count;
        await RollAsync(key,selectedMagnitude);
        if(Rolls.Count<=before)return;
        foreach(var roll in Rolls.Skip(before))
        {
            var die=Dice(roll.Key);
            if(die is not null)RecordRollHistory(die,roll.Value);
        }
        Notify();
    }

    public async Task RollHandCardWithHistoryAsync(HandCard card)
    {
        var before=Rolls.Count;
        ActiveRollCardName=card.Name;
        try
        {
            await RollHandCardAsync(card);
            if(Rolls.Count>before)
            {
                foreach(var roll in Rolls.Skip(before))
                {
                    var die=Dice(roll.Key);
                    if(die is not null)RecordRollHistory(die,roll.Value);
                }
            }
        }
        finally
        {
            ActiveRollCardName="";
            Notify();
        }
    }

    public void ClearRollsWithHistory()
    {
        if(_activeRollBatch is not null)
        {
            _activeRollBatch.Total=Total;
            _activeRollBatch.Complete=true;
            _activeRollBatch=null;
        }
        ActiveRollCardName="";
        ClearRolls();
    }
}

public sealed class RollHistoryBatch
{
    public string CharacterName { get; set; } = "Character";
    public List<string> CardNames { get; } = [];
    public List<string> Terms { get; } = [];
    public int Total { get; set; }
    public bool Complete { get; set; }
    public string Equation => Terms.Count==0?$"= {Total}":$"{string.Join(" + ",Terms).Replace("+ -","- ")} = {Total}";
}
