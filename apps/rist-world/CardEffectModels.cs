namespace RistWorld;

/// <summary>
/// Canonical behavior carried by a RIST card. Representation may change without
/// changing the authored mechanical behavior or runtime Effect Instance identity.
/// </summary>
public sealed class RistCardBehavior
{
    public int Version { get; set; } = 1;
    public RistActivationDefinition Activation { get; set; } = new();
    public List<RistRequirementDefinition> Requirements { get; set; } = [];
    public RistTargetingDefinition Targeting { get; set; } = new();
    public List<RistJoinedEffectDefinition> Effects { get; set; } = [];
    public RistEffectRepresentation Representation { get; set; } = new();
    public List<RistSpawnDefinition> Spawns { get; set; } = [];
    public RistPowerDefinition? Power { get; set; }
}

public sealed class RistActivationDefinition
{
    public string Mode { get; set; } = "ACTION"; // PASSIVE | ACTION | REACTION | TRIGGER | TOGGLE | EVENT
    public string Trigger { get; set; } = "";
    public string ResourceJoin { get; set; } = "";
    public double Cost { get; set; }
    public int Charges { get; set; }
    public int Cooldown { get; set; }
    public string CooldownUnit { get; set; } = "Rounds";
}

public sealed class RistRequirementDefinition
{
    public string RequirementId { get; set; } = Guid.NewGuid().ToString("N");
    public string Join { get; set; } = "";
    public string Comparator { get; set; } = "GTE";
    public double? Number { get; set; }
    public string Text { get; set; } = "";
}

public sealed class RistTargetingDefinition
{
    public string Selector { get; set; } = "SELF"; // SELF | SELECTED | MULTI | PARTY | POINT | OBJECT | AREA | PATH | ENCOUNTER
    public string Geometry { get; set; } = "NONE"; // NONE | POINT | CELL | LINE | CONE | DISC | SPHERE | CYLINDER | BOX | WALL | CHAIN | POLYGON | PATH | VOLUME
    public bool UnboundedRange { get; set; }
    public double Range { get; set; }
    public double Radius { get; set; }
    public double Height { get; set; }
    public double Width { get; set; }
    public double AngleDegrees { get; set; }
    public bool FollowSource { get; set; }
    public bool FollowTarget { get; set; }
    public bool UsesZ { get; set; } = true;
}

public sealed class RistJoinedEffectDefinition
{
    public string EffectDefinitionId { get; set; } = Guid.NewGuid().ToString("N");
    public string TargetJoin { get; set; } = "";
    public string TargetSlot { get; set; } = "CURRENT"; // BASE | CURRENT | MAX | VALUE
    public string Operation { get; set; } = "ADD"; // ADD | SUBTRACT | MULTIPLY | SET | CLAMP | GRANT | REMOVE | REPLACE | TOGGLE | MOVE | SPAWN | DESTROY
    public double Amount { get; set; }

    public string Resolution { get; set; } = "AUTO"; // AUTO | ROLL | OPPOSED | SAVE | THRESHOLD | GM
    public string RollFormula { get; set; } = "";
    public string DifficultyJoin { get; set; } = "";
    public double? Difficulty { get; set; }

    public int Duration { get; set; }
    public string DurationUnit { get; set; } = "Instant";
    public string Stacking { get; set; } = "ADD"; // ADD | INTENSITY | DURATION | REPLACE | HIGHEST | LOWEST | EXCLUSIVE
    public string Removal { get; set; } = "EXPIRE";
}

public sealed class RistEffectRepresentation
{
    public string Mode { get; set; } = "NONE"; // NONE | SPRITE | IMAGE | DRAW
    public string AssetId { get; set; } = "";
    public string SpriteChainId { get; set; } = "";
    public bool FlashAffectedBorders { get; set; } = true;
    public string BorderCue { get; set; } = "effect";
}

public sealed class RistSpawnDefinition
{
    public string SpawnDefinitionId { get; set; } = Guid.NewGuid().ToString("N");
    public string EntityType { get; set; } = "NPC"; // NPC | CHARACTER | CREATURE | OBJECT | TERRAIN | HAZARD | ITEM | EFFECT
    public string TemplateCardId { get; set; } = "";
    public string TokenAssetId { get; set; } = "";
    public string CharacterCardId { get; set; } = "";
    public int Quantity { get; set; } = 1;
    public bool Persistent { get; set; }
    public int Duration { get; set; }
    public string DurationUnit { get; set; } = "Rounds";
}

/// <summary>
/// Optional system-neutral description for a Power. "Magic" is a family, not a
/// separate runtime.
/// </summary>
public sealed class RistPowerDefinition
{
    public string Family { get; set; } = "Magic";
    public string Source { get; set; } = "";
    public string Discipline { get; set; } = "";
    public string ResourceJoin { get; set; } = "";
    public string CostName { get; set; } = "";
    public string UsageName { get; set; } = "";
}

/// <summary>
/// Runtime state created by resolving a card. It is deliberately separate from
/// the Card Definition / Card Instance so active effects survive template edits.
/// </summary>
public sealed class RistEffectInstance
{
    public string EffectId { get; set; } = Guid.NewGuid().ToString("N");
    public string CardId { get; set; } = "";
    public string CardInstanceId { get; set; } = "";
    public string SourceEntityId { get; set; } = "";
    public List<string> TargetEntityIds { get; set; } = [];
    public string WorldId { get; set; } = "";
    public string RegionId { get; set; } = "";
    public string LocalId { get; set; } = "";
    public string InstanceId { get; set; } = "";
    public string EncounterId { get; set; } = "";
    public RistHierarchicalAddress Address { get; set; } = new();
    public RistSpatialEffectGeometry Geometry { get; set; } = new();
    public string State { get; set; } = "READY"; // READY | PENDING | APPLIED | REJECTED | EXPIRED | REMOVED
    public DateTimeOffset CreatedAtUtc { get; set; } = DateTimeOffset.UtcNow;
    public DateTimeOffset? EndsAtUtc { get; set; }
    public List<RistResolvedEffectDelta> Deltas { get; set; } = [];
    public List<RistSpawnedEntityReference> SpawnedEntities { get; set; } = [];
}

public sealed class RistSpatialEffectGeometry
{
    public string Kind { get; set; } = "NONE";
    public double X { get; set; }
    public double Y { get; set; }
    public double Z { get; set; }
    public double EndX { get; set; }
    public double EndY { get; set; }
    public double EndZ { get; set; }
    public double Radius { get; set; }
    public double Height { get; set; }
    public double Width { get; set; }
    public double YawDegrees { get; set; }
    public double PitchDegrees { get; set; }
    public double AngleDegrees { get; set; }
    public List<RistSpatialPoint> Points { get; set; } = [];
}

public sealed record RistSpatialPoint(double X, double Y, double Z);

public sealed class RistResolvedEffectDelta
{
    public string TargetEntityId { get; set; } = "";
    public string TargetJoin { get; set; } = "";
    public string TargetSlot { get; set; } = "CURRENT";
    public string Operation { get; set; } = "ADD";
    public double RequestedAmount { get; set; }
    public double AppliedAmount { get; set; }
    public string Resolution { get; set; } = "AUTO";
    public string ResolutionState { get; set; } = "APPLIED";
}

public sealed class RistSpawnedEntityReference
{
    public string EntityId { get; set; } = Guid.NewGuid().ToString("N");
    public string EntityType { get; set; } = "NPC";
    public string TemplateCardId { get; set; } = "";
    public string TokenRepresentationId { get; set; } = "";
    public string CharacterCardRepresentationId { get; set; } = "";
}
