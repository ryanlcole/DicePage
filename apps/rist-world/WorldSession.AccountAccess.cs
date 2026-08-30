namespace RistWorld;

public sealed partial class WorldSession
{
    public bool AccountViewerOpen { get; private set; }
    public string PendingDisplayName { get; set; } = "";
    public string PendingPlayerAlias { get; set; } = "";
    public string PendingProfileNote { get; set; } = "";
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
        PendingDisplayName = PendingDisplayName.Trim();
        PendingPlayerAlias = PendingPlayerAlias.Trim();
        PendingProfileNote = PendingProfileNote.Trim();
        if (PendingDisplayName.Length == 0 || PendingPlayerAlias.Length == 0 || !PendingTermsAccepted) return;
        PendingPlan = PendingPlan is "gm-player" ? "gm-player" : "player";

        await js.InvokeVoidAsync("localStorage.setItem", "rist.auth.intent", "signup");
        await js.InvokeVoidAsync("localStorage.setItem", "rist.signup.displayName", PendingDisplayName);
        await js.InvokeVoidAsync("localStorage.setItem", "rist.signup.alias", PendingPlayerAlias);
        await js.InvokeVoidAsync("localStorage.setItem", "rist.signup.profileNote", PendingProfileNote);
        await js.InvokeVoidAsync("localStorage.setItem", "rist.signup.plan", PendingPlan);
        await js.InvokeVoidAsync("localStorage.setItem", "rist.signup.termsAccepted", "true");

        AccountViewerOpen = false;
        Notify();
        await ToggleLoginAsync();
    }

    public async Task BeginAccountLoginAsync()
    {
        await js.InvokeVoidAsync("localStorage.setItem", "rist.auth.intent", "login");
        AccountViewerOpen = false;
        Notify();
        await ToggleLoginAsync();
    }
}
