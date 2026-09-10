namespace RistWorld.Components;

public partial class WorldBuilderStudio
{
    /// <summary>
    /// World Builder is an editing surface. Rehydrate the latest local world
    /// snapshot whenever the surface is mounted so an iOS tab/app suspension
    /// cannot return to an empty in-memory session while the save still exists.
    /// Builder edits write this snapshot immediately; AWS remains the separate
    /// private-sync authority.
    /// </summary>
    protected override async Task OnInitializedAsync()
    {
        await Session.LoadAsync();
    }
}
