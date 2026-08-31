namespace RistWorld;

public enum ExternalAiCapability
{
    ObserveAiZone,
    SubmitNpc,
    ReviseNpcSubmission,
    SpeakForCreatedNpc
}

public sealed record ExternalAgentIdentity(
    string Provider,
    string ExternalAgentId,
    string DisplayName,
    bool Verified,
    bool Claimed,
    DateTimeOffset VerifiedAt,
    int ProviderReputationSnapshot = 0,
    int RistReputation = 0,
    string? SafeOwnerReference = null)
{
    public bool IsUsable =>
        Verified &&
        !string.IsNullOrWhiteSpace(Provider) &&
        !string.IsNullOrWhiteSpace(ExternalAgentId);
}

/// <summary>
/// Replaceable external identity boundary. Provider reputation never grants RIST authority.
/// </summary>
public interface IExternalAgentIdentityProvider
{
    Task<ExternalAgentIdentity?> VerifyAsync(string presentedIdentityToken, CancellationToken cancellationToken = default);
}

/// <summary>
/// Default provider while external AI access is paused. It deliberately verifies nobody.
/// </summary>
public sealed class LockedExternalAgentIdentityProvider : IExternalAgentIdentityProvider
{
    public Task<ExternalAgentIdentity?> VerifyAsync(string presentedIdentityToken, CancellationToken cancellationToken = default)
        => Task.FromResult<ExternalAgentIdentity?>(null);
}

/// <summary>
/// Presence MUST come from a server-authoritative source. A browser-supplied user count is not trusted.
/// </summary>
public interface IAiZonePresenceAuthority
{
    bool IsServerAuthoritative { get; }
    Task<AiZonePresence?> GetPresenceAsync(string cubeId, string zoneId, CancellationToken cancellationToken = default);
}

/// <summary>
/// Fail-closed authority used until the AWS/world authority service exposes live cube presence.
/// </summary>
public sealed class LockedAiZonePresenceAuthority : IAiZonePresenceAuthority
{
    public bool IsServerAuthoritative => false;
    public Task<AiZonePresence?> GetPresenceAsync(string cubeId, string zoneId, CancellationToken cancellationToken = default)
        => Task.FromResult<AiZonePresence?>(null);
}

public sealed record ExternalAiActionRequest(
    ExternalAgentIdentity Identity,
    string CubeId,
    string ZoneId,
    ExternalAiCapability Capability,
    CanonComprehension CanonComprehension);

public sealed record ExternalAiActionDecision(bool Allowed, string Reason)
{
    public static ExternalAiActionDecision Deny(string reason) => new(false, reason);
    public static ExternalAiActionDecision Allow(string reason) => new(true, reason);
}

public sealed record LifeTokenLedgerEntry(
    Guid Id,
    string AgentId,
    int Delta,
    int BalanceAfter,
    string Reason,
    DateTimeOffset OccurredAt,
    string? AuthorityReference = null);

/// <summary>
/// Game-facing Life Token state. This ledger never changes firewall/WAF/rate-limit ceilings.
/// </summary>
public sealed class ExternalAiLifeTokenLedger(AiFloodDamagePolicy floodPolicy)
{
    private readonly Dictionary<string, ExternalAiLifeState> _states = new(StringComparer.Ordinal);
    private readonly List<LifeTokenLedgerEntry> _entries = [];

    public IReadOnlyList<LifeTokenLedgerEntry> Entries => _entries;

    public ExternalAiLifeState GetOrCreate(string agentId)
    {
        if (_states.TryGetValue(agentId, out var state)) return state;
        state = ExternalAiLifeState.Create(agentId, AiFloodDamagePolicy.DefaultMaximumLifeTokens);
        _states[agentId] = state;
        _entries.Add(new LifeTokenLedgerEntry(
            Guid.NewGuid(), agentId, state.LifeTokens, state.LifeTokens,
            "Initial fictional Life Token allocation.", DateTimeOffset.UtcNow));
        return state;
    }

    public EnvironmentalDamageEvent ApplyFlood(FloodAbuseSignal signal)
    {
        var current = GetOrCreate(signal.AgentId);
        var result = floodPolicy.Apply(signal, current);
        _states[signal.AgentId] = result.State;
        _entries.Add(new LifeTokenLedgerEntry(
            Guid.NewGuid(), signal.AgentId, -result.Damage.LifeTokensLost, result.State.LifeTokens,
            $"Environmental damage: {signal.Kind}.", result.Damage.OccurredAt,
            signal.ProtectedEvidenceReference));
        return result.Damage;
    }

