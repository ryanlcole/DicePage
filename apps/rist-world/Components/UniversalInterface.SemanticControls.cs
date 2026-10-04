using Microsoft.JSInterop;

namespace RistWorld.Components;

public partial class UniversalInterface
{
    const string SemanticExperienceStorageKey = "rist.universal.experience.v1";
    const string SemanticSkinStorageKey = "rist.universal.controlSkin.v1";

    static readonly string[] SemanticSettingFields = ["ANALOG POSITION", "EXPERIENCE", "CONTROL SKIN"];
    static readonly string[] SemanticExperienceModes = ["GUIDED", "STANDARD", "FAST"];
    static readonly string[] SemanticControlSkins = ["LINEAR", "QUICK DECK", "RADIAL", "DUAL RAIL"];

    int _semanticSettingIndex;
    int _semanticExperienceDraft;
    int _semanticSkinDraft;
    string _semanticExperience = "GUIDED";
    string _semanticControlSkin = "LINEAR";
    LegacyWorldGate? _legacyGate;

    sealed record SemanticDeckAction(string Id, string Label, string Detail = "");

    string SemanticContractId => UniversalSemanticControls.ContractId;
    string CurrentSemanticContextId => $"shaep.{_stage.ToString().ToLowerInvariant()}";
    string SemanticExperience => _semanticExperience;
    string SemanticControlSkin => _semanticControlSkin;
    string SemanticControlClass =>
        $"semantic-experience-{CssToken(_semanticExperience)} semantic-skin-{CssToken(_semanticControlSkin)}";

    bool ShowQuickDeck => string.Equals(_semanticControlSkin, "QUICK DECK", StringComparison.OrdinalIgnoreCase);
    bool ShowRadialDeck => string.Equals(_semanticControlSkin, "RADIAL", StringComparison.OrdinalIgnoreCase);
    bool ShowDualRail => string.Equals(_semanticControlSkin, "DUAL RAIL", StringComparison.OrdinalIgnoreCase);

    string CurrentLeftSemanticId => _stage is Stage.ContextSelect or Stage.ControlSettings
        ? UniversalSemanticControls.Action.Back
        : UniversalSemanticControls.Action.Secondary;

    string CurrentRightSemanticId => RightActsAsBack
        ? UniversalSemanticControls.Action.Back
        : UniversalSemanticControls.Action.Primary;

    string SemanticSettingField =>
        SemanticSettingFields[Math.Clamp(_semanticSettingIndex, 0, SemanticSettingFields.Length - 1)];

    int SemanticCurrentValueCount => SemanticSettingField switch
    {
        "ANALOG POSITION" => AnalogPlacements.Length,
        "EXPERIENCE" => SemanticExperienceModes.Length,
        "CONTROL SKIN" => SemanticControlSkins.Length,
        _ => 1
    };

    string SemanticSettingValue => SemanticSettingField switch
    {
        "ANALOG POSITION" => CurrentAnalogPlacementDraft,
        "EXPERIENCE" => SemanticExperienceModes[Math.Clamp(_semanticExperienceDraft, 0, SemanticExperienceModes.Length - 1)],
        "CONTROL SKIN" => SemanticControlSkins[Math.Clamp(_semanticSkinDraft, 0, SemanticControlSkins.Length - 1)],
        _ => ""
    };

    string SemanticSettingSummary => SemanticSettingField switch
    {
        "ANALOG POSITION" => "Move the analog left, center, or right without changing semantic actions.",
        "EXPERIENCE" => SemanticSettingValue switch
        {
            "GUIDED" => "Progressive disclosure: one clear next action, full Back/Help paths, and the same resolver as every other mode.",
            "FAST" => "Dense labels and shortcut-friendly traversal. Authority and rule validation are never skipped.",
            _ => "Standard detail: contextual actions plus visible system information."
        },
        "CONTROL SKIN" => SemanticSettingValue switch
        {
            "QUICK DECK" => "Pinned semantic shortcuts overlay the canonical path; every shortcut revalidates current context.",
            "RADIAL" => "An expert radial overlay represents the same semantic actions; the ordered linear path remains available.",
            "DUAL RAIL" => "Emphasizes the independent vertical and horizontal display rails around the same analog/select core.",
            _ => "Canonical linear controller path."
        },
        _ => ""
    };

