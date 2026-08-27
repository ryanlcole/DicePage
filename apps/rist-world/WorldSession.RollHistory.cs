namespace RistWorld;

public sealed partial class WorldSession
{
    public List<RollHistoryBatch> RollHistoryBatches { get; } = [];
    public string ActiveRollCardName { get; private set; } = "";
    private RollHistoryBatch? _activeRollBatch;

    public void BeginCardRoll(string cardName)
    {
        ActiveRollCardName = cardName ?? "";
    }

    public void EndCardRoll()
    {
        ActiveRollCardName = "";
    }

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

    private void RecordGemHistory(int value)
    {
        var batch=EnsureRollHistoryBatch();
        batch.Terms.Add(value>=0?$"+{value}":value.ToString(System.Globalization.CultureInfo.InvariantCulture));
        batch.Total=Total;
    }

    private void FinishRollHistoryBatch()
    {
        if(_activeRollBatch is null)return;
        _activeRollBatch.Total=Total;
        _activeRollBatch.Complete=true;
        _activeRollBatch=null;
        ActiveRollCardName="";
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
