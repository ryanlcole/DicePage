namespace RistWorld;

public sealed partial class WorldSession
{
    public List<CharacterLanguage> CharacterLanguages { get; } = [new("Common", 100)];
    public string ActiveRoleplayLanguage { get; private set; } = "Common";
    public string DialogueLanguage { get; set; } = "Common";
    public string DialogueHumanLanguage { get; set; } = "English";
    public string PrimaryHumanLanguage { get; private set; } = "English";
    public string GmLanguageResolutionMode { get; private set; } = "system";
    public int GmLanguageLegibilityPercent { get; private set; } = 100;
    public string GmManualLanguageResponse { get; private set; } = "";
    public string ActiveRoleplayDialectLabel => ActiveRoleplayLanguage.Equals("Common", StringComparison.OrdinalIgnoreCase) ? "Universal" : ActiveRoleplayLanguage;

    public int LinguisticsValue => CharacterFields
        .Where(characterField => characterField.Name.Contains("lingu", StringComparison.OrdinalIgnoreCase)
                              || characterField.Name.Contains("language", StringComparison.OrdinalIgnoreCase)
                              || characterField.Name.Contains("comprehension", StringComparison.OrdinalIgnoreCase))
        .Select(characterField => Math.Max(characterField.Current, characterField.BaseValue))
        .DefaultIfEmpty(0)
        .Max();

    public void EnsureCharacterLanguages()
    {
        if (CharacterLanguages.Count == 0) CharacterLanguages.Add(new("Common", 100));
        if (!CharacterLanguages.Any(x => x.Name.Equals("Common", StringComparison.OrdinalIgnoreCase))) CharacterLanguages.Insert(0, new("Common", 100));
        var common = CharacterLanguages.First(x => x.Name.Equals("Common", StringComparison.OrdinalIgnoreCase));
        common.Proficiency = 100;
        if (!CharacterLanguages.Any(x => x.Name.Equals(ActiveRoleplayLanguage, StringComparison.OrdinalIgnoreCase))) ActiveRoleplayLanguage = "Common";
    }

    public void AddCharacterLanguage(string name = "Language")
    {
        if (!CharacterEditMode) return;
        name = string.IsNullOrWhiteSpace(name) ? "Language" : name.Trim();
        var root = name;
        var n = 2;
        while (CharacterLanguages.Any(x => x.Name.Equals(name, StringComparison.OrdinalIgnoreCase))) name = $"{root} {n++}";
        CharacterLanguages.Add(new(name, 0));
        Notify();
    }

    public void RenameCharacterLanguage(CharacterLanguage language, string name)
    {
        if (!CharacterEditMode || language.Name.Equals("Common", StringComparison.OrdinalIgnoreCase)) return;
        name = name.Trim();
        if (name.Length == 0 || CharacterLanguages.Any(x => !ReferenceEquals(x, language) && x.Name.Equals(name, StringComparison.OrdinalIgnoreCase))) return;
        var wasActive = ActiveRoleplayLanguage.Equals(language.Name, StringComparison.OrdinalIgnoreCase);
        language.Name = name;
        if (wasActive) ActiveRoleplayLanguage = name;
        Notify();
    }

    public void SetCharacterLanguageProficiency(CharacterLanguage language, int percent)
    {
        if (!CharacterEditMode) return;
        language.Proficiency = language.Name.Equals("Common", StringComparison.OrdinalIgnoreCase) ? 100 : Math.Clamp(percent, 0, 100);
        Notify();
    }

    public void RemoveCharacterLanguage(CharacterLanguage language)
    {
        if (!CharacterEditMode || language.Name.Equals("Common", StringComparison.OrdinalIgnoreCase)) return;
        CharacterLanguages.Remove(language);
        if (ActiveRoleplayLanguage.Equals(language.Name, StringComparison.OrdinalIgnoreCase)) ActiveRoleplayLanguage = "Common";
        Notify();
    }

    public void CycleRoleplayLanguage()
    {
        EnsureCharacterLanguages();
        var i = CharacterLanguages.FindIndex(x => x.Name.Equals(ActiveRoleplayLanguage, StringComparison.OrdinalIgnoreCase));
        ActiveRoleplayLanguage = CharacterLanguages[(i + 1 + CharacterLanguages.Count) % CharacterLanguages.Count].Name;
        Notify();
    }

    public void SetPrimaryHumanLanguage(string language)
    {
        PrimaryHumanLanguage = string.IsNullOrWhiteSpace(language) ? "English" : language.Trim();
        Notify();
    }

    public void SetGmLanguageResolution(string mode, int percent = 100, string manualResponse = "")
    {
        if (Role != "GM") return;
        GmLanguageResolutionMode = mode switch { "manual" => "manual", "percent" => "percent", _ => "system" };
        GmLanguageLegibilityPercent = Math.Clamp(percent, 0, 100);
        GmManualLanguageResponse = manualResponse ?? "";
        Notify();
    }

