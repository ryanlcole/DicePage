namespace RistWorld.Components;

public partial class WorldBuilderStudio
{
    /// <summary>
    /// Rehydrate the account-owned map card before the builder renders. Browser
    /// storage is only a recovery cache; logged-in users restore from AWS. TIFF
    /// imports leave a glyph reference token that resolves back to the card.
    /// </summary>
    protected override async Task OnInitializedAsync()
    {
        string? importReference = null;
        try
        {
            importReference = await JS.InvokeAsync<string?>("localStorage.getItem", "rist.card.import.reference");
            if (!string.IsNullOrWhiteSpace(importReference))
                await JS.InvokeVoidAsync("localStorage.removeItem", "rist.card.import.reference");
        }
        catch { }

        var loadedCard = false;
        if (!string.IsNullOrWhiteSpace(importReference) && importReference.StartsWith("RIST1|", StringComparison.Ordinal))
        {
            var parts = importReference.Split('|');
            if (parts.Length >= 2 && string.Equals(parts[1], Session.ActiveMapCardId, StringComparison.Ordinal))
                loadedCard = await Session.LoadActiveMapCardAsync();
        }

        if (!loadedCard)
            loadedCard = await Session.LoadActiveMapCardAsync();
        if (!loadedCard)
            await Session.LoadAsync();

        await EnsureWorldAtlasAsync();
        RestoreQuickTilesFromActiveCard();
    }
}
