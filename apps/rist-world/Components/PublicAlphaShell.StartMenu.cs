namespace RistWorld.Components;

public partial class PublicAlphaShell
{
    public void OpenStartMenu()
    {
        ReturnToHub();
        _ = InvokeAsync(StateHasChanged);
    }
}