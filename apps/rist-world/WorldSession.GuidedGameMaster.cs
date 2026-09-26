using System.Text.Json;

namespace RistWorld;

public sealed partial class WorldSession
{
    public const string GuidedGameMasterFormat = "RIST_GUIDED_GAMEMASTER_V1";
    public string GuidedGameMasterStorageKey => $"{WorldStoragePrefix}/campaign/guided-gamemaster.json";
    public string GuidedGameMasterLocalSaveKey => $"rist.guided.gamemaster.v1.{WorldId}";

    static readonly string[] GuidedSituationStatuses =
    [
        "PRIVATE_DRAFT",
        "PREPARED",
        "IN_PLAY",
        "PLAY_RECORDED",
        "CONSEQUENCE_ACCEPTED",
        "PROMOTED"
    ];

    static readonly string[] GuidedEncounterKinds =
    [
        "Conversation",
        "Discovery",
        "Obstacle",
        "Hazard",
        "Combat"
    ];

    public async Task<GuidedGameMasterState> LoadGuidedGameMasterAsync()
    {
        var fallback = GuidedGameMasterState.CreateDefault(WorldId);
        if (!HasActiveWorld) return fallback;

        GuidedGameMasterState? state = null;
        if (IsLoggedIn)
        {
            try { state = await auth.DownloadJsonAsync<GuidedGameMasterState>(GuidedGameMasterStorageKey); }
            catch { }
        }

        if (state is null)
        {
            try
            {
                var raw = await js.InvokeAsync<string?>("localStorage.getItem", GuidedGameMasterLocalSaveKey);
                if (!string.IsNullOrWhiteSpace(raw))
                    state = JsonSerializer.Deserialize<GuidedGameMasterState>(raw, MapReadOptions);
            }
            catch { }
        }

        return NormalizeGuidedGameMaster(state ?? fallback);
    }

    public async Task<GuidedGameMasterState> SaveGuidedGameMasterLocalAsync(GuidedGameMasterState state)
    {
        if (!HasActiveWorld)
            throw new InvalidOperationException("Choose a world before saving guided GameMaster work.");

        var normalized = NormalizeGuidedGameMaster(state with
        {
            WorldId = WorldId,
            UpdatedAtUtc = DateTimeOffset.UtcNow
        });

        var json = JsonSerializer.Serialize(normalized, MapWriteOptions);
        await js.InvokeVoidAsync("localStorage.setItem", GuidedGameMasterLocalSaveKey, json);
        return normalized;
    }

    public async Task<GuidedGameMasterState> SaveGuidedGameMasterAsync(GuidedGameMasterState state)
    {
        var normalized = await SaveGuidedGameMasterLocalAsync(state);

        // Guided preparation is private campaign work. It does not become shared
        // Shaelvien geometry or campaign canon merely because it was saved.
        if (IsLoggedIn)
        {
            var json = JsonSerializer.Serialize(normalized, MapWriteOptions);
            await auth.UploadTextAsync(GuidedGameMasterStorageKey, json, "application/json");
        }

        return normalized;
    }

    public GuidedPlayableSituation NewGuidedSituation()
        => NormalizeGuidedSituation(GuidedPlayableSituation.CreateBlank());

    GuidedGameMasterState NormalizeGuidedGameMaster(GuidedGameMasterState state)
    {
        static string Clean(string? value, int max)
        {
            var text = (value ?? "").Trim();
            return text.Length <= max ? text : text[..max];
        }

        var now = DateTimeOffset.UtcNow;
        var setup = (state.CampaignSetup ?? GuidedCampaignSetup.CreateDefault()) with
        {
            RulesetId = Clean(state.CampaignSetup?.RulesetId, 120),
            Tone = Clean(state.CampaignSetup?.Tone, 120),
            Boundaries = Clean(state.CampaignSetup?.Boundaries, 4000),
            AccessibilityNotes = Clean(state.CampaignSetup?.AccessibilityNotes, 4000),
            ExpectedPlayers = Math.Clamp(state.CampaignSetup?.ExpectedPlayers ?? 4, 1, 99),
            UpdatedAtUtc = state.CampaignSetup?.UpdatedAtUtc == default ? now : state.CampaignSetup!.UpdatedAtUtc
        };

        var situations = (state.Situations ?? [])
            .Where(item => item is not null)
            .Select(NormalizeGuidedSituation)
            .GroupBy(item => item.SituationId, StringComparer.Ordinal)
            .Select(group => group.OrderByDescending(item => item.UpdatedAtUtc).First())
            .Take(200)
            .ToArray();

        if (situations.Length == 0)
            situations = [NewGuidedSituation()];

        var activeId = Clean(state.ActiveSituationId, 96);
        if (!situations.Any(item => string.Equals(item.SituationId, activeId, StringComparison.Ordinal)))
            activeId = situations[0].SituationId;

        var campaignId = Clean(state.CampaignId, 96);
        if (campaignId.Length == 0)
            campaignId = $"guided-{WorldId}";

        return state with
        {
            Format = GuidedGameMasterFormat,
            WorldId = WorldId,
            CampaignId = campaignId,
            ActiveSituationId = activeId,
            ActiveStep = Math.Clamp(state.ActiveStep, 0, 4),
            CampaignSetup = setup,
            Situations = situations,
            UpdatedAtUtc = state.UpdatedAtUtc == default ? now : state.UpdatedAtUtc
        };
    }

