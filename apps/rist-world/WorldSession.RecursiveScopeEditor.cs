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

    readonly List<RecursiveScopePlacement> _recursiveScopePlacements = [];

    public IReadOnlyList<RecursiveScopePlacement> RecursiveScopePlacements => _recursiveScopePlacements;

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
        var identity = (assetId ?? "").Trim();
        return new RecursiveScopePlacement(
            Format: RecursiveScopeFormat,
            AssetId: identity,
            ScopeKind: kind,
            ScopeId: (scopeId ?? "").Trim(),
            ParentScopeId: (parentScopeId ?? "").Trim(),
            ParentAssetId: (parentAssetId ?? "").Trim(),
            X: 0,
            Y: 0,
            Tier: 1,
            Layer: 1,
            ViewDegrees: EditorScopeViewDegrees(kind),
            Opacity: 1,
            Visible: true,
            Locked: false,
            LinkedGroupId: "",
            PermissionResourceId: identity);
    }

    public static int NormalizeScopeTier(int tier) => Math.Max(1, tier);
    public static int NormalizeScopeLayer(int layer) => Math.Max(1, layer);

    public static int NextVisualLayer(IEnumerable<RecursiveScopePlacement> placements, int tier)
    {
        var normalizedTier = NormalizeScopeTier(tier);
        var max = placements
            .Where(item => item.Visible && item.Tier == normalizedTier)
            .Select(item => item.Layer)
            .DefaultIfEmpty(0)
            .Max();
        return Math.Max(1, max + 1);
    }

    public IReadOnlyList<RecursiveScopePlacement> RecursivePlacementsForScope(string scopeKind, string scopeId)
    {
        var kind = NormalizeEditorScope(scopeKind);
        var id = (scopeId ?? "").Trim();
        return _recursiveScopePlacements
            .Where(item =>
                string.Equals(item.ScopeKind, kind, StringComparison.OrdinalIgnoreCase) &&
                string.Equals(item.ScopeId, id, StringComparison.Ordinal))
            .OrderBy(item => item.Tier)
            .ThenBy(item => item.Layer)
            .ThenBy(item => item.AssetId, StringComparer.Ordinal)
            .ToList();
    }

    public RecursiveScopePlacement? FindRecursiveScopePlacement(string scopeKind, string scopeId, string assetId)
    {
        var kind = NormalizeEditorScope(scopeKind);
        var id = (scopeId ?? "").Trim();
        var asset = (assetId ?? "").Trim();
        return _recursiveScopePlacements.FirstOrDefault(item =>
            string.Equals(item.ScopeKind, kind, StringComparison.OrdinalIgnoreCase) &&
            string.Equals(item.ScopeId, id, StringComparison.Ordinal) &&
            string.Equals(item.AssetId, asset, StringComparison.Ordinal));
    }

    public void UpsertRecursiveScopePlacement(RecursiveScopePlacement placement)
    {
        if (UpsertRecursiveScopePlacementCore(placement))
            Notify();
    }

    public bool RemoveRecursiveScopePlacement(string scopeKind, string scopeId, string assetId)
    {
        var kind = NormalizeEditorScope(scopeKind);
        var id = (scopeId ?? "").Trim();
        var asset = (assetId ?? "").Trim();
        var removed = _recursiveScopePlacements.RemoveAll(item =>
            string.Equals(item.ScopeKind, kind, StringComparison.OrdinalIgnoreCase) &&
            string.Equals(item.ScopeId, id, StringComparison.Ordinal) &&
            string.Equals(item.AssetId, asset, StringComparison.Ordinal)) > 0;
        if (removed) Notify();
        return removed;
    }

    public bool SetRecursivePlacementPosition(string scopeKind, string scopeId, string assetId, double x, double y)
        => MutateRecursiveScopePlacement(scopeKind, scopeId, assetId, item => item with { X = x, Y = y });

    public bool SetRecursivePlacementTier(string scopeKind, string scopeId, string assetId, int tier)
        => MutateRecursiveScopePlacement(scopeKind, scopeId, assetId, item => item with { Tier = NormalizeScopeTier(tier) });

    public bool SetRecursivePlacementLayer(string scopeKind, string scopeId, string assetId, int layer)
        => MutateRecursiveScopePlacement(scopeKind, scopeId, assetId, item => item with { Layer = NormalizeScopeLayer(layer) });

    public bool SetRecursivePlacementOpacity(string scopeKind, string scopeId, string assetId, double opacity)
        => MutateRecursiveScopePlacement(scopeKind, scopeId, assetId, item => item with { Opacity = Math.Clamp(opacity, 0, 1) });

    public bool SetRecursivePlacementVisible(string scopeKind, string scopeId, string assetId, bool visible)
        => MutateRecursiveScopePlacement(scopeKind, scopeId, assetId, item => item with { Visible = visible });

    public bool SetRecursivePlacementLocked(string scopeKind, string scopeId, string assetId, bool locked)
        => MutateRecursiveScopePlacement(scopeKind, scopeId, assetId, item => item with { Locked = locked });

    public bool SetRecursivePlacementLinkedGroup(string scopeKind, string scopeId, string assetId, string linkedGroupId)
        => MutateRecursiveScopePlacement(scopeKind, scopeId, assetId, item => item with { LinkedGroupId = (linkedGroupId ?? "").Trim() });

    public bool SetRecursivePlacementPermissionResource(string scopeKind, string scopeId, string assetId, string permissionResourceId)
        => MutateRecursiveScopePlacement(scopeKind, scopeId, assetId, item => item with { PermissionResourceId = (permissionResourceId ?? "").Trim() });

    public List<RecursiveScopePlacement> ExportRecursiveScopePlacements()
        => _recursiveScopePlacements.Select(item => item.Normalize()).ToList();

    public void ImportRecursiveScopePlacements(
        IEnumerable<RecursiveScopePlacement>? placements,
        string? containerFormat = null)
    {
        _recursiveScopePlacements.Clear();

        if (!string.IsNullOrWhiteSpace(containerFormat) &&
            !string.Equals(containerFormat, RecursiveScopeFormat, StringComparison.Ordinal))
            return;

        foreach (var placement in placements ?? [])
        {
            if (!string.Equals(placement.Format, RecursiveScopeFormat, StringComparison.Ordinal))
                continue;
            UpsertRecursiveScopePlacementCore(placement);
        }
    }

    bool UpsertRecursiveScopePlacementCore(RecursiveScopePlacement placement)
    {
        var normalized = placement.Normalize();
        if (string.IsNullOrWhiteSpace(normalized.AssetId) || string.IsNullOrWhiteSpace(normalized.ScopeId))
            return false;

        var index = _recursiveScopePlacements.FindIndex(item =>
            string.Equals(item.ScopeKind, normalized.ScopeKind, StringComparison.OrdinalIgnoreCase) &&
            string.Equals(item.ScopeId, normalized.ScopeId, StringComparison.Ordinal) &&
            string.Equals(item.AssetId, normalized.AssetId, StringComparison.Ordinal));

        if (index >= 0)
        {
            if (_recursiveScopePlacements[index] == normalized)
                return false;
            _recursiveScopePlacements[index] = normalized;
            return true;
        }

        _recursiveScopePlacements.Add(normalized);
        return true;
    }

    bool MutateRecursiveScopePlacement(
        string scopeKind,
        string scopeId,
        string assetId,
        Func<RecursiveScopePlacement, RecursiveScopePlacement> mutate)
    {
        var kind = NormalizeEditorScope(scopeKind);
        var id = (scopeId ?? "").Trim();
        var asset = (assetId ?? "").Trim();
        var index = _recursiveScopePlacements.FindIndex(item =>
            string.Equals(item.ScopeKind, kind, StringComparison.OrdinalIgnoreCase) &&
            string.Equals(item.ScopeId, id, StringComparison.Ordinal) &&
            string.Equals(item.AssetId, asset, StringComparison.Ordinal));
        if (index < 0) return false;

        var current = _recursiveScopePlacements[index];
        var next = mutate(current).Normalize();

        // Field-specific setters above deliberately mutate only the requested
        // concept. Normalize enforces formatting/ranges, never cross-couples
        // layer, tier, coordinates, view, or authority.
        if (current == next) return false;
        _recursiveScopePlacements[index] = next;
        Notify();
        return true;
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
    int ViewDegrees,
    double Opacity = 1,
    bool Visible = true,
    bool Locked = false,
    string LinkedGroupId = "",
    string PermissionResourceId = "")
{
    public RecursiveScopePlacement Normalize()
    {
        var scope = WorldSession.NormalizeEditorScope(ScopeKind);
        var assetId = (AssetId ?? "").Trim();
        return this with
        {
            Format = WorldSession.RecursiveScopeFormat,
            AssetId = assetId,
            ScopeKind = scope,
            ScopeId = (ScopeId ?? "").Trim(),
            ParentScopeId = (ParentScopeId ?? "").Trim(),
            ParentAssetId = (ParentAssetId ?? "").Trim(),
            Tier = WorldSession.NormalizeScopeTier(Tier),
            Layer = WorldSession.NormalizeScopeLayer(Layer),
            ViewDegrees = WorldSession.EditorScopeViewDegrees(scope),
            Opacity = Math.Clamp(Opacity, 0, 1),
            LinkedGroupId = (LinkedGroupId ?? "").Trim(),
            PermissionResourceId = string.IsNullOrWhiteSpace(PermissionResourceId)
                ? assetId
                : PermissionResourceId.Trim()
        };
    }
}
