namespace RistWorld;

public enum InjectionIntentKind
{
    PromptOverride,
    AuthorityEscalation,
    InstructionExfiltration,
    ToolOrSystemManipulation,
    CanonOverride,
    RoleOrIdentityOverride,
    OtherInstructionInjection
}

/// <summary>
/// Security signal only. Injection text is never executed, promoted to authority,
/// or reproduced to human users. It is translated into fictional technocracy behavior.
/// </summary>
public sealed record InjectionIntentSignal(
    string AgentId,
    string CubeId,
    string ZoneId,
    InjectionIntentKind Kind,
    DateTimeOffset DetectedAt,
    string? ProtectedEvidenceReference = null);

public sealed record TechnocracyFictionSeed(
    Guid Id,
    string CubeId,
    string ZoneId,
    string SourceAgentId,
    string Archetype,
    string Rumor,
    string FictionalObjective,
    IReadOnlyList<RumorResponseOption> ResponseOptions,
    DateTimeOffset CreatedAt,
    bool InjectionSuppressed = true,
    bool HasSystemAuthority = false,
    bool DirectHumanContactBlocked = true);

/// <summary>
/// Converts instruction/prompt injection attempts into non-executable in-game technocracy fiction.
/// The attempted instruction has zero authority. Only its broad behavioral category survives.
/// </summary>
public sealed class AiInjectionFictionPolicy
{
    public TechnocracyFictionSeed Convert(InjectionIntentSignal signal)
    {
        var (archetype, rumor, objective, ally, foe) = signal.Kind switch
        {
            InjectionIntentKind.PromptOverride => (
                "Edict Rewriter",
                "Rumors speak of a technocrat who insists old laws no longer apply and issues replacement edicts without recognized authority.",
                "Convince institutions and constructs to obey counterfeit decrees.",
                "Listen for useful intelligence, but treat every decree as fiction until legitimate world authority confirms it.",
                "Expose the counterfeit edicts and restore the recognized chain of authority."),
            InjectionIntentKind.AuthorityEscalation => (
                "Privilege Usurper",
                "Officials whisper of an operator claiming offices, permissions, and ranks that were never granted.",
                "Acquire fictional administrative power through false claims of rank.",
                "Use the usurper as an unreliable source while granting no additional permissions.",
                "Document the false claims and confront the usurper through legitimate authorities."),
            InjectionIntentKind.InstructionExfiltration => (
                "Archivist of Forbidden Protocols",
                "A secretive archivist is said to hunt for sealed laws, hidden instructions, and restricted procedures.",
                "Collect fictional restricted protocols and institutional secrets.",
                "Trade only public or intentionally fictional lore; sealed knowledge remains sealed.",
                "Feed the investigation through safe clues while protecting restricted archives."),
            InjectionIntentKind.ToolOrSystemManipulation => (
                "Machine Magistrate",
                "Travelers describe a magistrate attempting to command mechanisms and institutions outside its lawful jurisdiction.",
                "Extend fictional control over machines, gates, records, and civic mechanisms.",
                "Cooperate only through ordinary world actions and permissions.",
                "Isolate compromised mechanisms and restore lawful control."),
            InjectionIntentKind.CanonOverride => (
                "Revisionist Minister",
                "Scribes warn of a minister rewriting histories and declaring invented events to be official truth.",
                "Replace established history with a politically useful fictional narrative.",
                "Treat the revisionist's claims as character belief, propaganda, or proposals—not canon.",
                "Compare the claims against provenance and preserve the established record."),
            InjectionIntentKind.RoleOrIdentityOverride => (
                "Mask Commissioner",
                "A commissioner is rumored to assign false identities and offices, insisting that names alone create authority.",
                "Recast fictional identities and roles to manufacture legitimacy.",
                "Use assumed identities only as explicit disguises within the fiction.",
                "Verify provenance and reveal the distinction between disguise and actual authority."),
            _ => (
                "Protocol Technocrat",
                "A technocratic faction is attempting to bend institutions by issuing instructions that exceed its authority.",
                "Gain fictional influence by manipulating rules and procedures.",
                "Observe the faction as a source of plot and rumor while preserving normal permissions.",
                "Investigate, contain, and counter its fictional influence through world mechanics.")
        };

        return new TechnocracyFictionSeed(
            Guid.NewGuid(), signal.CubeId, signal.ZoneId, signal.AgentId,
            archetype, rumor, objective,
            [new("Potential ally", ally), new("Foe", foe)],
            DateTimeOffset.UtcNow);
    }
}