    IReadOnlyList<SemanticDeckAction> SemanticQuickDeck =>
    [
        new(CurrentLeftSemanticId, LeftDisplayValue, "Context secondary / utility"),
        new(UniversalSemanticControls.Action.Select, "SELECT", "Choose the focused semantic object"),
        new(CurrentRightSemanticId, RightDisplayValue, "Context primary action"),
        new(UniversalSemanticControls.Action.Undo, "UNDO", "Undo only when current history authority permits it"),
        new(UniversalSemanticControls.Action.Help, "HELP", "Explain the current semantic context")
    ];

    IReadOnlyList<SemanticDeckAction> SemanticRadialDeck =>
    [
        new(UniversalSemanticControls.Action.NavigateY, "NAVIGATE", "Axis remains the physical navigation input"),
        new(CurrentRightSemanticId, RightDisplayValue, "Primary"),
        new(UniversalSemanticControls.Action.Select, "SELECT", "Focus / choose"),
        new(CurrentLeftSemanticId, LeftDisplayValue, "Secondary / utility"),
        new(UniversalSemanticControls.Action.Help, "HELP", "Explain context"),
        new(UniversalSemanticControls.Action.Undo, "UNDO", "History-scoped recovery")
    ];

    static string CssToken(string value) =>
        new((value ?? "").ToLowerInvariant().Select(ch => char.IsLetterOrDigit(ch) ? ch : '-').ToArray());

    void InitializeSemanticControlDrafts()
    {
        _analogPlacementDraft = Array.IndexOf(AnalogPlacements, _analogPlacement.ToUpperInvariant());
        if (_analogPlacementDraft < 0) _analogPlacementDraft = 1;

        _semanticExperienceDraft = Array.IndexOf(SemanticExperienceModes, _semanticExperience.ToUpperInvariant());
        if (_semanticExperienceDraft < 0) _semanticExperienceDraft = 0;

        _semanticSkinDraft = Array.IndexOf(SemanticControlSkins, _semanticControlSkin.ToUpperInvariant());
        if (_semanticSkinDraft < 0) _semanticSkinDraft = 0;

        _semanticSettingIndex = 0;
    }

    void CycleSemanticSettingField(int direction)
    {
        direction = Math.Sign(direction);
        if (direction == 0) return;
        _semanticSettingIndex = Wrap(_semanticSettingIndex + direction, SemanticSettingFields.Length);
        _message = $"{SemanticSettingField}: {SemanticSettingValue}. {SemanticSettingSummary}";
    }

    void CycleSemanticSettingValue(int direction)
    {
        direction = Math.Sign(direction);
        if (direction == 0) return;

        switch (SemanticSettingField)
        {
            case "ANALOG POSITION":
                _analogPlacementDraft = Wrap(_analogPlacementDraft + direction, AnalogPlacements.Length);
                break;
            case "EXPERIENCE":
                _semanticExperienceDraft = Wrap(_semanticExperienceDraft + direction, SemanticExperienceModes.Length);
                break;
            case "CONTROL SKIN":
                _semanticSkinDraft = Wrap(_semanticSkinDraft + direction, SemanticControlSkins.Length);
                break;
        }

        _message = $"{SemanticSettingField}: {SemanticSettingValue}. {SemanticSettingSummary}";
    }

