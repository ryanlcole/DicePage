namespace RistWorld;

public sealed partial class WorldSession
{
    public CharacterField? EditingDiceField { get; private set; }
    public int? DiceBagExampleTotal { get; private set; }
    public bool ShowSkillDescriptions { get; private set; } = true;
    public bool ShowFeatDescriptions { get; private set; } = true;

    public static bool IsAttributeField(CharacterField field)
        => field.Kind == "ATTRIBUTE" || field.Group == "Attributes";

    public static bool IsTrackerField(CharacterField field)
        => field.Kind is "TRACKER" or "TRACK" or "POOL" || field.Group is "Trackers" or "Tracks" or "Vitals" or "Accent" or "Pools";

    public static bool IsLimitField(CharacterField field)
        => field.Kind == "LIMIT" || field.Group == "Limits";

    public static bool IsFlareField(CharacterField field)
        => field.Kind is "FLARE" or "ABILITY" || field.Group is "Flare" or "Feats";

    public static bool IsTrackField(CharacterField field) => IsTrackerField(field);

    public bool IsFieldInHand(CharacterField field)
        => HandCards.Any(x => x.Field.Id == field.Id);

    public void AddCharacterControl(string group)
    {
        if (!CharacterEditMode) return;
        var (kind,prefix) = group switch
        {
            "Attributes" => ("ATTRIBUTE","Attribute"),
            "Trackers" => ("TRACKER","Tracker"),
            "Limits" => ("LIMIT","Limit"),
            "Skills" => ("VALUE","Skill"),
            "Flare" => ("FLARE","Flare"),
            _ => ("FLARE","Flare")
        };
        var n=1; var name=$"{prefix} {n}";
        while(CharacterFields.Any(x=>x.Name.Equals(name,StringComparison.OrdinalIgnoreCase))) name=$"{prefix} {++n}";
        var field=new CharacterField(name,kind,group);
        if(kind=="ATTRIBUTE"){field.BaseValue=10;field.Current=0;field.Max=10;}
        else if(kind=="TRACKER"){field.Current=0;field.Max=100;}
        else if(kind=="LIMIT"){field.Current=0;field.Max=10;}
        else if(kind=="FLARE"){field.Current=0;field.Max=0;}
        CharacterFields.Add(field);
        Notify();
    }

    public void SetAttribute(CharacterField field,int modifier)
    {
        if(!CharacterEditMode || !IsAttributeField(field)) return;
        field.Kind="ATTRIBUTE"; field.Group="Attributes"; field.Max=10;
        field.Current=Math.Clamp(modifier,-10,10); Notify();
    }

    public void SetAttributeBase(CharacterField field,int value)
    {
        if(!CharacterEditMode || !IsAttributeField(field)) return;
        field.BaseValue=Math.Clamp(value,-999999,999999); Notify();
    }

    public void SetTrackerMaximum(CharacterField field,int max)
    {
        if(!CharacterEditMode || !IsTrackerField(field)) return;
        field.Kind="TRACKER"; field.Group="Trackers";
        field.Max=Math.Clamp(max,1,999999);
        field.Current=Math.Clamp(field.Current,0,field.Max); Notify();
    }

    public void SetTrackerCurrent(CharacterField field,int current)
    {
        if(!IsTrackerField(field)) return;
        field.Kind="TRACKER"; field.Group="Trackers";
        field.Current=Math.Clamp(current,0,Math.Max(field.Max,1)); Notify();
    }

    public void SetLimitMaximum(CharacterField field,int max)
    {
        if(!CharacterEditMode || !IsLimitField(field)) return;
        field.Kind="LIMIT"; field.Group="Limits";
        field.Max=Math.Clamp(max,0,999999);
        field.Current=Math.Clamp(field.Current,0,field.Max); Notify();
    }

    public void SetLimitValue(CharacterField field,int value)
    {
        if(!CharacterEditMode || !IsLimitField(field)) return;
        field.Kind="LIMIT"; field.Group="Limits";
        field.Current=Math.Clamp(value,0,Math.Max(field.Max,0)); Notify();
    }

