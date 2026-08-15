namespace RistWorld;

public sealed partial class WorldSession
{
    public CharacterField? EditingDiceField { get; private set; }
    public int? DiceBagExampleTotal { get; private set; }
    public bool ShowSkillDescriptions { get; private set; } = true;
    public bool ShowFeatDescriptions { get; private set; } = true;

    public void AddCharacterControl(string group)
    {
        if (!CharacterEditMode) return;
        var equalizer = group is "Vitals" or "Attributes" or "Accent" or "Pools";
        var kind = equalizer ? "POOL" : group == "Skills" ? "VALUE" : "ABILITY";
        var prefix = group switch
        {
            "Vitals" => "Vital",
            "Attributes" => "Attribute",
            "Accent" => "Accent",
            "Pools" => "Pool",
            "Skills" => "Skill",
            _ => "Feat"
        };
        var n = 1;
        var name = $"{prefix} {n}";
        while (CharacterFields.Any(x => x.Name.Equals(name,StringComparison.OrdinalIgnoreCase)))
            name = $"{prefix} {++n}";
        CharacterFields.Add(new(name,kind,group));
        Notify();
    }

    public void SetFieldDescription(CharacterField field,string value)
    {
        if (!CharacterEditMode) return;
        field.Description = value ?? "";
        Notify();
    }

    public void SetFieldDescriptionEnabled(CharacterField field,bool enabled)
    {
        if (!CharacterEditMode) return;
        field.DescriptionEnabled = enabled;
        Notify();
    }

    public void ToggleSectionDescriptions(string group)
    {
        if (group == "Skills") ShowSkillDescriptions = !ShowSkillDescriptions;
        else if (group == "Feats") ShowFeatDescriptions = !ShowFeatDescriptions;
        Notify();
    }

    public void SetCharacterFieldImage(CharacterField field,string dataUrl)
    {
        if (!CharacterEditMode) return;
        field.ImageDataUrl = dataUrl ?? "";
        Notify();
    }

    public void EditFieldDiceBag(CharacterField field)
    {
        EditingDiceField = field;
        DiceBagExampleTotal = null;
        Notify();
    }

    public void CloseFieldDiceBag()
    {
        EditingDiceField = null;
        DiceBagExampleTotal = null;
        Notify();
    }

    public int DiceBagCount(CharacterField field,string dieKey)
        => field.DiceBag.FirstOrDefault(x => x.DieKey == dieKey)?.Count ?? 0;

    public int DiceBagMagnitude(CharacterField field,string dieKey)
        => field.DiceBag.FirstOrDefault(x => x.DieKey == dieKey)?.SelectedMagnitude ?? 1;

    public void AdjustDiceBag(CharacterField field,string dieKey,int delta)
    {
        if (!CharacterEditMode || Dice(dieKey) is null) return;
        var entry = field.DiceBag.FirstOrDefault(x => x.DieKey == dieKey);
        if (entry is null)
        {
            if (delta <= 0) return;
            field.DiceBag.Add(new(dieKey,Math.Clamp(delta,1,20)));
        }
        else
        {
            var next = entry.Count + delta;
            if (next <= 0) field.DiceBag.Remove(entry);
            else entry.Count = Math.Clamp(next,1,20);
        }
        DiceBagExampleTotal = null;
        Notify();
    }

    public void SetFieldDiceMagnitude(CharacterField field,string dieKey,int magnitude)
    {
        if (!CharacterEditMode) return;
        var entry = field.DiceBag.FirstOrDefault(x => x.DieKey == dieKey);
        if (entry is null)
        {
            entry = new(dieKey,1,magnitude);
            field.DiceBag.Add(entry);
        }
        else entry.SelectedMagnitude = Math.Clamp(magnitude,1,5);
        DiceBagExampleTotal = null;
        Notify();
    }

    public void ExampleDiceBagRoll(CharacterField field)
    {
        var total = 0;
        foreach (var entry in field.DiceBag)
        {
            var die = Dice(entry.DieKey);
            if (die is null) continue;
            for (var i=0;i<entry.Count;i++)
            {
                if (entry.DieKey is "d5-bonus" or "d5-penalty")
                    total += entry.SelectedMagnitude * die.Sign;
                else
                    total += (Random.Shared.Next(die.Sides) + die.ValueOffset) * die.Sign;
            }
        }
        DiceBagExampleTotal = total;
        Notify();
    }
}