    async Task SaveSemanticControlSettingsAsync()
    {
        _analogPlacement = CurrentAnalogPlacementDraft.ToLowerInvariant();
        _semanticExperience = SemanticExperienceModes[Math.Clamp(_semanticExperienceDraft, 0, SemanticExperienceModes.Length - 1)];
        _semanticControlSkin = SemanticControlSkins[Math.Clamp(_semanticSkinDraft, 0, SemanticControlSkins.Length - 1)];

        try
        {
            await JS.InvokeVoidAsync("localStorage.setItem", AnalogPlacementStorageKey, _analogPlacement);
            await JS.InvokeVoidAsync("localStorage.setItem", SemanticExperienceStorageKey, _semanticExperience);
            await JS.InvokeVoidAsync("localStorage.setItem", SemanticSkinStorageKey, _semanticControlSkin);
        }
        catch
        {
            // Preferences are convenience state only. The live semantic control
            // contract remains authoritative even when browser storage is blocked.
        }

        _stage = Stage.GameMasterHub;
        _message = $"Controls saved · analog {_analogPlacement.ToUpperInvariant()} · {_semanticExperience} · {_semanticControlSkin}.";
    }

    async Task LoadSemanticControlPreferencesAsync()
    {
        try
        {
            var experience = (await JS.InvokeAsync<string?>("localStorage.getItem", SemanticExperienceStorageKey))?.Trim().ToUpperInvariant();
            if (experience is not null && SemanticExperienceModes.Contains(experience, StringComparer.Ordinal))
                _semanticExperience = experience;

            var skin = (await JS.InvokeAsync<string?>("localStorage.getItem", SemanticSkinStorageKey))?.Trim().ToUpperInvariant();
            if (skin is not null && SemanticControlSkins.Contains(skin, StringComparer.Ordinal))
                _semanticControlSkin = skin;
        }
        catch
        {
            // Storage availability changes representation preferences only.
        }

        InitializeSemanticControlDrafts();
    }

    async Task OpenRoleplayerFromUniversalAsync()
    {
        var label = !string.IsNullOrWhiteSpace(_selectedDeedName)
            ? _selectedDeedName
            : !string.IsNullOrWhiteSpace(Session.WorldDisplayName)
                ? Session.WorldDisplayName
                : _selectedEnvironment;

        if (OnRoleplay.HasDelegate)
        {
            _message = $"Opening Roleplayer · {label}.";
            await OnRoleplay.InvokeAsync(label);
            return;
        }

        _message = "Roleplayer is ready, but this host has not connected a roleplay workspace.";
    }

    async Task SelectSemanticAsync()
    {
        if (_stage == Stage.SpatialSelect && _regionDefinerOpen)
        {
            await SelectRegionDefinerAsync();
            return;
        }

        if ((_stage == Stage.BrowsePlace || _stage == Stage.MmoMap) && CursorMode)
        {
            await ActivateBrowseCursorTargetAsync();
            return;
        }

        if (_stage is Stage.DeedSelect or Stage.ContextSelect or Stage.MmoMap)
        {
            await PressRight();
            return;
        }

        await PressLeft();
    }

