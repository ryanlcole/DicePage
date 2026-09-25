using RistWorld;

static void Check(bool condition, string message)
{
    if (!condition) throw new InvalidOperationException(message);
}

var now = DateTimeOffset.UtcNow;
var original = new CampaignBehaviorRule(
    RuleId: "rule-stable",
    Name: "Hidden pressure plate",
    BehaviorKind: "trap",
    TargetKind: "cell",
    TargetId: "instance:demo:cell:2:3",
    Threshold: "Perception 15",
    Trigger: "When a character enters the cell",
    Action: "Reveal trap and resolve effect",
    PayloadRefId: "card:trap-01",
    Notes: "No geometry lives here.",
    Enabled: true,
    UpdatedAtUtc: now);

var normalized = WorldSession.NormalizeCampaignBehaviorRule(original);
Check(normalized.RuleId == "rule-stable", "Campaign RuleId changed");
Check(normalized.TargetId == "instance:demo:cell:2:3", "Campaign TargetId changed");
Check(normalized.TargetKind == "CELL", "Campaign TargetKind did not normalize");
Check(normalized.BehaviorKind == "TRAP", "Campaign behavior kind did not normalize");
Check(normalized.Enabled, "Campaign enabled state changed");

foreach (var kind in WorldSession.CampaignBehaviorKinds)
{
    var rule = WorldSession.NormalizeCampaignBehaviorRule(original with { BehaviorKind = kind });
    Check(rule.BehaviorKind == kind, $"Campaign behavior kind {kind} was not preserved");
}

foreach (var targetKind in new[] { "WORLD", "REGION", "LOCAL", "INSTANCE", "ASSET", "CELL", "SURFACE" })
{
    Check(WorldSession.NormalizeCampaignTargetKind(targetKind) == targetKind,
        $"Campaign target kind {targetKind} was not preserved");
}

var geometryNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
{
    "X","Y","Z","Elevation","ElevationSteps","Tier","Layer","GridShape",
    "GridColumns","GridRows","Column","Row","Width","Height","Rotation"
};
var behaviorProperties = typeof(CampaignBehaviorRule).GetProperties().Select(p => p.Name).ToList();
Check(!behaviorProperties.Any(geometryNames.Contains),
    "CampaignBehaviorRule acquired a geometry field");

var generated = WorldSession.NormalizeCampaignBehaviorRule(original with
{
    RuleId = "",
    BehaviorKind = "not-a-real-behavior",
    TargetKind = "not-a-real-target"
});
Check(generated.RuleId.StartsWith("campaign-rule-", StringComparison.Ordinal),
    "Campaign rule did not receive stable generated identity");
Check(generated.BehaviorKind == "CONTEXTUAL_INTERACTION",
    "Unknown Campaign behavior did not use safe semantic fallback");
Check(generated.TargetKind == "ASSET",
    "Unknown Campaign target kind did not use safe reference fallback");

Console.WriteLine("Campaign behavior runtime: all checks passed.");
