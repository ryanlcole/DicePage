namespace RistWorld;

public sealed partial class WorldSession
{
    public List<RollHistoryBatch> RollHistoryBatches { get; } = [];
    public string ActiveRollCardName { get; private set; } = "";
    public string RollVisibilityMode { get; private set; } = "public";
    public bool DiceSumEnabled { get; private set; } = true;
    public bool DiceValuesVisibleToUser => RollVisibilityMode != "gm-discrete" || Role == "GM";
    public bool DiceSumVisibleToUser => (RollVisibilityMode == "gm-discrete" && Role == "GM") || (DiceSumEnabled && DiceValuesVisibleToUser);
    public string RollVisibilityLabel => RollVisibilityMode switch
    {
        "test" => "Test Roll",
        "group" => "Group Roll",
        "gm" => "GM Roll",
        "gm-discrete" => "GM Discrete",
        _ => "Public Roll"
    };
    public string RollVisibilityCssClass => $"roll-mode-{RollVisibilityMode}";
    private RollHistoryBatch? _activeRollBatch;

    public void CycleRollVisibility()
    {
        SetRollVisibilityMode(RollVisibilityMode switch
        {
            "test" => "public",
            "public" => "group",
            "group" => "gm",
            "gm" => "gm-discrete",
            _ => "test"
        });
    }

    public void SetRollVisibilityMode(string mode)
    {
        mode = mode switch
        {
            "test" or "public" or "group" or "gm" or "gm-discrete" => mode,
            _ => "public"
        };
        if(mode == RollVisibilityMode)return;
        CompleteActiveRollBatch();
        RollVisibilityMode = mode;
        Notify();
    }

    public void ToggleDiceSum()
    {
        if(Role != "GM")return;
        CompleteActiveRollBatch();
        DiceSumEnabled = !DiceSumEnabled;
        Notify();
    }

    private void CompleteActiveRollBatch()
    {
        if(_activeRollBatch is null)return;
        _activeRollBatch.Total = Total;
        _activeRollBatch.Complete = true;
        _activeRollBatch = null;
    }

    private RollHistoryBatch EnsureRollHistoryBatch()
    {
        if(_activeRollBatch is not null)return _activeRollBatch;
        _activeRollBatch = new RollHistoryBatch
        {
            CharacterName = string.IsNullOrWhiteSpace(CharacterName) ? "Character" : CharacterName.Trim(),
            VisibilityMode = RollVisibilityMode,
            SumWasEnabled = DiceSumEnabled
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
        CompleteActiveRollBatch();
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
    public string VisibilityMode { get; set; } = "public";
    public bool SumWasEnabled { get; set; } = true;
    public string VisibilityLabel => VisibilityMode switch
    {
        "test" => "Test Roll",
        "group" => "Group Roll",
        "gm" => "GM Roll",
        "gm-discrete" => "GM Discrete",
        _ => "Public Roll"
    };
    public string Equation => Terms.Count==0?$"= {Total}":$"{string.Join(" + ",Terms).Replace("+ -","- ")} = {Total}";
    public string PlayerEquation => VisibilityMode=="gm-discrete" ? "Hidden result" : SumWasEnabled ? Equation : string.Join(" + ",Terms).Replace("+ -","- ");
}
