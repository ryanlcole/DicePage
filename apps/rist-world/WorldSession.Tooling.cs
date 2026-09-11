namespace RistWorld;

public sealed partial class WorldSession
{
    bool _globalToolsLoaded;

    public async Task EnsureGlobalToolsAsync()
    {
        if (_globalToolsLoaded) return;
        _globalToolsLoaded = true;
        if (Cards.Count == 0) await LoadCardsAsync();
        Notify();
    }
}
