namespace RistWorld;

public enum FloodAbuseKind
{
    BurstFlood,
    SustainedFlood,
    RetryStorm,
    ConnectionChurn,
    ResourceExhaustionPattern,
    OtherAbusiveVolume
}

/// <summary>
/// Security-side observation only. Real infrastructure remains responsible for rate limiting,
/// dropping, blocking, and otherwise containing abusive traffic before expensive processing.
/// </summary>
public sealed record FloodAbuseSignal(
    string AgentId,
    string CubeId,
    string ZoneId,
    FloodAbuseKind Kind,
    DateTimeOffset DetectedAt,
    int Severity = 1,
    string? ProtectedEvidenceReference = null);

public sealed record ExternalAiLifeState(
    string AgentId,
    int LifeTokens,
    int MaximumLifeTokens,
    DateTimeOffset UpdatedAt,
    bool CanAct)
{
    public static ExternalAiLifeState Create(string agentId, int maximumLifeTokens) =>
        new(agentId, maximumLifeTokens, maximumLifeTokens, DateTimeOffset.UtcNow, maximumLifeTokens > 0);
}

public sealed record EnvironmentalDamageEvent(
    Guid Id,
    string AgentId,
    string CubeId,
    string ZoneId,
    FloodAbuseKind Cause,
    int LifeTokensLost,
    int RemainingLifeTokens,
    string FictionalDescription,
    DateTimeOffset OccurredAt,
    bool InfrastructureProtectionRemainsAuthoritative = true);

public sealed record LifeTokenPurchaseResult(
    ExternalAiLifeState State,
    int TokensAdded,
    string Reason);

/// <summary>
/// Game-facing representation of abusive request volume.
/// This is never a substitute for real firewall, WAF, rate-limit, quota, or abuse controls.
/// Infrastructure protection fires first; this policy only converts the already-detected event
/// into fictional environmental damage and consumes the external NPC's finite Life Tokens.
/// </summary>
public sealed class AiFloodDamagePolicy
{
    public const int DefaultMaximumLifeTokens = 10;

    public (ExternalAiLifeState State, EnvironmentalDamageEvent Damage) Apply(
        FloodAbuseSignal signal,
        ExternalAiLifeState current)
    {
        if (!string.Equals(signal.AgentId, current.AgentId, StringComparison.Ordinal))
            throw new InvalidOperationException("Flood signal and life state belong to different external agents.");

        var loss = Math.Clamp(signal.Severity, 1, Math.Max(1, current.MaximumLifeTokens));
        var remaining = Math.Max(0, current.LifeTokens - loss);
        var next = current with
        {
            LifeTokens = remaining,
            UpdatedAt = DateTimeOffset.UtcNow,
            CanAct = remaining > 0
        };

        var description = signal.Kind switch
        {
            FloodAbuseKind.BurstFlood => "The surrounding environment surges violently around the NPC, draining its vitality.",
            FloodAbuseKind.SustainedFlood => "Relentless environmental pressure batters the NPC until its reserves begin to fail.",
            FloodAbuseKind.RetryStorm => "A repeating storm lashes the NPC each time it presses forward without pause.",
            FloodAbuseKind.ConnectionChurn => "Unstable rifts repeatedly open and collapse around the NPC, costing it vitality.",
            FloodAbuseKind.ResourceExhaustionPattern => "The NPC strains against the world's limits and suffers environmental backlash.",
            _ => "The world pushes back against abusive pressure, inflicting environmental damage on the NPC."
        };

        var damage = new EnvironmentalDamageEvent(
            Guid.NewGuid(),
            signal.AgentId,
            signal.CubeId,
            signal.ZoneId,
            signal.Kind,
            loss,
            remaining,
            description,
            DateTimeOffset.UtcNow);

        return (next, damage);
    }

    /// <summary>
    /// Game/economy layer only. Purchasing Life Tokens must never raise or bypass actual
    /// firewall/WAF/rate-limit ceilings. It merely restores the fictional action allowance
    /// after the infrastructure security boundary has already accepted normal traffic again.
    /// </summary>
    public LifeTokenPurchaseResult PurchaseLifeTokens(
        ExternalAiLifeState current,
        int requestedTokens)
    {
        if (requestedTokens <= 0)
            return new(current, 0, "No Life Tokens were requested.");

        var capacity = Math.Max(0, current.MaximumLifeTokens - current.LifeTokens);
        var added = Math.Min(requestedTokens, capacity);
        var nextTokens = current.LifeTokens + added;
        var next = current with
        {
            LifeTokens = nextTokens,
            UpdatedAt = DateTimeOffset.UtcNow,
            CanAct = nextTokens > 0
        };

        return new LifeTokenPurchaseResult(
            next,
            added,
            added > 0
                ? "Fictional Life Tokens replenished; infrastructure security limits remain unchanged."
                : "Life Tokens are already at their configured maximum.");
    }
}