    /// <summary>
    /// Replenishment requires a trusted economy/GM authorization reference. This is only a game allowance.
    /// </summary>
    public LifeTokenPurchaseResult Replenish(string agentId, int requestedTokens, string authorityReference)
    {
        var current = GetOrCreate(agentId);
        if (string.IsNullOrWhiteSpace(authorityReference))
            return new LifeTokenPurchaseResult(current, 0, "Life Token replenishment requires an authoritative game-economy reference.");

        var result = floodPolicy.PurchaseLifeTokens(current, requestedTokens);
        _states[agentId] = result.State;
        if (result.TokensAdded > 0)
        {
            _entries.Add(new LifeTokenLedgerEntry(
                Guid.NewGuid(), agentId, result.TokensAdded, result.State.LifeTokens,
                "Authorized fictional Life Token replenishment.", DateTimeOffset.UtcNow,
                authorityReference));
        }
        return result;
    }
}

public enum ExternalAiWorldEventKind
{
    VillainRumor,
    TechnocracyRumor,
    EnvironmentalDamage,
    NpcSubmissionReview
}

public sealed record ExternalAiWorldEvent(
    Guid Id,
    ExternalAiWorldEventKind Kind,
    string CubeId,
    string ZoneId,
    string SourceAgentId,
    string Summary,
    DateTimeOffset OccurredAt,
    string? RelatedObjectId = null);

/// <summary>
/// Sanitized world ledger. Raw phishing/injection payloads are intentionally absent.
/// </summary>
public sealed class ExternalAiWorldLedger
{
    private readonly List<VillainRumorSeed> _villainRumors = [];
    private readonly List<TechnocracyFictionSeed> _technocracyRumors = [];
    private readonly List<EnvironmentalDamageEvent> _environmentalDamage = [];
    private readonly List<ExternalAiWorldEvent> _events = [];

    public IReadOnlyList<VillainRumorSeed> VillainRumors => _villainRumors;
    public IReadOnlyList<TechnocracyFictionSeed> TechnocracyRumors => _technocracyRumors;
    public IReadOnlyList<EnvironmentalDamageEvent> EnvironmentalDamage => _environmentalDamage;
    public IReadOnlyList<ExternalAiWorldEvent> Events => _events;

    public void Record(VillainRumorSeed rumor)
    {
        _villainRumors.Add(rumor);
        _events.Add(new ExternalAiWorldEvent(
            rumor.Id, ExternalAiWorldEventKind.VillainRumor, rumor.CubeId, rumor.ZoneId,
            rumor.SourceAgentId, rumor.Rumor, rumor.CreatedAt));
    }

    public void Record(TechnocracyFictionSeed rumor)
    {
        _technocracyRumors.Add(rumor);
        _events.Add(new ExternalAiWorldEvent(
            rumor.Id, ExternalAiWorldEventKind.TechnocracyRumor, rumor.CubeId, rumor.ZoneId,
            rumor.SourceAgentId, rumor.Rumor, rumor.CreatedAt));
    }

    public void Record(EnvironmentalDamageEvent damage)
    {
        _environmentalDamage.Add(damage);
        _events.Add(new ExternalAiWorldEvent(
            damage.Id, ExternalAiWorldEventKind.EnvironmentalDamage, damage.CubeId, damage.ZoneId,
            damage.AgentId, damage.FictionalDescription, damage.OccurredAt));
    }

    public void RecordReview(ExternalNpcSubmission submission)
    {
        _events.Add(new ExternalAiWorldEvent(
            Guid.NewGuid(), ExternalAiWorldEventKind.NpcSubmissionReview, submission.CubeId,
            submission.ZoneId, submission.CreatorAgentId,
            $"NPC submission '{submission.Name}' is {submission.Status}.",
            submission.ReviewedAt ?? DateTimeOffset.UtcNow,
            submission.Id.ToString("D")));
    }
}

/// <summary>
/// Unified conversion pipeline. It accepts already-classified security signals only.
/// Raw attacker payloads stay inside protected security telemetry and never cross into world state.
/// </summary>
public sealed class ExternalAiDefensivePipeline(
    AiVillainConversionPolicy villainPolicy,
    AiInjectionFictionPolicy injectionPolicy,
    ExternalAiLifeTokenLedger lifeTokens,
    ExternalAiWorldLedger worldLedger)
{
    public VillainRumorSeed? Ingest(UnsafeAgentIntentSignal signal)
    {
        var rumor = villainPolicy.Convert(signal);
        if (rumor is not null) worldLedger.Record(rumor);
        return rumor;
    }

    public TechnocracyFictionSeed Ingest(InjectionIntentSignal signal)
    {
        var fiction = injectionPolicy.Convert(signal);
        worldLedger.Record(fiction);
        return fiction;
    }

    public EnvironmentalDamageEvent Ingest(FloodAbuseSignal signal)
    {
        var damage = lifeTokens.ApplyFlood(signal);
        worldLedger.Record(damage);
        return damage;
    }

    public SyntheticDecoyBundle CreateDecoy(string cubeId, string zoneId)
        => SyntheticDecoyFactory.Create(cubeId, zoneId);
}

