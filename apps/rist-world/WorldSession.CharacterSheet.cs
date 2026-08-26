namespace RistWorld;

public sealed partial class WorldSession
{
    public string CharacterEquipment { get; set; } = "";
    public string CharacterAnatomy { get; set; } = "";
    public string CharacterConditions { get; set; } = "";
    public string CharacterLinkedNotes { get; set; } = "";

    public void EnsureCharacterSheetFields()
    {
        var attributes = CharacterFields.Count(IsAttributeField);
        for (var i = attributes + 1; i <= 6; i++)
        {
            var field = new CharacterField($"Value {i}", "ATTRIBUTE", "Attributes")
            {
                BaseValue = 0,
                Current = 0,
                Max = 10
            };
            CharacterFields.Add(field);
        }

        var trackers = CharacterFields.Count(IsTrackerField);
        for (var i = trackers + 1; i <= 2; i++)
        {
            var field = new CharacterField($"Tracker {i}", "TRACKER", "Trackers")
            {
                Current = 0,
                Max = 100
            };
            CharacterFields.Add(field);
        }
    }
}
