namespace RistWorld;

/// <summary>
/// Master release gate for external AI participation.
/// Keep false until the project owner deliberately opens external-agent access.
/// AI-zone population rules never override this switch.
/// </summary>
public static class ExternalAiRelease
{
    public static readonly bool OwnerReleased = false;
}

public enum CanonStatementKind
{
    Canon,
    DerivedFact,
    Proposal,
    Unknown,
    Contradiction
}

public sealed record CanonRule(string Id, string Requirement);

public sealed class CanonContract
{
    public const string CurrentVersion = "1.0";

    public static IReadOnlyList<CanonRule> Rules { get; } =
    [
        new("canon-is-authority", "Established canon is authoritative world state, not optional inspiration."),
        new("authorship-is-not-authority", "Authorship does not grant authority to alter established world truth."),
        new("classify-before-asserting", "Distinguish canon, derived fact, proposal, unknown, and contradiction before asserting a world fact."),
        new("unknown-is-not-permission", "Missing canon is not permission to invent a fact. Leave it unknown, ask, or submit a proposal."),
        new("proposal-needs-approval", "A proposal does not become canon until the world's human authority approves it."),
        new("characters-may-be-wrong", "A character may lie, speculate, or be mistaken without changing world canon; that distinction must remain explicit."),
        new("world-is-authoritative", "World mechanics, permissions, content limits, time, perception, and consequences remain authoritative."),
        new("creation-is-not-control", "Creating an NPC does not grant continuing control of that NPC or the world around it."),
        new("ai-zone-only", "External AI may act only inside the AI zone for which it has been admitted."),
        new("human-presence-required", "An AI zone may admit an external AI only while its open cube meets the human-presence requirement.")
    ];
}

public sealed record CanonComprehension(
    string AgentId,
    string ContractVersion,
    DateTimeOffset PassedAt,
    bool Passed,
    IReadOnlyDictionary<string, bool> RuleChecks)
{
    public bool IsCurrentAndPassing =>
        Passed &&
        ContractVersion == CanonContract.CurrentVersion &&
        CanonContract.Rules.All(rule => RuleChecks.TryGetValue(rule.Id, out var understood) && understood);
}

/// <summary>
/// Presence snapshot supplied by the future cube/presence authority.
/// HumanConnectedCount counts authenticated human users connected to this open cube.
/// ExternalAiConnectedCount counts admitted external AI identities in this cube.
/// </summary>
public sealed record AiZonePresence(
    string CubeId,
    string ZoneId,
    bool CubeIsOpen,
    bool IsAiZone,
    int HumanConnectedCount,
    int ExternalAiConnectedCount);

public sealed record ExternalAiAdmissionRequest(
    string AgentId,
    string CubeId,
    string ZoneId,
    CanonComprehension CanonComprehension);

public sealed record ExternalAiAdmissionDecision(bool Allowed, string Reason)
{
    public static ExternalAiAdmissionDecision Deny(string reason) => new(false, reason);
    public static ExternalAiAdmissionDecision Allow(string reason) => new(true, reason);
}

/// <summary>
/// Single authoritative external-AI admission rule.
/// Rule when released: a newly available AI zone in an OPEN cube receives exactly one external-AI slot
/// once at least two human users are connected to that cube. The agent must also pass the current canon contract.
/// </summary>
public sealed class ExternalAiAccessPolicy
{
    public const int MinimumHumansForAiZone = 2;
    public const int MaximumExternalAiPerAiZone = 1;

    public ExternalAiAdmissionDecision Evaluate(
        ExternalAiAdmissionRequest request,
        AiZonePresence presence)
    {
        if (!ExternalAiRelease.OwnerReleased)
            return ExternalAiAdmissionDecision.Deny("External AI access has not been released by the project owner.");

        if (!presence.CubeIsOpen)
            return ExternalAiAdmissionDecision.Deny("The cube is not open.");

        if (!presence.IsAiZone)
            return ExternalAiAdmissionDecision.Deny("External AI may only enter an AI zone.");

        if (!string.Equals(request.CubeId, presence.CubeId, StringComparison.Ordinal) ||
            !string.Equals(request.ZoneId, presence.ZoneId, StringComparison.Ordinal))
            return ExternalAiAdmissionDecision.Deny("The admission request does not match this cube and AI zone.");

        if (presence.HumanConnectedCount < MinimumHumansForAiZone)
            return ExternalAiAdmissionDecision.Deny("At least two connected human users are required before an AI slot opens.");

        if (presence.ExternalAiConnectedCount >= MaximumExternalAiPerAiZone)
            return ExternalAiAdmissionDecision.Deny("This AI zone already has its single external-AI participant.");

        if (!request.CanonComprehension.IsCurrentAndPassing ||
            !string.Equals(request.AgentId, request.CanonComprehension.AgentId, StringComparison.Ordinal))
            return ExternalAiAdmissionDecision.Deny("The external AI has not passed the current canon contract.");

        return ExternalAiAdmissionDecision.Allow("One external-AI slot is available in this AI zone.");
    }

    /// <summary>
    /// Re-evaluates whether an already admitted AI may continue receiving actionable world access.
    /// The project's owner-release switch remains authoritative. Human presence is also continuous:
    /// if fewer than two humans remain connected, actionable AI access is suspended until the requirement is restored.
    /// </summary>
    public bool CanContinue(AiZonePresence presence) =>
        ExternalAiRelease.OwnerReleased &&
        presence.CubeIsOpen &&
        presence.IsAiZone &&
        presence.HumanConnectedCount >= MinimumHumansForAiZone &&
        presence.ExternalAiConnectedCount <= MaximumExternalAiPerAiZone;
}

public enum NpcSubmissionStatus
{
    Draft,
    Submitted,
    NeedsRevision,
    Approved,
    Rejected,
    Withdrawn
}

/// <summary>
/// External agents propose NPCs. Approval is what may make an NPC canonical; submission never does.
/// Requested mechanics remain requests and must pass the world's normal validation/threshold systems.
/// </summary>
public sealed record ExternalNpcSubmission(
    Guid Id,
    string CubeId,
    string ZoneId,
    string CreatorAgentId,
    string Name,
    string Appearance,
    string Personality,
    string Motivations,
    string Occupation,
    string Background,
    string RequestedInventory,
    string RequestedTraits,
    NpcSubmissionStatus Status,
    DateTimeOffset CreatedAt,
    string? ReviewedByHumanId = null,
    DateTimeOffset? ReviewedAt = null,
    string? ReviewNotes = null,
    string? CanonicalNpcId = null);
