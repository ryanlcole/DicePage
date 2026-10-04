namespace RistWorld.Components;

public sealed record RegionDefinerControllerState(
    string Phase,
    int SelectedCount,
    string GridShape,
    int TierIndex,
    bool Pending,
    bool ExitRequested,
    string RegionId,
    string RegionName);
