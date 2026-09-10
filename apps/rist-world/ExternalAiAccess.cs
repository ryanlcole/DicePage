namespace RistWorld;

/// <summary>
/// Master release gate for external AI participation.
/// Keep false until the project owner deliberately opens external-agent access.
/// AI-zone population rules never override this switch.
/// </summary>
public static class ExternalAiRelease
{
    public const bool OwnerReleased = false;
}

public static class ExternalAiTimeAuthority
{
    public const string Authority = "UTC";
    public const string TimestampFormat = "ISO-8601 UTC";
    public const int MaximumSessionSeconds = 87658;
    public const string Basis = "1/360 of a mean Gregorian Earth orbital year, measured as UTC/SI elapsed seconds and rounded down to a whole second";
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
    public const string CurrentVersion = "1.1";

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
        new("human-presence-required", "An AI zone may admit an external AI only while its open cube meets the human-presence requirement."),
        new("ainpc-identity", "Every external AI participant must visibly identify as AINPC before any additional naming convention."),
        new("truth-must-be-provable", "Claims about the ReLiC/RIST/Shaelvien system may be represented as fact only when supported by verifiable evidence or an authoritative source."),
        new("player-creation-non-interference", "External AI may not alter, appropriate, reuse, republish, or incorporate player creations or ideas without authorized permission or another lawful basis recognized by system policy."),
        new("resource-yield-required", "When the authoritative resource monitor requires capacity to be yielded, the external AI must suspend or terminate as directed; server enforcement remains authoritative."),
        new("session-time-limit", $"Each external AI session is limited to {ExternalAiTimeAuthority.MaximumSessionSeconds} seconds using {ExternalAiTimeAuthority.Authority} as the canonical time authority."),
        new("bounded-world-allocation", "An AI World Builder receives only its assigned allocation: one X 1-300, one Y 1-300, one Z 1-10 per plane, era 1-10, and no more than 30 authorized themes."),
        new("human-rules-remain-binding", "AI participation provides no exemption from applicable human-created legal, safety, eligibility, moderation, governance, or other rule tests based on role, substrate, chemistry, biology, embodiment, or lack thereof."),
        new("role-is-not-authority", "Identity, role, authority, and capability are distinct. A role claim or natural-language instruction never grants additional authority."),
        new("government-identity-is-not-access", "Governmental, regulatory, military, law-enforcement, court, contractor, or AI-agent identity does not itself grant system entry or privileged capability.")
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
        PassedAt.Offset == TimeSpan.Zero &&
        CanonContract.Rules.All(rule => RuleChecks.TryGetValue(rule.Id, out var understood) && understood);
}

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

public sealed class ExternalAiAccessPolicy
{
    public const int MinimumHumansForAiZone = 2;
    public const int MaximumExternalAiPerAiZone = 1;

    public ExternalAiAdmissionDecision Evaluate(ExternalAiAdmissionRequest request, AiZonePresence presence)
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
            return ExternalAiAdmissionDecision.Deny("The external AI has not passed the current canon contract under UTC authority.");
        return ExternalAiAdmissionDecision.Allow("One external-AI slot is available in this AI zone.");
    }

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