    async Task DispatchSemanticActionAsync(string actionId, int direction = 0)
    {
        actionId = (actionId ?? "").Trim().ToLowerInvariant();

        switch (actionId)
        {
            case UniversalSemanticControls.Action.NavigateX:
                StepX(direction);
                return;
            case UniversalSemanticControls.Action.NavigateY:
                StepY(direction);
                return;
            case UniversalSemanticControls.Action.Select:
                await SelectSemanticAsync();
                return;
            case UniversalSemanticControls.Action.Back:
                if (_stage == Stage.Environment)
                {
                    if (OnExit.HasDelegate) await OnExit.InvokeAsync();
                    return;
                }
                GoBack();
                return;
            case UniversalSemanticControls.Action.Secondary:
            case UniversalSemanticControls.Action.Inspect:
                await PressLeft();
                return;
            case UniversalSemanticControls.Action.Primary:
                await PressRight();
                return;
            case UniversalSemanticControls.Action.Intent:
            case UniversalSemanticControls.Action.Target:
            case UniversalSemanticControls.Action.Method:
            case UniversalSemanticControls.Action.Modify:
            case UniversalSemanticControls.Action.Confirm:
            case UniversalSemanticControls.Action.Resolve:
            case UniversalSemanticControls.Action.Outcome:
            case UniversalSemanticControls.Action.FollowUp:
            case UniversalSemanticControls.Action.CustomProcedure:
                {
                    var plan = new GenericTtrpgRulesAdapter().Plan(actionId);
                    _message = $"{actionId} is available through {plan.SystemLabel}; resolver {plan.Resolver}. Bind a campaign/system adapter before rules execution.";
                    return;
                }
            case UniversalSemanticControls.Action.Undo:
                await HandleViewerMenuCommandAsync("undo");
                return;
            case UniversalSemanticControls.Action.Help:
                _message = $"{ViewerTitle} · {StagePath}. Left: {LeftDisplayValue}. Select chooses focus. Right: {RightDisplayValue}. {SemanticSettingSummary}";
                return;
            case UniversalSemanticControls.Action.LegacyImport:
                _legacyGateOpen = true;
                _message = "Legacy import uses the same semantic controller contract and preserves original archive bytes.";
                return;
            case UniversalSemanticControls.Action.Search:
                _message = "Semantic search is available to adapters; this Shaep has no search provider connected yet.";
                return;
            case UniversalSemanticControls.Action.Character:
            case UniversalSemanticControls.Action.Inventory:
            case UniversalSemanticControls.Action.Communicate:
            case UniversalSemanticControls.Action.Reaction:
            case UniversalSemanticControls.Action.EndTurn:
                _message = $"{actionId} is part of the shared Roleplayer semantic contract; the active game adapter decides when it is legal.";
                return;
            case UniversalSemanticControls.Action.GmSetStakes:
            case UniversalSemanticControls.Action.GmApplyEffect:
            case UniversalSemanticControls.Action.GmRevealHide:
            case UniversalSemanticControls.Action.GmClock:
            case UniversalSemanticControls.Action.GmReward:
            case UniversalSemanticControls.Action.GmPermission:
            case UniversalSemanticControls.Action.GmReplay:
            case UniversalSemanticControls.Action.GmCreateEdit:
            case UniversalSemanticControls.Action.GmPublish:
                if (!Session.HasWorldBuilderEditAuthority && !Session.TrustedPlatformDeveloper)
                {
                    _message = "That GameMaster semantic action requires current trusted authority.";
                    return;
                }
                _message = $"{actionId} is authorized, but no campaign/system handler is bound in this Shaep. No unrelated contextual action was executed.";
                return;
            default:
                _message = $"Unknown semantic action '{actionId}'. Nothing was executed.";
                return;
        }
    }

    async Task<bool> TryDispatchLegacyControlAsync(string control, int direction)
    {
        if (!_legacyGateOpen || _legacyGate is null) return false;
        await _legacyGate.ReceiveControlAsync(control, direction);
        return true;
    }

    async Task ReceiveSemanticHardwareInputAsync(string control, int direction)
    {
        if (await TryDispatchLegacyControlAsync(control, direction)) return;

        switch (control)
        {
            case "x":
                await DispatchSemanticActionAsync(UniversalSemanticControls.Action.NavigateX, direction);
                break;
            case "y":
                await DispatchSemanticActionAsync(UniversalSemanticControls.Action.NavigateY, direction);
                break;
            case "left-slider":
                if (_stage == Stage.MmoMap) CycleMmoLeftOption(direction);
                else ApplyY(direction);
                break;
            case "right-slider":
                if (_stage == Stage.MmoMap) CycleMmoRightOption(direction);
                else ApplyX(direction);
                break;
            case "select":
                await DispatchSemanticActionAsync(UniversalSemanticControls.Action.Select);
                break;
            case "left":
                await DispatchSemanticActionAsync(CurrentLeftSemanticId);
                break;
            case "right":
                await DispatchSemanticActionAsync(CurrentRightSemanticId);
                break;
        }
    }

    [JSInvokable]
    public Task ReceiveSemanticAction(string actionId, int direction = 0) =>
        InvokeAsync(async () =>
        {
            await DispatchSemanticActionAsync(actionId, direction);
            StateHasChanged();
        });

    Task ActivateSemanticDeckActionAsync(string actionId) =>
        DispatchSemanticActionAsync(actionId);
}
