namespace RistWorld;

public sealed partial class WorldSession
{
    private sealed class CharacterSlot
    {
        public string Name { get; set; } = "";
        public string Species { get; set; } = "";
        public string Age { get; set; } = "";
        public string Alignment { get; set; } = "";
        public string Description { get; set; } = "";
        public string Background { get; set; } = "";
        public string Portrait { get; set; } = "";
        public List<CharacterField> Fields { get; set; } = [];
        public List<(string FieldId,List<DiceBagEntry> Dice)> Hand { get; set; } = [];
    }

    private readonly List<CharacterSlot> _characterSlots = [new()];
    private int _activeCharacterIndex;
    private string _characterPortraitDataUrl = "";

    public string CharacterPortraitDataUrl => _characterPortraitDataUrl;
    public int CharacterCount => _characterSlots.Count;
    public int ActiveCharacterNumber => _activeCharacterIndex + 1;

    public void SetCharacterPortrait(string dataUrl)
    {
        _characterPortraitDataUrl = dataUrl ?? "";
        Notify();
    }

    public void NewCharacter()
    {
        SaveCurrentCharacterSlot();
        _characterSlots.Add(new());
        _activeCharacterIndex = _characterSlots.Count - 1;
        LoadCharacterSlot(_characterSlots[_activeCharacterIndex]);
        CharacterEditMode = true;
        Notify();
    }

    public void SwitchCharacter(int delta)
    {
        if (_characterSlots.Count <= 1) return;
        SaveCurrentCharacterSlot();
        _activeCharacterIndex = (_activeCharacterIndex + delta) % _characterSlots.Count;
        if (_activeCharacterIndex < 0) _activeCharacterIndex += _characterSlots.Count;
        LoadCharacterSlot(_characterSlots[_activeCharacterIndex]);
        EditingHandCard = null;
        DraggedDieKey = null;
        Notify();
    }

    private void SaveCurrentCharacterSlot()
    {
        var slot = _characterSlots[_activeCharacterIndex];
        slot.Name = CharacterName;
        slot.Species = CharacterSpecies;
        slot.Age = CharacterAge;
        slot.Alignment = CharacterAlignment;
        slot.Description = CharacterDescription;
        slot.Background = CharacterBackground;
        slot.Portrait = _characterPortraitDataUrl;
        slot.Fields = CharacterFields.Select(CloneField).ToList();
        slot.Hand = HandCards.Select(card =>
        {
            var fieldId = card.Field.Id;
            var dice = card.DiceBag.Select(x => new DiceBagEntry(x.DieKey,x.Count,x.SelectedMagnitude)).ToList();
            return (fieldId,dice);
        }).ToList();
    }

    private void LoadCharacterSlot(CharacterSlot slot)
    {
        CharacterName = slot.Name;
        CharacterSpecies = slot.Species;
        CharacterAge = slot.Age;
        CharacterAlignment = slot.Alignment;
        CharacterDescription = slot.Description;
        CharacterBackground = slot.Background;
        _characterPortraitDataUrl = slot.Portrait;
        CharacterFields.Clear();
        CharacterFields.AddRange(slot.Fields.Select(CloneField));
        HandCards.Clear();
        foreach (var saved in slot.Hand)
        {
            var field = CharacterFields.FirstOrDefault(x => x.Id == saved.FieldId) ?? CharacterFields.FirstOrDefault();
            if (field is null) continue;
            var card = new HandCard(field);
            foreach (var die in saved.Dice) card.DiceBag.Add(new(die.DieKey,die.Count,die.SelectedMagnitude));
            HandCards.Add(card);
        }
    }

    private static CharacterField CloneField(CharacterField source)
    {
        var clone = new CharacterField(source.Name,source.Kind,source.Group)
        {
            Current = source.Current,
            Max = source.Max,
            Color = source.Color
        };
        clone.Id = source.Id;
        return clone;
    }
}
