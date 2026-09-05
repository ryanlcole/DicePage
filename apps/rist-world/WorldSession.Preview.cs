namespace RistWorld;

public sealed partial class WorldSession
{
    /// <summary>
    /// Public Preview is a demonstration runtime, never a persistence authority.
    /// It may render and accept local demonstration interactions, but it must not
    /// load, overwrite, export to, or synchronize a player's private campaign.
    /// </summary>
    public bool PublicPreviewMode { get; private set; }

    public void EnablePublicPreviewMode()
    {
        if (PublicPreviewMode) return;
        PublicPreviewMode = true;
        Role = "PC";
        SaveMenuOpen = false;
        LoadMenuOpen = false;
        PrivateStorageStatus = "Public preview · changes are not saved.";
        Notify();
    }

    public string RuntimeAccessLabel => PublicPreviewMode
        ? "Public preview · changes are not saved"
        : IsLoggedIn
            ? "Signed-in game"
            : "Session unavailable";
}