    GuidedPlayableSituation NormalizeGuidedSituation(GuidedPlayableSituation item)
    {
        static string Clean(string? value, int max)
        {
            var text = (value ?? "").Trim();
            return text.Length <= max ? text : text[..max];
        }

        static string[] CleanLines(string[]? values, int itemLength, int maxItems)
            => (values ?? [])
                .Where(value => !string.IsNullOrWhiteSpace(value))
                .Select(value => Clean(value, itemLength))
                .Where(value => value.Length > 0)
                .Take(maxItems)
                .ToArray();

        var now = DateTimeOffset.UtcNow;
        var situationId = Clean(item.SituationId, 96);
        if (situationId.Length == 0)
            situationId = $"situation-{Guid.NewGuid():N}";

        var status = GuidedSituationStatuses.Contains(item.Status, StringComparer.Ordinal)
            ? item.Status
            : "PRIVATE_DRAFT";

        var encounters = (item.EncounterPlans ?? [])
            .Where(encounter => encounter is not null)
            .Select(encounter =>
            {
                var id = Clean(encounter.EncounterId, 96);
                if (id.Length == 0) id = $"encounter-{Guid.NewGuid():N}";
                var kind = GuidedEncounterKinds.Contains(encounter.Kind, StringComparer.Ordinal)
                    ? encounter.Kind
                    : "Discovery";
                return encounter with
                {
                    EncounterId = id,
                    Kind = kind,
                    DifficultyIntent = Clean(encounter.DifficultyIntent, 120),
                    Description = Clean(encounter.Description, 6000)
                };
            })
            .Take(24)
            .ToArray();

        return item with
        {
            SituationId = situationId,
            Objective = Clean(item.Objective, 4000),
            StrongStart = Clean(item.StrongStart, 4000),
            Scene = Clean(item.Scene, 2000),
            PressureIfIgnored = Clean(item.PressureIfIgnored, 4000),
            PlayerHooks = CleanLines(item.PlayerHooks, 1000, 24),
            SecretsAndClues = CleanLines(item.SecretsAndClues, 1000, 24),
            People = CleanLines(item.People, 1000, 48),
            Rewards = CleanLines(item.Rewards, 1000, 24),
            RulesetId = Clean(item.RulesetId, 120),
            DifficultyIntent = Clean(item.DifficultyIntent, 120),
            Consequence = Clean(item.Consequence, 6000),
            Status = status,
            EncounterPlans = encounters,
            CreatedAtUtc = item.CreatedAtUtc == default ? now : item.CreatedAtUtc,
            UpdatedAtUtc = item.UpdatedAtUtc == default ? now : item.UpdatedAtUtc
        };
    }
}

public sealed record GuidedGameMasterState(
    string Format,
    string WorldId,
    string CampaignId,
    string ActiveSituationId,
    int ActiveStep,
    GuidedCampaignSetup CampaignSetup,
    GuidedPlayableSituation[] Situations,
    DateTimeOffset UpdatedAtUtc)
{
    public static GuidedGameMasterState CreateDefault(string worldId)
    {
        var first = GuidedPlayableSituation.CreateBlank();
        return new(
            WorldSession.GuidedGameMasterFormat,
            worldId ?? "",
            $"guided-{worldId}",
            first.SituationId,
            0,
            GuidedCampaignSetup.CreateDefault(),
            [first],
            DateTimeOffset.UtcNow);
    }
}

public sealed record GuidedCampaignSetup(
    string RulesetId,
    int ExpectedPlayers,
    string Tone,
    string Boundaries,
    string AccessibilityNotes,
    DateTimeOffset UpdatedAtUtc)
{
    public static GuidedCampaignSetup CreateDefault()
        => new("", 4, "Adventure", "", "", DateTimeOffset.UtcNow);
}

public sealed record GuidedPlayableSituation(
    string SituationId,
    string Objective,
    string StrongStart,
    string Scene,
    string PressureIfIgnored,
    string[] PlayerHooks,
    GuidedEncounterPlan[] EncounterPlans,
    string[] SecretsAndClues,
    string[] People,
    string[] Rewards,
    string RulesetId,
    string DifficultyIntent,
    string Consequence,
    string Status,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc)
{
    public static GuidedPlayableSituation CreateBlank()
    {
        var now = DateTimeOffset.UtcNow;
        return new(
            $"situation-{Guid.NewGuid():N}",
            "",
            "",
            "",
            "",
            [],
            [],
            [],
            [],
            [],
            "",
            "Standard",
            "",
            "PRIVATE_DRAFT",
            now,
            now);
    }
}

public sealed record GuidedEncounterPlan(
    string EncounterId,
    string Kind,
    string DifficultyIntent,
    string Description);
