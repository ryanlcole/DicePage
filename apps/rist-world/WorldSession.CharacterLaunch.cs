namespace RistWorld;

public sealed partial class WorldSession
{
    public void OpenCharacterFromLibrary()
    {
        CardBrowserOpen = false;
        TileBrowserOpen = false;
        CloseHeaderMenus();
        MixerOpen = true;
        Notify();
    }
}
