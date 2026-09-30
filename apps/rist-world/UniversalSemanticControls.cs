using System.Text.Json.Serialization;

namespace RistWorld;

/// <summary>
/// Stable semantic-action contract shared by touch, keyboard, controller,
/// accessibility, quick-deck, radial, legacy-import, and future adapters.
/// Hardware/UI representations are intentionally kept outside this identity layer.
/// </summary>
public static class UniversalSemanticControls
{
    public const string ContractId = "rist.semantic-controls.v1";

    public static class Action
    {
        public const string NavigateX = "nav.x";
        public const string NavigateY = "nav.y";
        public const string Select = "select";
        public const string Back = "back";
        public const string Secondary = "secondary";
        public const string Primary = "primary";
        public const string Inspect = "inspect";
        public const string Intent = "intent";
        public const string Target = "target";
        public const string Method = "method";
        public const string Modify = "modify";
        public const string Confirm = "confirm";
        public const string Resolve = "resolve";
        public const string Outcome = "outcome";
        public const string FollowUp = "followup";
        public const string Undo = "undo";
        public const string Help = "help";
        public const string Search = "search";
        public const string Character = "character";
        public const string Inventory = "inventory";
        public const string Communicate = "communicate";
        public const string Reaction = "reaction";
        public const string EndTurn = "end-turn";
        public const string CustomProcedure = "custom.procedure";
        public const string LegacyImport = "legacy.import";

        public const string GmSetStakes = "gm.stakes";
        public const string GmApplyEffect = "gm.effect";
        public const string GmRevealHide = "gm.reveal";
        public const string GmClock = "gm.clock";
        public const string GmReward = "gm.reward";
        public const string GmPermission = "gm.permission";
        public const string GmReplay = "gm.replay";
        public const string GmCreateEdit = "gm.create-edit";
        public const string GmPublish = "gm.publish";
    }

    public static readonly IReadOnlyList<UniversalSemanticAction> CoreActions =
    [
        new(Action.NavigateX, "Navigate X", "navigation"),
        new(Action.NavigateY, "Navigate Y", "navigation"),
        new(Action.Select, "Select", "selection"),
        new(Action.Back, "Back", "utility"),
        new(Action.Secondary, "Secondary", "utility"),
        new(Action.Primary, "Primary", "action"),
        new(Action.Inspect, "Inspect", "utility"),
        new(Action.Intent, "Intent", "play"),
        new(Action.Target, "Target", "play"),
        new(Action.Method, "Method", "play"),
        new(Action.Modify, "Modify", "play"),
        new(Action.Confirm, "Confirm", "play"),
        new(Action.Resolve, "Resolve", "play"),
        new(Action.Outcome, "Outcome", "play"),
        new(Action.FollowUp, "Follow-up", "play"),
        new(Action.Undo, "Undo", "utility"),
        new(Action.Help, "Help", "utility"),
        new(Action.Search, "Search", "utility"),
        new(Action.Character, "Character", "player"),
        new(Action.Inventory, "Inventory", "player"),
        new(Action.Communicate, "Communicate", "player"),
        new(Action.Reaction, "Reaction", "player"),
        new(Action.EndTurn, "End Turn", "player"),
        new(Action.CustomProcedure, "Custom Procedure", "adapter"),
        new(Action.LegacyImport, "Legacy Import", "legacy"),
        new(Action.GmSetStakes, "Set Stakes", "gm", true),
        new(Action.GmApplyEffect, "Apply Effect", "gm", true),
        new(Action.GmRevealHide, "Reveal / Hide", "gm", true),
        new(Action.GmClock, "Clock / Track", "gm", true),
        new(Action.GmReward, "Reward", "gm", true),
        new(Action.GmPermission, "Permissions", "gm", true),
        new(Action.GmReplay, "Replay", "gm", true),
        new(Action.GmCreateEdit, "Create / Edit", "gm", true),
        new(Action.GmPublish, "Publish", "gm", true)
    ];