    public int RoleplayLegibilityPercent(string language, string text)
    {
        if (language.Equals("Common", StringComparison.OrdinalIgnoreCase)) return 100;
        if (GmLanguageResolutionMode == "percent") return GmLanguageLegibilityPercent;
        if (GmLanguageResolutionMode == "manual") return 100;

        var proficiency = CharacterLanguages.FirstOrDefault(x => x.Name.Equals(language, StringComparison.OrdinalIgnoreCase))?.Proficiency ?? 0;
        var roll = StableLinguisticsRoll(text, language);
        var skill = Math.Clamp(LinguisticsValue, 0, 100);
        return Math.Clamp(proficiency + skill / 2 + roll - 50, 0, 100);
    }

    public string ResolveRoleplayForViewer(string text, string language)
    {
        if (string.IsNullOrEmpty(text)) return text;
        language = string.IsNullOrWhiteSpace(language) ? "Common" : language;
        if (language.Equals("Common", StringComparison.OrdinalIgnoreCase)) return text;
        if (GmLanguageResolutionMode == "manual" && !string.IsNullOrWhiteSpace(GmManualLanguageResponse)) return GmManualLanguageResponse;
        return ScrambleByLegibility(text, language, RoleplayLegibilityPercent(language, text));
    }

    private int StableLinguisticsRoll(string text, string language)
        => (int)(StableHash($"roll|{CharacterName}|{language}|{text}") % 101u);

    /* The canonical/original message is never mutated. This method creates only the viewer's
       representation. Unrevealed words become stable five-letter dialect tokens, while the
       language roll determines exactly how many word positions are restored to the original. */
    private static string ScrambleByLegibility(string text, string language, int percent)
    {
        percent = Math.Clamp(percent, 0, 100);
        if (percent >= 100) return text;

        var parts = SplitPreservingWhitespace(text);
        var wordPositions = Enumerable.Range(0, parts.Count)
            .Where(i => ContainsWordCharacter(parts[i]))
            .ToArray();
        if (wordPositions.Length == 0) return text;

        var revealCount = (int)Math.Round(wordPositions.Length * percent / 100.0, MidpointRounding.AwayFromZero);
        revealCount = Math.Clamp(revealCount, 0, wordPositions.Length);
        var revealed = wordPositions
            .OrderBy(i => StableHash($"reveal|{language}|{text}|{i}"))
            .Take(revealCount)
            .ToHashSet();

        foreach (var i in wordPositions)
        {
            if (revealed.Contains(i)) continue;
            parts[i] = ScrambleWord(parts[i], language, text, i);
        }
        return string.Concat(parts);
    }

    private static List<string> SplitPreservingWhitespace(string text)
    {
        var result = new List<string>();
        if (text.Length == 0) return result;
        var start = 0;
        var whitespace = char.IsWhiteSpace(text[0]);
        for (var i = 1; i < text.Length; i++)
        {
            var nextWhitespace = char.IsWhiteSpace(text[i]);
            if (nextWhitespace == whitespace) continue;
            result.Add(text[start..i]);
            start = i;
            whitespace = nextWhitespace;
        }
        result.Add(text[start..]);
        return result;
    }

    private static bool ContainsWordCharacter(string value)
        => value.Any(char.IsLetterOrDigit);

    private static string ScrambleWord(string token, string language, string text, int position)
    {
        var first = 0;
        while (first < token.Length && !char.IsLetterOrDigit(token[first])) first++;
        var last = token.Length - 1;
        while (last >= first && !char.IsLetterOrDigit(token[last])) last--;
        if (first > last) return token;

        // Five-letter dialect words stay speech-friendly for future TTS: consonant-vowel-consonant-vowel-consonant.
        const string consonants = "bcdfghjklmnprstvwxyz";
        const string vowels = "aeiou";
        var seed = StableHash($"mask|{language}|{text}|{position}|{token}");
        Span<char> code = stackalloc char[5];
        for (var i = 0; i < code.Length; i++)
        {
            seed = unchecked(seed * 1664525u + 1013904223u);
            var alphabet = i % 2 == 0 ? consonants : vowels;
            code[i] = alphabet[(int)(seed % (uint)alphabet.Length)];
        }
        return string.Concat(token[..first], new string(code), token[(last + 1)..]);
    }

    private static uint StableHash(string value)
    {
        unchecked
        {
            var hash = 2166136261u;
            foreach (var c in value)
            {
                hash ^= c;
                hash *= 16777619u;
            }
            return hash;
        }
    }
}

public sealed class CharacterLanguage(string name, int proficiency)
{
    public string Name { get; set; } = name;
    public int Proficiency { get; set; } = proficiency;
}
