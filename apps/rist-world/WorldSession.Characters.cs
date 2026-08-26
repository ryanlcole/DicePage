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
        public string Notes { get; set; } = "";
        public string Equipment { get; set; } = "";
        public string Anatomy { get; set; } = "";
        public string Conditions { get; set; } = "";
        public string LinkedNotes { get; set; } = "";
        public string Portrait { get; set; } = "";
        public List<CharacterField> Fields { get; set; } = [];
        public List<string> HandFieldIds { get; set; } = [];
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
        EnsureCharacterSheetFields();
        CharacterEditMode = true;
        Notify();
    }

    public void DeleteCharacter()
    {
        if (_characterSlots.Count == 1) return;
        _characterSlots.RemoveAt(_activeCharacterIndex);
        _activeCharacterIndex = Math.Min(_activeCharacterIndex, _characterSlots.Count - 1);
        LoadCharacterSlot(_characterSlots[_activeCharacterIndex]);
        EnsureCharacterSheetFields();
        CharacterEditMode = false;
        EditingHandCard = null;
        EditingDiceField = null;
        Notify();
    }

    public void SwitchCharacter(int delta)
    {
        if (_characterSlots.Count <= 1) return;
        SaveCurrentCharacterSlot();
        _activeCharacterIndex = (_activeCharacterIndex + delta) % _characterSlots.Count;
        if (_activeCharacterIndex < 0) _activeCharacterIndex += _characterSlots.Count;
        LoadCharacterSlot(_characterSlots[_activeCharacterIndex]);
        EnsureCharacterSheetFields();
        EditingHandCard = null;
        EditingDiceField = null;
        DraggedDieKey = null;
        DraggedHandCardId = null;
        PublicCards.Clear();
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
        slot.Notes = CharacterNotes;
        slot.Equipment = CharacterEquipment;
        slot.Anatomy = CharacterAnatomy;
        slot.Conditions = CharacterConditions;
        slot.LinkedNotes = CharacterLinkedNotes;
        slot.Portrait = _characterPortraitDataUrl;
        slot.Fields = CharacterFields.Select(CloneField).ToList();
        slot.HandFieldIds = HandCards.Select(card => card.Field.Id).Distinct().ToList();
    }

    private void LoadCharacterSlot(CharacterSlot slot)
    {
        CharacterName = slot.Name;
        CharacterSpecies = slot.Species;
        CharacterAge = slot.Age;
        CharacterAlignment = slot.Alignment;
        CharacterDescription = slot.Description;
        CharacterBackground = slot.Background;
        CharacterNotes = slot.Notes;
        CharacterEquipment = slot.Equipment;
        CharacterAnatomy = slot.Anatomy;
        CharacterConditions = slot.Conditions;
        CharacterLinkedNotes = slot.LinkedNotes;
        _characterPortraitDataUrl = slot.Portrait;
        CharacterFields.Clear();
        CharacterFields.AddRange(slot.Fields.Select(CloneField));
        HandCards.Clear();
        foreach (var fieldId in slot.HandFieldIds)
        {
            var field = CharacterFields.FirstOrDefault(x => x.Id == fieldId);
            if (field is not null) HandCards.Add(new(field));
        }
    }

    private static CharacterField CloneField(CharacterField source)
    {
        var clone = new CharacterField(source.Name,source.Kind,source.Group)
        {
            Id = source.Id,
            BaseValue = source.BaseValue,
            Current = source.Current,
            Max = source.Max,
            Color = source.Color,
            Description = source.Description,
            NameplateDescription = source.NameplateDescription,
            Subtitle = source.Subtitle,
            DescriptionEnabled = source.DescriptionEnabled,
            ImageDataUrl = source.ImageDataUrl,
            ShortName = source.ShortName,
            ShortNameOverridden = source.ShortNameOverridden
        };
        foreach (var die in source.DiceBag)
            clone.DiceBag.Add(new(die.DieKey,die.Count,die.SelectedMagnitude));
        return clone;
    }
}
