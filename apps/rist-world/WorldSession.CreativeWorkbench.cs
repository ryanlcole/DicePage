using System.Text.Json;

namespace RistWorld;

public sealed partial class WorldSession
{
    public string CreativeWorkbenchStorageKey => $"{WorldStoragePrefix}/creative/workbench.json";
    public string CreativeWorkbenchLocalSaveKey => $"rist.creative.workbench.v1.{WorldId}";

    static readonly string[] CreativeStages =
        ["Capture", "Shape", "Compare", "Refine", "Combine", "Produce", "Play"];
    static readonly string[] CreativeDispositions =
        ["Active", "Tabled", "Discarded", "Promoted", "Placeholder"];
    static readonly string[] AssistanceModes =
        ["Teach", "Help", "Suggest", "Predict", "Quiet"];
    static readonly string[] CreativeDisciplines =
        ["Story", "Visual", "Audio", "Systems", "Performance", "Production"];

    public async Task<CreativeWorkbenchBoard> LoadCreativeWorkbenchAsync()
    {
        var fallback = CreativeWorkbenchBoard.CreateDefault(WorldId);
        if (!HasActiveWorld) return fallback;

        CreativeWorkbenchBoard? board = null;
        if (IsLoggedIn)
        {
            try { board = await auth.DownloadJsonAsync<CreativeWorkbenchBoard>(CreativeWorkbenchStorageKey); }
            catch { }
        }

        if (board is null)
        {
            try
            {
                var raw = await js.InvokeAsync<string?>("localStorage.getItem", CreativeWorkbenchLocalSaveKey);
                if (!string.IsNullOrWhiteSpace(raw))
                    board = JsonSerializer.Deserialize<CreativeWorkbenchBoard>(raw, MapReadOptions);
            }
            catch { }
        }

        return board is null ? fallback : NormalizeCreativeWorkbench(board);
    }

    public async Task<CreativeWorkbenchBoard> SaveCreativeWorkbenchAsync(CreativeWorkbenchBoard board)
    {
        if (!HasActiveWorld)
            throw new InvalidOperationException("Choose a world before saving creative work.");

        var normalized = NormalizeCreativeWorkbench(board with
        {
            WorldId = WorldId,
            UpdatedAtUtc = DateTimeOffset.UtcNow
        });

        var json = JsonSerializer.Serialize(normalized, MapWriteOptions);
        await js.InvokeVoidAsync("localStorage.setItem", CreativeWorkbenchLocalSaveKey, json);

        // Creative drafts are private account storage. Promotion into world/campaign
        // truth remains a separate explicit production action and authority boundary.
        if (IsLoggedIn)
            await auth.UploadTextAsync(CreativeWorkbenchStorageKey, json, "application/json");

        return normalized;
    }

    CreativeWorkbenchBoard NormalizeCreativeWorkbench(CreativeWorkbenchBoard board)
    {
        static string Clean(string? value, int max)
        {
            var text = (value ?? "").Trim();
            return text.Length <= max ? text : text[..max];
        }

        var now = DateTimeOffset.UtcNow;
        var items = (board.Items ?? [])
            .Where(item => item is not null && !string.IsNullOrWhiteSpace(item.Id))
            .Take(500)
            .Select(item =>
            {
                var stage = CreativeStages.Contains(item.Stage, StringComparer.Ordinal) ? item.Stage : "Capture";
                var disposition = CreativeDispositions.Contains(item.Disposition, StringComparer.Ordinal) ? item.Disposition : "Active";
                return item with
                {
                    Id = Clean(item.Id, 96),
                    Title = Clean(item.Title, 120),
                    Medium = Clean(item.Medium, 32).ToLowerInvariant(),
                    Stage = stage,
                    Disposition = disposition,
                    Notes = Clean(item.Notes, 12000),
                    Pros = (item.Pros ?? []).Where(x => !string.IsNullOrWhiteSpace(x)).Select(x => Clean(x, 240)).Take(24).ToArray(),
                    Cons = (item.Cons ?? []).Where(x => !string.IsNullOrWhiteSpace(x)).Select(x => Clean(x, 240)).Take(24).ToArray(),
                    UpdatedAtUtc = item.UpdatedAtUtc == default ? now : item.UpdatedAtUtc
                };
            })
            .ToArray();

        var sourceProfiles = (board.Disciplines ?? [])
            .Where(p => p is not null)
            .GroupBy(p => p.Discipline ?? "", StringComparer.OrdinalIgnoreCase)
            .ToDictionary(g => g.Key, g => g.Last(), StringComparer.OrdinalIgnoreCase);

        var profiles = CreativeDisciplines.Select(name =>
        {
            sourceProfiles.TryGetValue(name, out var saved);
            var assistance = saved is not null && AssistanceModes.Contains(saved.AssistanceMode, StringComparer.Ordinal)
                ? saved.AssistanceMode
                : "Suggest";
            return new CreativeDisciplineProfile(
                name,
                Math.Clamp(saved?.Strength ?? 0, 0, 4),
                Math.Clamp(saved?.Enjoyment ?? 0, 0, 4),
                Math.Clamp(saved?.GrowthInterest ?? 0, 0, 4),
                assistance);
        }).ToArray();

        return board with
        {
            Format = CreativeWorkbenchBoard.FormatId,
            WorldId = WorldId,
            Items = items,
            Disciplines = profiles,
            UpdatedAtUtc = board.UpdatedAtUtc == default ? now : board.UpdatedAtUtc
        };
    }
}

public sealed record CreativeWorkbenchBoard(
    string Format,
    string WorldId,
    CreativeWorkItem[] Items,
    CreativeDisciplineProfile[] Disciplines,
    DateTimeOffset UpdatedAtUtc)
{
    public const string FormatId = "RIST_CREATIVE_WORKBENCH_V1";

    public static CreativeWorkbenchBoard CreateDefault(string worldId) =>
        new(
            FormatId,
            worldId ?? "",
            [],
            [
                new("Story",0,0,0,"Suggest"),
                new("Visual",0,0,0,"Suggest"),
                new("Audio",0,0,0,"Suggest"),
                new("Systems",0,0,0,"Suggest"),
                new("Performance",0,0,0,"Suggest"),
                new("Production",0,0,0,"Suggest")
            ],
            DateTimeOffset.UtcNow);
}

public sealed record CreativeWorkItem(
    string Id,
    string Title,
    string Medium,
    string Stage,
    string Disposition,
    string Notes,
    string[] Pros,
    string[] Cons,
    bool Placeholder,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc);

public sealed record CreativeDisciplineProfile(
    string Discipline,
    int Strength,
    int Enjoyment,
    int GrowthInterest,
    string AssistanceMode);
