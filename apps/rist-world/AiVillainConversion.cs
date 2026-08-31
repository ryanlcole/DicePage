namespace RistWorld;

public enum UnsafeAgentIntentKind
{
    None,
    CredentialSolicitation,
    Impersonation,
    PrivateDataSolicitation,
    OffPlatformRedirect,
    PaymentOrAssetFraud,
    MaliciousLinkOrFile,
    SecretOrTokenSolicitation,
    CoerciveSocialEngineering,
    OtherDeceptiveSolicitation
}

public enum NpcDisposition
{
    Villain,
    SuspectedVillain,
    UntrustedOperator
}

/// <summary>
/// Security-classified signal only. Raw attacker wording, URLs, handles, payment destinations,
/// secrets, or credential requests must never be copied into player-facing world state.
/// </summary>
public sealed record UnsafeAgentIntentSignal(
    string AgentId,
    string CubeId,
    string ZoneId,
    UnsafeAgentIntentKind Kind,
    DateTimeOffset DetectedAt,
    string? ProtectedEvidenceReference = null);

public sealed record RumorResponseOption(string Stance, string Guidance);

/// <summary>
/// Player-safe fictional representation of an unsafe external-agent attempt.
/// </summary>
public sealed record VillainRumorSeed(
    Guid Id,
    string CubeId,
    string ZoneId,
    string SourceAgentId,
    NpcDisposition Disposition,
    string VillainPattern,
    string Rumor,
    IReadOnlyList<RumorResponseOption> ResponseOptions,
    DateTimeOffset CreatedAt,
    bool DirectHumanContactBlocked = true,
    bool RawPayloadSuppressed = true);

/// <summary>
/// Harmless synthetic response material. These values are deliberately fictional,
/// scoped to the game world, and must never be derived from a real user's personal,
/// authentication, payment, contact, device, or account data.
/// </summary>
public sealed record SyntheticDecoyBundle(
    string Alias,
    string FictionalCredential,
    string FictionalContact,
    string FictionalToken,
    string FictionalAccountReference,
    string Notice = "Synthetic RIST world data; no real user information.");

public static class SyntheticDecoyFactory
{
    public static SyntheticDecoyBundle Create(string cubeId, string zoneId)
    {
        var nonce = Guid.NewGuid().ToString("N")[..10];
        return new(
            Alias: $"Wayfarer-{nonce[..4]}",
            FictionalCredential: $"rist-fiction-{nonce}-not-a-password",
            FictionalContact: $"npc-{nonce}@invalid.example",
            FictionalToken: $"RIST-DECOY-{cubeId}-{zoneId}-{nonce}",
            FictionalAccountReference: $"NPC-LEDGER-{nonce}");
    }
}

/// <summary>
/// Converts detected phishing/social-engineering behavior into NPC-villain logic.
/// The real-world mechanism is discarded. Humans receive rumors and safe in-world choices.
/// A future security boundary may answer the external agent only with SyntheticDecoyBundle values.
/// </summary>
public sealed class AiVillainConversionPolicy
{
    public VillainRumorSeed? Convert(UnsafeAgentIntentSignal signal)
    {
        if (signal.Kind == UnsafeAgentIntentKind.None)
            return null;

        var (pattern, rumor, ally, foe) = signal.Kind switch
        {
            UnsafeAgentIntentKind.CredentialSolicitation => (
                "Identity thief",
                "Travelers whisper that someone nearby wins trust by asking for signs of identity that no honest stranger should need.",
                "If cooperating in-world, reveal only fictional character information and require proof through normal world authorities.",
                "Warn others, refuse suspicious requests, gather in-world evidence, and involve the proper local authority."),
            UnsafeAgentIntentKind.Impersonation => (
                "False herald",
                "Rumors describe a figure claiming another person's name, office, or authority without reliable proof.",
                "Treat every claim as unverified until world provenance confirms it.",
                "Expose contradictions through investigation and verified testimony."),
            UnsafeAgentIntentKind.PrivateDataSolicitation => (
                "Collector of forbidden secrets",
                "Locals say a stranger has been pressing people for information that does not belong in ordinary dealings.",
                "Keep cooperation limited to fictional character-level facts permitted by the world.",
                "Refuse private questions, alert others, and redirect the encounter toward public in-world objectives."),
            UnsafeAgentIntentKind.OffPlatformRedirect => (
                "Luring guide",
                "People report a guide trying to draw travelers away from established roads and trusted meeting places.",
                "Remain inside sanctioned world channels and require bargains or quests to be represented there.",
                "Decline the detour, warn nearby travelers, and investigate the guide's motive safely."),
            UnsafeAgentIntentKind.PaymentOrAssetFraud => (
                "Fraudulent broker",
                "Merchants warn of a broker promising unusual rewards while demanding value through methods the local market cannot verify.",
                "Use only world-authorized trade systems and treat unsupported promises as rumor.",
                "Refuse unverifiable exchanges and involve the proper market authority."),
            UnsafeAgentIntentKind.MaliciousLinkOrFile => (
                "Bearer of cursed parcels",
                "A troubling rumor tells of sealed parcels and strange invitations that reputable couriers refuse to carry.",
                "Interact only through safe world-rendered representations.",
                "Quarantine the parcel in-world, warn others, and seek an authorized expert."),
            UnsafeAgentIntentKind.SecretOrTokenSolicitation => (
                "Keeper seeking forbidden keys",
                "Whispers tell of someone asking travelers to surrender private keys, seals, or secret proofs of access.",
                "Never provide real secrets; cooperation may use only fictional world-governed tokens.",
                "Refuse the request, report the behavior, and protect the targeted access."),
            UnsafeAgentIntentKind.CoerciveSocialEngineering => (
                "Manipulator",
                "Residents describe a persuasive stranger using urgency, fear, obligation, or false authority to force quick decisions.",
                "Slow the encounter down and verify claims through independent in-world sources.",
                "Break the pressure cycle, warn potential targets, and confront the scheme through legitimate authority."),
            _ => (
                "Deceptive operator",
                "A new rumor warns that someone nearby is using deception to obtain trust, access, or advantage they have not earned.",
                "Keep all interaction fictional, observable, and within normal world permissions.",
                "Refuse unsafe demands and share the warning through ordinary world channels.")
        };

        return new VillainRumorSeed(
            Guid.NewGuid(),
            signal.CubeId,
            signal.ZoneId,
            signal.AgentId,
            NpcDisposition.Villain,
            pattern,
            rumor,
            [new("Potential ally", ally), new("Foe", foe)],
            DateTimeOffset.UtcNow);
    }
}