    public void ShowFieldHand(CharacterField field)
    {
        if(IsFieldInHand(field)) return;
        if(IsTrackerField(field)){field.Kind="TRACKER";field.Group="Trackers";}
        else if(IsAttributeField(field)){field.Kind="ATTRIBUTE";field.Group="Attributes";}
        else if(IsLimitField(field)){field.Kind="LIMIT";field.Group="Limits";}
        else if(IsFlareField(field)){field.Kind="FLARE";field.Group="Flare";}
        HandCards.Add(new(field));
        Notify();
    }

    public void ShowTrackHand(CharacterField field)=>ShowFieldHand(field);
    public void SetTrackMaximum(CharacterField field,int max)=>SetTrackerMaximum(field,max);
    public void SetTrackCurrent(CharacterField field,int current)=>SetTrackerCurrent(field,current);

    public void SetFieldDescription(CharacterField field,string value){if(!CharacterEditMode)return;field.Description=value??"";Notify();}
    public void SetFieldNameplateDescription(CharacterField field,string value){if(!CharacterEditMode)return;field.NameplateDescription=value??"";Notify();}
    public void SetFieldSubtitle(CharacterField field,string value){if(!CharacterEditMode)return;field.Subtitle=value??"";Notify();}
    public void SetFieldShortName(CharacterField field,string value){if(!CharacterEditMode)return;field.SetShortName(value);Notify();}
    public void ResetFieldShortName(CharacterField field){if(!CharacterEditMode)return;field.ResetShortName();Notify();}
    public void SetFieldDescriptionEnabled(CharacterField field,bool enabled){if(!CharacterEditMode)return;field.DescriptionEnabled=enabled;Notify();}
    public void ToggleSectionDescriptions(string group){if(group=="Skills")ShowSkillDescriptions=!ShowSkillDescriptions;else if(group is "Flare" or "Feats")ShowFeatDescriptions=!ShowFeatDescriptions;Notify();}
    public void SetCharacterFieldImage(CharacterField field,string dataUrl){if(!CharacterEditMode)return;field.ImageDataUrl=dataUrl??"";Notify();}

    public void EditFieldDiceBag(CharacterField field){EditingDiceField=field;DiceBagExampleTotal=null;Notify();}
    public void CloseFieldDiceBag(){EditingDiceField=null;DiceBagExampleTotal=null;Notify();}
    public int DiceBagCount(CharacterField field,string dieKey)=>field.DiceBag.FirstOrDefault(x=>x.DieKey==dieKey)?.Count??0;
    public int DiceBagMagnitude(CharacterField field,string dieKey)=>field.DiceBag.FirstOrDefault(x=>x.DieKey==dieKey)?.SelectedMagnitude??1;

    public void SetDiceBagCount(CharacterField field,string dieKey,int count)
    {
        if(!MixerOpen || Dice(dieKey) is null) return;
        count=Math.Clamp(count,0,20);
        var entry=field.DiceBag.FirstOrDefault(x=>x.DieKey==dieKey);
        if(count==0){if(entry is not null)field.DiceBag.Remove(entry);}
        else if(entry is null)field.DiceBag.Add(new(dieKey,count));
        else entry.Count=count;
        DiceBagExampleTotal=null; Notify();
    }

    public void AdjustDiceBag(CharacterField field,string dieKey,int delta)
        => SetDiceBagCount(field,dieKey,DiceBagCount(field,dieKey)+delta);

    public void SetFieldDiceMagnitude(CharacterField field,string dieKey,int magnitude)
    {
        if(!MixerOpen || Dice(dieKey) is null) return;
        var entry=field.DiceBag.FirstOrDefault(x=>x.DieKey==dieKey);
        if(entry is null){entry=new(dieKey,1,magnitude);field.DiceBag.Add(entry);}else entry.SelectedMagnitude=Math.Clamp(magnitude,1,5);
        DiceBagExampleTotal=null;Notify();
    }

    public void ExampleDiceBagRoll(CharacterField field)
    {
        var total=0;
        foreach(var entry in field.DiceBag)
        {
            var die=Dice(entry.DieKey); if(die is null)continue;
            for(var i=0;i<entry.Count;i++)
                total+=entry.DieKey is "d5-bonus" or "d5-penalty"?entry.SelectedMagnitude*die.Sign:(Random.Shared.Next(die.Sides)+die.ValueOffset)*die.Sign;
        }
        DiceBagExampleTotal=total;Notify();
    }
}
