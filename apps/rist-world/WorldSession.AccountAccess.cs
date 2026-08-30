namespace RistWorld;

public sealed partial class WorldSession
{
    public bool AccountViewerOpen { get; private set; }
    public string PendingPlayerAlias { get; set; } = "";
    public string PendingPlan { get; set; } = "player";
    public bool PendingTermsAccepted { get; set; }

    public void OpenAccountViewer()
    {
        AccountViewerOpen = true;
        CloseHeaderMenus();
        Notify();
    }

    public void CloseAccountViewer()
    {
        AccountViewerOpen = false;
        Notify();
    }

    public async Task BeginAccountSignupAsync()
    {
        PendingPlayerAlias = PendingPlayerAlias.Trim();
        if (PendingPlayerAlias.Length == 0 || !PendingTermsAccepted) return;
        PendingPlan = PendingPlan is "gm-player" ? "gm-player" : "player";
        await js.InvokeVoidAsync("localStorage.setItem", "rist.signup.alias", PendingPlayerAlias);
        await js.InvokeVoidAsync("localStorage.setItem", "rist.signup.plan", PendingPlan);
        await js.InvokeVoidAsync("localStorage.setItem", "rist.signup.termsAccepted", "true");
        AccountViewerOpen = false;
        Notify();
        await ToggleLoginAsync();
    }

    public async Task BeginAccountLoginAsync()
    {
        AccountViewerOpen = false;
        Notify();
        await ToggleLoginAsync();
    }
}