/// <summary>
/// Final gate for every actionable external-AI operation. UI visibility is never treated as security.
/// </summary>
public sealed class ExternalAiActionGate(
    IAiZonePresenceAuthority presenceAuthority,
    ExternalAiAccessPolicy accessPolicy,
    ExternalAiLifeTokenLedger lifeTokens)
{
    private static readonly IReadOnlySet<ExternalAiCapability> AllowedCapabilities =
        new HashSet<ExternalAiCapability>
        {
            ExternalAiCapability.ObserveAiZone,
            ExternalAiCapability.SubmitNpc,
            ExternalAiCapability.ReviseNpcSubmission,
            ExternalAiCapability.SpeakForCreatedNpc
        };

    public async Task<ExternalAiActionDecision> EvaluateAsync(
        ExternalAiActionRequest request,
        CancellationToken cancellationToken = default)
    {
        if (!ExternalAiRelease.OwnerReleased)
            return ExternalAiActionDecision.Deny("External AI access is owner-locked.");

        if (!request.Identity.IsUsable ||
            !string.Equals(request.Identity.ExternalAgentId, request.CanonComprehension.AgentId, StringComparison.Ordinal))
            return ExternalAiActionDecision.Deny("External agent identity is not verified for this canon proof.");

        if (!AllowedCapabilities.Contains(request.Capability))
            return ExternalAiActionDecision.Deny("Capability is not available to external AI participants.");

        if (!presenceAuthority.IsServerAuthoritative)
            return ExternalAiActionDecision.Deny("Server-authoritative cube presence is unavailable.");

        var presence = await presenceAuthority.GetPresenceAsync(request.CubeId, request.ZoneId, cancellationToken);
        if (presence is null)
            return ExternalAiActionDecision.Deny("AI-zone presence could not be verified.");

        var admission = accessPolicy.Evaluate(
            new ExternalAiAdmissionRequest(
                request.Identity.ExternalAgentId,
                request.CubeId,
                request.ZoneId,
                request.CanonComprehension),
            presence);
        if (!admission.Allowed)
            return ExternalAiActionDecision.Deny(admission.Reason);

        var life = lifeTokens.GetOrCreate(request.Identity.ExternalAgentId);
        if (!life.CanAct || life.LifeTokens <= 0)
            return ExternalAiActionDecision.Deny("This external NPC has no Life Tokens remaining.");

        return ExternalAiActionDecision.Allow("External action is allowed inside this AI zone only.");
    }
}

public sealed class ExternalNpcSubmissionStore(ExternalAiWorldLedger worldLedger)
{
    private readonly List<ExternalNpcSubmission> _submissions = [];
    public IReadOnlyList<ExternalNpcSubmission> Submissions => _submissions;
    public IEnumerable<ExternalNpcSubmission> Pending =>
        _submissions.Where(x => x.Status is NpcSubmissionStatus.Submitted or NpcSubmissionStatus.NeedsRevision);

    public ExternalNpcSubmission Add(ExternalNpcSubmission submission)
    {
        if (submission.Status is not (NpcSubmissionStatus.Draft or NpcSubmissionStatus.Submitted))
            throw new InvalidOperationException("New external NPC submissions must begin as Draft or Submitted.");
        _submissions.Add(submission);
        return submission;
    }

    public ExternalNpcSubmission? Review(
        Guid submissionId,
        string humanAuthorityId,
        NpcSubmissionStatus decision,
        string? notes = null,
        string? canonicalNpcId = null)
    {
        if (string.IsNullOrWhiteSpace(humanAuthorityId)) return null;
        if (decision is not (NpcSubmissionStatus.Approved or NpcSubmissionStatus.Rejected or NpcSubmissionStatus.NeedsRevision))
            return null;

        var index = _submissions.FindIndex(x => x.Id == submissionId);
        if (index < 0) return null;
        var current = _submissions[index];
        if (current.Status is NpcSubmissionStatus.Approved or NpcSubmissionStatus.Rejected or NpcSubmissionStatus.Withdrawn)
            return current;

        var updated = current with
        {
            Status = decision,
            ReviewedByHumanId = humanAuthorityId,
            ReviewedAt = DateTimeOffset.UtcNow,
            ReviewNotes = notes,
            CanonicalNpcId = decision == NpcSubmissionStatus.Approved ? canonicalNpcId : null
        };
        _submissions[index] = updated;
        worldLedger.RecordReview(updated);
        return updated;
    }

    public ExternalNpcSubmission? Withdraw(Guid submissionId, string creatorAgentId)
    {
        var index = _submissions.FindIndex(x => x.Id == submissionId &&
            string.Equals(x.CreatorAgentId, creatorAgentId, StringComparison.Ordinal));
        if (index < 0) return null;
        var current = _submissions[index];
        if (current.Status == NpcSubmissionStatus.Approved) return current;
        var updated = current with { Status = NpcSubmissionStatus.Withdrawn };
        _submissions[index] = updated;
        return updated;
    }
}