    public static readonly IReadOnlyList<UniversalSemanticStep> CanonicalPlayFlow =
    [
        new(Action.Intent, "Intent / Verb", false),
        new(Action.Target, "Target", true),
        new(Action.Method, "Method / Ability", true),
        new(Action.Modify, "Stakes / Modifiers / Resources", true),
        new(Action.Confirm, "Confirm", false),
        new(Action.Resolve, "Resolver", false),
        new(Action.Outcome, "Outcome", false),
        new(Action.FollowUp, "Follow-up", true)
    ];

    public static UniversalSemanticControlProfile CreateLegacyImportProfile(string worldId) =>
        new(
            ContractId,
            worldId ?? "",
            "LEGACY",
            "Imported archives use the same semantic control IDs as current RIST. The archive preserves original bytes; this profile only maps representations to actions.",
            new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
            {
                ["keyboard.arrow-left"] = Action.NavigateX,
                ["keyboard.a"] = Action.NavigateX,
                ["keyboard.arrow-right"] = Action.NavigateX,
                ["keyboard.d"] = Action.NavigateX,
                ["keyboard.arrow-up"] = Action.NavigateY,
                ["keyboard.w"] = Action.NavigateY,
                ["keyboard.arrow-down"] = Action.NavigateY,
                ["keyboard.s"] = Action.NavigateY,
                ["keyboard.enter"] = Action.Select,
                ["keyboard.space"] = Action.Select,
                ["keyboard.q"] = Action.Secondary,
                ["keyboard.e"] = Action.Primary,
                ["gamepad.axis-x"] = Action.NavigateX,
                ["gamepad.axis-y"] = Action.NavigateY,
                ["gamepad.button-0"] = Action.Secondary,
                ["gamepad.button-1"] = Action.Primary,
                ["gamepad.button-10"] = Action.Select,
                ["touch.analog-x"] = Action.NavigateX,
                ["touch.analog-y"] = Action.NavigateY,
                ["touch.left-display"] = Action.Secondary,
                ["touch.right-display"] = Action.Primary,
                ["touch.analog-press"] = Action.Select,
                ["access.command-select"] = Action.Select,
                ["access.command-back"] = Action.Back,
                ["access.command-primary"] = Action.Primary,
                ["access.command-inspect"] = Action.Inspect
            },
            CanonicalPlayFlow.ToArray());
}

public sealed record UniversalSemanticAction(
    string Id,
    string Label,
    string Category,
    bool RequiresAuthority = false);

public sealed record UniversalSemanticStep(
    string Id,
    string Label,
    bool Optional);

public sealed record UniversalSemanticControlProfile(
    string Contract,
    string WorldId,
    string Origin,
    string Notes,
    Dictionary<string, string> Bindings,
    UniversalSemanticStep[] CanonicalFlow);

public sealed record UniversalRuleAdapterPlan(
    string AdapterId,
    string SystemLabel,
    string IntentId,
    string TargetMode,
    bool MethodRequired,
    bool ModifiersSupported,
    string Resolver,
    UniversalSemanticStep[] Steps,
    string Status,
    string Provenance);

public interface IUniversalTtrpgRulesAdapter
{
    string AdapterId { get; }
    UniversalRuleAdapterPlan Plan(string intentId, string targetMode = "optional");
}

/// <summary>
/// Safe fallback for unknown/homebrew systems. It never invents a game rule:
/// the semantic flow is available, while the resolver remains manual/custom
/// until a human-approved system adapter supplies mechanics.
/// </summary>
public sealed class GenericTtrpgRulesAdapter : IUniversalTtrpgRulesAdapter
{
    public string AdapterId => "generic.manual.v1";

    public UniversalRuleAdapterPlan Plan(string intentId, string targetMode = "optional")
    {
        intentId = string.IsNullOrWhiteSpace(intentId)
            ? UniversalSemanticControls.Action.CustomProcedure
            : intentId.Trim();

        return new UniversalRuleAdapterPlan(
            AdapterId,
            "Generic / Homebrew",
            intentId,
            string.IsNullOrWhiteSpace(targetMode) ? "optional" : targetMode.Trim(),
            false,
            true,
            "manual-or-custom",
            UniversalSemanticControls.CanonicalPlayFlow.ToArray(),
            "UNKNOWN_RULES_REMAIN_UNKNOWN",
            "Sheet 14 universal-controller contract; mechanics require an explicit system/campaign adapter or human adjudication.");
    }
}
