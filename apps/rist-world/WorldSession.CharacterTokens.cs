namespace RistWorld;

public sealed partial class WorldSession
{
    // Character token selection is intentionally separate from map-piece type.
    // Until the dedicated token selector is built, option 1 is the active
    // character portrait so switching characters also switches this source.
    public IReadOnlyList<string> CharacterFrontTokenOptions
        => string.IsNullOrWhiteSpace(CharacterPortraitDataUrl)
            ? Array.Empty<string>()
            : new[] { CharacterPortraitDataUrl };

    public int SelectedCharacterFrontTokenIndex { get; private set; }

    public string CharacterFrontTokenDataUrl
    {
        get
        {
            var options = CharacterFrontTokenOptions;
            if (options.Count == 0) return string.Empty;
            var index = Math.Clamp(SelectedCharacterFrontTokenIndex, 0, options.Count - 1);
            return options[index];
        }
    }

    public void SelectCharacterFrontToken(int index)
    {
        var options = CharacterFrontTokenOptions;
        SelectedCharacterFrontTokenIndex = options.Count == 0 ? 0 : Math.Clamp(index, 0, options.Count - 1);
        Notify();
    }
}
