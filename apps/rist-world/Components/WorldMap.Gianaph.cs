namespace RistWorld.Components;

public partial class WorldMap
{
    protected override Task OnInitializedAsync()
    {
        Session.EnsureGianaphWorld();
        return Task.CompletedTask;
    }

    protected override void OnParametersSet()
    {
        Session.EnsureGianaphWorld();
    }
}
