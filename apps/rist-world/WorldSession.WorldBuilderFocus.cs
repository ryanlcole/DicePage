namespace RistWorld;

/// <summary>
/// Semantic focus/drill authority for World Builder. This is viewer containment state,
/// not a second coordinate system: Tier/Layer/SceneZ remain the spatial authority.
/// </summary>
public sealed partial class WorldSession
{
    const string DefaultWorldBuilderStratum = "surface";

    static readonly WorldBuilderFocusOption[] WorldBuilderStrata =
    [
        new("universe", "Universe", "Parallax"),
        new("sky", "Sky", "Parallax"),
        new("weather", "Weather", "Parallax"),
        new("surface", "Surface", "Parallax"),
        new("subterranean", "Subterranean", "Parallax"),
        new("depths", "Depths", "Parallax"),
        new("core", "Core", "Parallax")
    ];

    static readonly WorldBuilderFocusOption[] SurfaceCategories =
    [
        new("mountain", "Mountain", "Category"),
        new("volcano", "Volcano", "Category"),
        new("hills", "Hills", "Category"),
        new("plains", "Plains", "Category")
    ];

    readonly List<WorldBuilderFocusSegment> _worldBuilderFocusPath = [];
    string _worldBuilderFocusSelectedKey = DefaultWorldBuilderStratum;

    public WorldBuilderFocusState GetWorldBuilderFocusState()
    {
        var options = GetWorldBuilderFocusOptions();
        var selected = options.FirstOrDefault(x => string.Equals(x.Key, _worldBuilderFocusSelectedKey, StringComparison.Ordinal))
            ?? options.FirstOrDefault();

        if (selected is not null && !string.Equals(selected.Key, _worldBuilderFocusSelectedKey, StringComparison.Ordinal))
            _worldBuilderFocusSelectedKey = selected.Key;

        var nextLevel = FocusLevelForDepth(_worldBuilderFocusPath.Count);
        return new WorldBuilderFocusState(
            SelectedKey: selected?.Key ?? "",
            SelectedLabel: selected?.Label ?? nextLevel,
            NextLevel: nextLevel,
            CanLock: selected is not null,
            CanUnlock: _worldBuilderFocusPath.Count > 0,
            BattleInstanceVisible: _worldBuilderFocusPath.Any(x => string.Equals(x.Level, "Battle Instance", StringComparison.Ordinal)),
            SceneZ: SceneZ,
            TierIndex: TierIndex,
            LayerOffset: LayerOffset,
            LockedPath: _worldBuilderFocusPath.ToList(),
            Options: options);
    }

    public WorldBuilderFocusState SelectWorldBuilderFocusOption(string? key)
    {
        var options = GetWorldBuilderFocusOptions();
        var match = options.FirstOrDefault(x => string.Equals(x.Key, key?.Trim(), StringComparison.Ordinal));
        if (match is not null)
        {
            _worldBuilderFocusSelectedKey = match.Key;
            Notify();
        }
        return GetWorldBuilderFocusState();
    }

    public WorldBuilderFocusState LockWorldBuilderFocus()
    {
        var state = GetWorldBuilderFocusState();
        var selected = state.Options.FirstOrDefault(x => string.Equals(x.Key, state.SelectedKey, StringComparison.Ordinal));
        if (selected is null) return state;

        _worldBuilderFocusPath.Add(new WorldBuilderFocusSegment(selected.Level, selected.Key, selected.Label));
        if (string.Equals(selected.Level, "Region", StringComparison.Ordinal))
            SetActiveRegion(selected.Key);

        _worldBuilderFocusSelectedKey = GetWorldBuilderFocusOptions().FirstOrDefault()?.Key ?? "";
        Notify();
        return GetWorldBuilderFocusState();
    }

    public WorldBuilderFocusState UnlockWorldBuilderFocus()
    {
        if (_worldBuilderFocusPath.Count == 0) return GetWorldBuilderFocusState();

        var removed = _worldBuilderFocusPath[^1];
        _worldBuilderFocusPath.RemoveAt(_worldBuilderFocusPath.Count - 1);
        var options = GetWorldBuilderFocusOptions();
        _worldBuilderFocusSelectedKey = options.Any(x => string.Equals(x.Key, removed.Key, StringComparison.Ordinal))
            ? removed.Key
            : options.FirstOrDefault()?.Key ?? "";
        Notify();
        return GetWorldBuilderFocusState();
    }

    public WorldBuilderFocusState ResetWorldBuilderFocus()
    {
        _worldBuilderFocusPath.Clear();
        _worldBuilderFocusSelectedKey = DefaultWorldBuilderStratum;
        Notify();
        return GetWorldBuilderFocusState();
    }

    IReadOnlyList<WorldBuilderFocusOption> GetWorldBuilderFocusOptions()
    {
        return _worldBuilderFocusPath.Count switch
        {
            0 => WorldBuilderStrata,
            1 => CategoryOptionsFor(_worldBuilderFocusPath[0]),
            2 => _regions
                .OrderBy(x => x.Name, StringComparer.OrdinalIgnoreCase)
                .Select(x => new WorldBuilderFocusOption(x.RegionId, x.Name, "Region"))
                .ToList(),
            3 => [new($"local:{_worldBuilderFocusPath[2].Key}", "Local", "Local")],
            4 => [new($"landmark:{_worldBuilderFocusPath[2].Key}", "Landmark", "Landmark")],
            5 =>
            [
                new($"npc:{_worldBuilderFocusPath[2].Key}", "NPC", "Entity"),
                new($"object:{_worldBuilderFocusPath[2].Key}", "Object", "Entity")
            ],
            6 => [new($"battle:{_worldBuilderFocusPath[5].Key}", "Battle Instance", "Battle Instance")],
            _ => []
        };
    }

    static IReadOnlyList<WorldBuilderFocusOption> CategoryOptionsFor(WorldBuilderFocusSegment stratum)
    {
        if (string.Equals(stratum.Key, DefaultWorldBuilderStratum, StringComparison.Ordinal))
            return SurfaceCategories;

        // Other strata retain an explicit semantic scope without inventing an ontology.
        // Their actual height/depth remains the canonical SceneZ/Tier/Layer address.
        return [new($"{stratum.Key}:all", $"All {stratum.Label}", "Category")];
    }

    static string FocusLevelForDepth(int depth) => depth switch
    {
        0 => "Parallax",
        1 => "Category",
        2 => "Region",
        3 => "Local",
        4 => "Landmark",
        5 => "Entity",
        6 => "Battle Instance",
        _ => "Battle Instance"
    };
}

public sealed record WorldBuilderFocusOption(string Key, string Label, string Level);
public sealed record WorldBuilderFocusSegment(string Level, string Key, string Label);
public sealed record WorldBuilderFocusState(
    string SelectedKey,
    string SelectedLabel,
    string NextLevel,
    bool CanLock,
    bool CanUnlock,
    bool BattleInstanceVisible,
    int SceneZ,
    int TierIndex,
    int LayerOffset,
    IReadOnlyList<WorldBuilderFocusSegment> LockedPath,
    IReadOnlyList<WorldBuilderFocusOption> Options);
