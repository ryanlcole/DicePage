namespace RistWorld;

public sealed partial class WorldSession
{
    public List<CharacterLanguage> CharacterLanguages { get; } = [new("Common", 100)];
    public string ActiveRoleplayLanguage { get; private set; } = "Common";
    public string DialogueLanguage { get; set; } = "Common";
    public string PrimaryHumanLanguage { get; private set; } = "English";
    public string GmLanguageResolutionMode { get; private set; } = "system";
    public int GmLanguageLegibilityPercent { get; private set; } = 100;
    public string GmManualLanguageResponse { get; private set; } = "";

    public int LinguisticsValue => CharacterFields
        .Where(field => field.Name.Contains("lingu", StringComparison.OrdinalIgnoreCase)
                     || field.Name.Contains("language", StringComparison.OrdinalIgnoreCase)
                     || field.Name.Contains("comprehension", StringComparison.OrdinalIgnoreCase))
        .Select(field => Math.Max(field.Current, field.BaseValue))
        .DefaultIfEmpty(0)
        .Max();

    public void EnsureCharacterLanguages()
    {
        if (CharacterLanguages.Count == 0) CharacterLanguages.Add(new("Common", 100));
        if (!CharacterLanguages.Any(x => x.Name.Equals("Common", StringComparison.OrdinalIgnoreCase))) CharacterLanguages.Insert(0, new("Common", 100));
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
        language.Proficiency = Math.Clamp(percent, 0, 100);
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
        if (Role == "GM" && GmLanguageResolutionMode == "percent") return GmLanguageLegibilityPercent;
        if (Role == "GM" && GmLanguageResolutionMode == "manual") return 100;

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
        if (Role == "GM" && GmLanguageResolutionMode == "manual" && !string.IsNullOrWhiteSpace(GmManualLanguageResponse)) return GmManualLanguageResponse;
        return MaskByLegibility(text, RoleplayLegibilityPercent(language, text));
    }

    private int StableLinguisticsRoll(string text, string language)
    {
        unchecked
        {
            var hash = 17;
            foreach (var c in $"{CharacterName}|{language}|{text}") hash = hash * 31 + c;
            return Math.Abs(hash % 101);
        }
    }

    private static string MaskByLegibility(string text, int percent)
    {
        if (percent >= 100) return text;
        if (percent <= 0) return string.Concat(text.Select(c => char.IsWhiteSpace(c) || char.IsPunctuation(c) ? c : '•'));
        var words = text.Split(' ');
        for (var i = 0; i < words.Length; i++)
        {
            var reveal = Math.Abs(HashCode.Combine(words[i], i, text.Length)) % 100 < percent;
            if (reveal) continue;
            words[i] = string.Concat(words[i].Select(c => char.IsLetterOrDigit(c) ? '•' : c));
        }
        return string.Join(' ', words);
    }
}

public sealed class CharacterLanguage(string name, int proficiency)
{
    public string Name { get; set; } = name;
    public int Proficiency { get; set; } = proficiency;
}
