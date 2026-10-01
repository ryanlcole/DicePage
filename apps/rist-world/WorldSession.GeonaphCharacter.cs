namespace RistWorld;

public sealed partial class WorldSession
{
    public bool GeonaphTravelerPrepared { get; private set; }
    public bool GeonaphTravelerAlive { get; private set; } = true;

    /// <summary>
    /// Applies only the owner-approved Geonaph player backbone.
    /// Era-specific species, language, culture, rules, and statistics remain unknown
    /// until an authoritative campaign/system adapter can establish them.
    /// </summary>
    public void PrepareGeonaphTravelerCharacter()
    {
        EnsureCharacterSheetFields();

        if (!GeonaphTravelerPrepared)
        {
            if (string.IsNullOrWhiteSpace(CharacterName))
                CharacterName = "Traveler";

            if (string.IsNullOrWhiteSpace(CharacterBackground))
                CharacterBackground = "Future immortal · temporally conformed to the current historical zone";

            if (string.IsNullOrWhiteSpace(CharacterNotes))
                CharacterNotes =
                    "Identity continuity persists across the journey. Matter conforms to the destination era. " +
                    "Almost all future memory is lost. Survive and continue with the world until the original future becomes present.";

            if (string.IsNullOrWhiteSpace(CharacterConditions))
                CharacterConditions = "Temporal conformity complete · future-memory access unavailable";

            CharacterSpecies = "";
            CharacterAge = "";
            CharacterAlignment = "";
            GeonaphTravelerPrepared = true;
        }

        MixerOpen = true;
        CharacterEditMode = true;
        Notify();
    }

    public void EndGeonaphRunByDeath()
    {
        if (!GeonaphTravelerAlive) return;
        GeonaphTravelerAlive = false;
        CharacterConditions = string.IsNullOrWhiteSpace(CharacterConditions)
            ? "DECEASED · GEONAPH RUN ENDED"
            : CharacterConditions + " · DECEASED · GEONAPH RUN ENDED";
        Notify();
    }
}
