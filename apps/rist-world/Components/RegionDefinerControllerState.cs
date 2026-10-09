namespace RistWorld.Components;

// The universal controller is a flowchart navigator.  The active node owns a
// bounded set of cases; analog X/Y changes the selected case and the two display
// buttons expose the actions for that case.  Shaelvien and local RIST reuse this
// interaction contract while authority/storage/rules remain outside controller
// identity.
public sealed record RegionDefinerControllerState(
    string Phase,
    int SelectedCount,
    string GridShape,
    int TierIndex,
    bool Pending,
    bool ExitRequested,
    string RegionId,
    string RegionName,
    int CaseIndex = 0,
    int CaseCount = 1,
    string CaseLabel = "REGION",
    string LeftLabel = "REGION TOOLS",
    string RightLabel = "SELECT");
