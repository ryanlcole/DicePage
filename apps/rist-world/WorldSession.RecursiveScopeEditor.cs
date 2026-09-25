namespace RistWorld;

/// <summary>
/// Canonical authoring-scope model for the recursive Shaelvien map editors.
/// This intentionally sits beside legacy RecursionTiers while saved content
/// migrates. It does not rewrite legacy truth in place.
/// </summary>
public sealed partial class WorldSession
{
    public const string RecursiveScopeFormat = "RIST_RECURSIVE_SCOPE_V1";

    public static readonly IReadOnlyDictionary<string, RecursiveEditorScopeDefinition> RecursiveEditorScopes =
        new Dictionary<string, RecursiveEditorScopeDefinition>(StringComparer.OrdinalIgnoreCase)
        {
            ["WORLD"] = new("WORLD", 0, null),
            ["REGION"] = new("REGION", 15, "WORLD"),
            ["LOCAL"] = new("LOCAL", 30, "REGION"),
            ["INSTANCE"] = new("INSTANCE", 45, "LOCAL")
        };

    public static string NormalizeEditorScope(string? value)
    {
        var key = (value ?? "WORLD").Trim().ToUpperInvariant();
        return key switch
        {
            "ENCOUNTER" or "TACTICAL" => "INSTANCE",
            _ when RecursiveEditorScopes.ContainsKey(key) => key,
            _ => "WORLD"
        };
    }

    public static int EditorScopeViewDegrees(string? scope)
        => RecursiveEditorScopes[NormalizeEditorScope(scope)].ViewDegrees;

    public static RecursiveScopePlacement NewRecursiveScopePlacement(
        string assetId,
        string scopeKind,
        string scopeId,
        string parentScopeId = "",
        string parentAssetId = "")
    {
        var kind = NormalizeEditorScope(scopeKind);
        return new RecursiveScopePlacement(
            Format: RecursiveScopeFormat,
            AssetId: (assetId ?? "").Trim(),
            ScopeKind: kind,
            ScopeId: (scopeId ?? "").Trim(),
            ParentScopeId: (parentScopeId ?? "").Trim(),
            ParentAssetId: (parentAssetId ?? "").Trim(),
            X: 0,
            Y: 0,
            Tier: 1,
            Layer: 1,
            ViewDegrees: EditorScopeViewDegrees(kind));
    }

    public static int NormalizeScopeTier(int tier) => Math.Max(1, tier);
    public static int NormalizeScopeLayer(int layer) => Math.Max(1, layer);

    public static int NextVisualLayer(IEnumerable<RecursiveScopePlacement> placements, int tier)
    {
        var normalizedTier = NormalizeScopeTier(tier);
        var max = placements
            .Where(item => item.Tier == normalizedTier)
            .Select(item => item.Layer)
            .DefaultIfEmpty(0)
            .Max();
        return Math.Max(1, max + 1);
    }
}

public sealed record RecursiveEditorScopeDefinition(
    string Kind,
    int ViewDegrees,
    string? ParentKind);

public sealed record RecursiveScopePlacement(
    string Format,
    string AssetId,
    string ScopeKind,
    string ScopeId,
    string ParentScopeId,
    string ParentAssetId,
    double X,
    double Y,
    int Tier,
    int Layer,
    int ViewDegrees)
{
    public RecursiveScopePlacement Normalize()
    {
        var scope = WorldSession.NormalizeEditorScope(ScopeKind);
        return this with
        {
            Format = WorldSession.RecursiveScopeFormat,
            ScopeKind = scope,
            ScopeId = (ScopeId ?? "").Trim(),
            ParentScopeId = (ParentScopeId ?? "").Trim(),
            ParentAssetId = (ParentAssetId ?? "").Trim(),
            Tier = WorldSession.NormalizeScopeTier(Tier),
            Layer = WorldSession.NormalizeScopeLayer(Layer),
            ViewDegrees = WorldSession.EditorScopeViewDegrees(scope)
        };
    }
}
