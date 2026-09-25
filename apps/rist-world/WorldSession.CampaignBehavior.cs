using System.Text.Json;

namespace RistWorld;

public sealed partial class WorldSession
{
    public const string CampaignBehaviorFormat = "RIST_CAMPAIGN_BEHAVIOR_V1";

    public static readonly string[] CampaignBehaviorKinds =
    [
        "PERCEPTION_THRESHOLD",
        "CONTEXTUAL_INTERACTION",
        "TRAP",
        "ENEMY_TRIGGER",
        "INITIATIVE_PRESENTATION",
        "NPC",
        "LOOT",
        "ENCOUNTER"
    ];

    public string CampaignBehaviorStorageKey => $"{WorldStoragePrefix}/campaign/behavior.json";
    public string CampaignBehaviorLocalSaveKey => $"rist.campaign.behavior.v1.{WorldId}";

    CampaignBehaviorState? _campaignBehavior;

    public CampaignBehaviorState CampaignBehavior =>
        NormalizeCampaignBehaviorState(_campaignBehavior ?? NewCampaignBehaviorState());

    public async Task<CampaignBehaviorState> LoadCampaignBehaviorAsync()
    {
        CampaignBehaviorState? state = null;
        if (!HasActiveWorld)
        {
            _campaignBehavior = NewCampaignBehaviorState();
            return _campaignBehavior;
        }

        if (IsLoggedIn)
        {
            try { state = await auth.DownloadJsonAsync<CampaignBehaviorState>(CampaignBehaviorStorageKey); }
            catch { }
        }

        if (state is null)
        {
            try
            {
                var raw = await js.InvokeAsync<string?>("localStorage.getItem", CampaignBehaviorLocalSaveKey);
                if (!string.IsNullOrWhiteSpace(raw))
                    state = JsonSerializer.Deserialize<CampaignBehaviorState>(raw, MapReadOptions);
            }
            catch { }
        }

        _campaignBehavior = NormalizeCampaignBehaviorState(state ?? NewCampaignBehaviorState());
        Notify();
        return _campaignBehavior;
    }

    public async Task<CampaignBehaviorState> SaveCampaignBehaviorAsync(CampaignBehaviorState state)
    {
        if (!HasActiveWorld)
            throw new InvalidOperationException("Choose a world before saving Campaign behavior.");

        var normalized = NormalizeCampaignBehaviorState(state);
        var json = JsonSerializer.Serialize(normalized, MapWriteOptions);
        await js.InvokeVoidAsync("localStorage.setItem", CampaignBehaviorLocalSaveKey, json);
        if (IsLoggedIn)
            await auth.UploadTextAsync(CampaignBehaviorStorageKey, json, "application/json");

        _campaignBehavior = normalized;
        Notify();
        return normalized;
    }

    public async Task<CampaignBehaviorRule> UpsertCampaignBehaviorRuleAsync(CampaignBehaviorRule rule)
    {
        var state = _campaignBehavior ?? await LoadCampaignBehaviorAsync();
        var normalized = NormalizeCampaignBehaviorRule(rule);
        if (string.IsNullOrWhiteSpace(normalized.TargetId))
            throw new InvalidOperationException("Choose a stable target identity for this Campaign behavior.");

        var rules = state.Rules.ToList();
        var index = rules.FindIndex(item =>
            string.Equals(item.RuleId, normalized.RuleId, StringComparison.Ordinal));
        if (index >= 0) rules[index] = normalized;
        else rules.Add(normalized);

        var saved = await SaveCampaignBehaviorAsync(state with
        {
            Rules = rules,
            UpdatedAtUtc = DateTimeOffset.UtcNow
        });
        return saved.Rules.First(item =>
            string.Equals(item.RuleId, normalized.RuleId, StringComparison.Ordinal));
    }

    public async Task<bool> DeleteCampaignBehaviorRuleAsync(string ruleId)
    {
        var state = _campaignBehavior ?? await LoadCampaignBehaviorAsync();
        ruleId = (ruleId ?? "").Trim();
        if (ruleId.Length == 0) return false;

        var rules = state.Rules
            .Where(item => !string.Equals(item.RuleId, ruleId, StringComparison.Ordinal))
            .ToList();
        if (rules.Count == state.Rules.Count) return false;

        await SaveCampaignBehaviorAsync(state with
        {
            Rules = rules,
            UpdatedAtUtc = DateTimeOffset.UtcNow
        });
        return true;
    }

