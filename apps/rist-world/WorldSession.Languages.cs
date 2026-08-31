namespace RistWorld;

public sealed partial class WorldSession
{
    public List<CharacterLanguage> CharacterLanguages { get; } = [new("Common", 100)];
    public List<LanguageLexiconEntry> LanguageLexicon { get; } = [];
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
        var oldName = language.Name;
        var wasActive = ActiveRoleplayLanguage.Equals(oldName, StringComparison.OrdinalIgnoreCase);
        language.Name = name;
        foreach (var entry in LanguageLexicon.Where(x => x.Language.Equals(oldName, StringComparison.OrdinalIgnoreCase))) entry.Language = name;
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
        LanguageLexicon.RemoveAll(x => x.Language.Equals(language.Name, StringComparison.OrdinalIgnoreCase));
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

    public void SetLanguageTranslation(string language, string source, string translation, string pronunciation = "")
    {
        if (Role != "GM") return;
        language = language.Trim(); source = NormalizeLexiconText(source); translation = translation.Trim(); pronunciation = pronunciation.Trim();
        if (language.Length == 0 || source.Length == 0 || translation.Length == 0 || language.Equals("Common", StringComparison.OrdinalIgnoreCase)) return;
        var existing = LanguageLexicon.FirstOrDefault(x => x.Language.Equals(language, StringComparison.OrdinalIgnoreCase) && x.Source.Equals(source, StringComparison.OrdinalIgnoreCase));
        if (existing is null) LanguageLexicon.Add(new(language, source, translation, pronunciation));
        else { existing.Translation = translation; existing.Pronunciation = pronunciation; }
        Notify();
    }

    public void RemoveLanguageTranslation(string language, string source)
    {
        if (Role != "GM") return;
        source = NormalizeLexiconText(source);
        LanguageLexicon.RemoveAll(x => x.Language.Equals(language, StringComparison.OrdinalIgnoreCase) && x.Source.Equals(source, StringComparison.OrdinalIgnoreCase));
        Notify();
    }

    public IReadOnlyList<string> UnresolvedLanguageTerms(string language, IEnumerable<string> messages)
    {
        var mapped = LanguageLexicon.Where(x => x.Language.Equals(language, StringComparison.OrdinalIgnoreCase)).Select(x => x.Source).ToHashSet(StringComparer.OrdinalIgnoreCase);
        return messages.SelectMany(TokenizeWords).Select(NormalizeLexiconText).Where(x => x.Length > 0 && !mapped.Contains(x)).GroupBy(x => x, StringComparer.OrdinalIgnoreCase).OrderByDescending(g => g.Count()).ThenBy(g => g.Key).Select(g => g.Key).ToArray();
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

    private int StableLinguisticsRoll(string text, string language) => (int)(StableHash($"roll|{CharacterName}|{language}|{text}") % 101u);

    private string ScrambleByLegibility(string text, string language, int percent)
    {
        percent = Math.Clamp(percent, 0, 100);
        if (percent >= 100) return text;
        var parts = SplitPreservingWhitespace(text);
        var wordPositions = Enumerable.Range(0, parts.Count).Where(i => ContainsWordCharacter(parts[i])).ToArray();
        if (wordPositions.Length == 0) return text;
        var revealCount = Math.Clamp((int)Math.Round(wordPositions.Length * percent / 100.0, MidpointRounding.AwayFromZero), 0, wordPositions.Length);
        var revealed = wordPositions.OrderBy(i => StableHash($"reveal|{language}|{text}|{i}")).Take(revealCount).ToHashSet();
        foreach (var i in wordPositions)
        {
            if (revealed.Contains(i)) continue;
            var clean = NormalizeLexiconText(parts[i]);
            var custom = LanguageLexicon.Where(x => x.Language.Equals(language, StringComparison.OrdinalIgnoreCase) && x.Source.Equals(clean, StringComparison.OrdinalIgnoreCase)).OrderByDescending(x => x.Source.Length).FirstOrDefault();
            parts[i] = custom is null ? ScrambleWord(parts[i], language, text, i) : ReplaceWordCore(parts[i], custom.Translation);
        }
        return string.Concat(parts);
    }

    private static string ReplaceWordCore(string token, string replacement)
    {
        var first = 0; while (first < token.Length && !char.IsLetterOrDigit(token[first])) first++;
        var last = token.Length - 1; while (last >= first && !char.IsLetterOrDigit(token[last])) last--;
        return first > last ? token : string.Concat(token[..first], replacement, token[(last + 1)..]);
    }

    private static IEnumerable<string> TokenizeWords(string text) => SplitPreservingWhitespace(text).Where(ContainsWordCharacter);
    private static string NormalizeLexiconText(string value) => new(value.Trim().Where(char.IsLetterOrDigit).Select(char.ToLowerInvariant).ToArray());

    private static List<string> SplitPreservingWhitespace(string text)
    {
        var result = new List<string>(); if (text.Length == 0) return result;
        var start = 0; var whitespace = char.IsWhiteSpace(text[0]);
        for (var i = 1; i < text.Length; i++) { var next = char.IsWhiteSpace(text[i]); if (next == whitespace) continue; result.Add(text[start..i]); start = i; whitespace = next; }
        result.Add(text[start..]); return result;
    }

    private static bool ContainsWordCharacter(string value) => value.Any(char.IsLetterOrDigit);

    private static string ScrambleWord(string token, string language, string text, int position)
    {
        var first = 0; while (first < token.Length && !char.IsLetterOrDigit(token[first])) first++;
        var last = token.Length - 1; while (last >= first && !char.IsLetterOrDigit(token[last])) last--;
        if (first > last) return token;
        const string consonants = "bcdfghjklmnprstvwxyz"; const string vowels = "aeiou";
        var seed = StableHash($"mask|{language}|{text}|{position}|{token}"); Span<char> code = stackalloc char[5];
        for (var i = 0; i < code.Length; i++) { seed = unchecked(seed * 1664525u + 1013904223u); var alphabet = i % 2 == 0 ? consonants : vowels; code[i] = alphabet[(int)(seed % (uint)alphabet.Length)]; }
        return string.Concat(token[..first], new string(code), token[(last + 1)..]);
    }

    private static uint StableHash(string value)
    {
        unchecked { var hash = 2166136261u; foreach (var c in value) { hash ^= c; hash *= 16777619u; } return hash; }
    }
}

public sealed class CharacterLanguage(string name, int proficiency) { public string Name { get; set; } = name; public int Proficiency { get; set; } = proficiency; }
public sealed class LanguageLexiconEntry(string language, string source, string translation, string pronunciation = "") { public string Language { get; set; } = language; public string Source { get; set; } = source; public string Translation { get; set; } = translation; public string Pronunciation { get; set; } = pronunciation; }