    public CampaignBehaviorRule NewCampaignBehaviorRule(
        string targetKind,
        string targetId,
        string behaviorKind = "CONTEXTUAL_INTERACTION")
        => NormalizeCampaignBehaviorRule(new(
            RuleId: $"campaign-rule-{Guid.NewGuid():N}",
            Name: "",
            BehaviorKind: behaviorKind,
            TargetKind: targetKind,
            TargetId: targetId,
            Threshold: "",
            Trigger: "",
            Action: "",
            PayloadRefId: "",
            Notes: "",
            Enabled: true,
            UpdatedAtUtc: DateTimeOffset.UtcNow));

    CampaignBehaviorState NewCampaignBehaviorState()
        => new(
            Format: CampaignBehaviorFormat,
            WorldId: WorldId,
            Rules: [],
            UpdatedAtUtc: DateTimeOffset.UtcNow);

    CampaignBehaviorState NormalizeCampaignBehaviorState(CampaignBehaviorState state)
    {
        var rules = (state.Rules ?? [])
            .Where(item => item is not null)
            .Select(NormalizeCampaignBehaviorRule)
            .Where(item => item.RuleId.Length > 0 && item.TargetId.Length > 0)
            .GroupBy(item => item.RuleId, StringComparer.Ordinal)
            .Select(group => group.OrderByDescending(item => item.UpdatedAtUtc).First())
            .OrderBy(item => item.Name, StringComparer.OrdinalIgnoreCase)
            .ThenBy(item => item.RuleId, StringComparer.Ordinal)
            .ToList();

        return state with
        {
            Format = CampaignBehaviorFormat,
            WorldId = WorldId,
            Rules = rules
        };
    }

    public static CampaignBehaviorRule NormalizeCampaignBehaviorRule(CampaignBehaviorRule rule)
    {
        var kind = NormalizeCampaignBehaviorKind(rule.BehaviorKind);
        var ruleId = (rule.RuleId ?? "").Trim();
        if (ruleId.Length == 0) ruleId = $"campaign-rule-{Guid.NewGuid():N}";
        return rule with
        {
            RuleId = ruleId,
            Name = NormalizeCampaignText(rule.Name, 120),
            BehaviorKind = kind,
            TargetKind = NormalizeCampaignTargetKind(rule.TargetKind),
            TargetId = (rule.TargetId ?? "").Trim(),
            Threshold = NormalizeCampaignText(rule.Threshold, 240),
            Trigger = NormalizeCampaignText(rule.Trigger, 1000),
            Action = NormalizeCampaignText(rule.Action, 2000),
            PayloadRefId = (rule.PayloadRefId ?? "").Trim(),
            Notes = NormalizeCampaignText(rule.Notes, 4000),
            UpdatedAtUtc = rule.UpdatedAtUtc == default ? DateTimeOffset.UtcNow : rule.UpdatedAtUtc
        };
    }

    public static string NormalizeCampaignBehaviorKind(string? value)
    {
        var key = (value ?? "").Trim().ToUpperInvariant();
        return CampaignBehaviorKinds.Contains(key, StringComparer.Ordinal)
            ? key
            : "CONTEXTUAL_INTERACTION";
    }

    public static string NormalizeCampaignTargetKind(string? value)
    {
        var key = (value ?? "").Trim().ToUpperInvariant();
        return key switch
        {
            "WORLD" or "REGION" or "LOCAL" or "INSTANCE" or "ASSET" or "CELL" or "SURFACE" => key,
            _ => "ASSET"
        };
    }

    static string NormalizeCampaignText(string? value, int maxLength)
    {
        var text = (value ?? "").Trim();
        return text.Length <= maxLength ? text : text[..maxLength];
    }
}

public sealed record CampaignBehaviorState(
    string Format,
    string WorldId,
    List<CampaignBehaviorRule> Rules,
    DateTimeOffset UpdatedAtUtc);

public sealed record CampaignBehaviorRule(
    string RuleId,
    string Name,
    string BehaviorKind,
    string TargetKind,
    string TargetId,
    string Threshold,
    string Trigger,
    string Action,
    string PayloadRefId,
    string Notes,
    bool Enabled,
    DateTimeOffset UpdatedAtUtc);
