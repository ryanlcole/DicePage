using System.Text.Json;

namespace RistWorld;

public sealed class PrivateCardLibrary(DiscordAuthClient auth)
{
    const string CustomKey = "cards/decks/custom-cards.json";
    const string SpellbookKey = "cards/spellbooks/active-character.json";
    static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true
    };

    public event Action? Changed;

    public List<LibraryCard> Cards { get; } = [];
    public List<string> SpellbookIds { get; } = [];

    public LibraryCard? DraggingCard { get; private set; }

    public bool Loading { get; private set; }
    public bool Loaded { get; private set; }

    public string Status { get; private set; } = "";

    public IEnumerable<LibraryCard> SpellbookCards
    {
        get
        {
            if (SpellbookIds.Count == 0 || Cards.Count == 0)
                return [];

            var byId = Cards.ToDictionary(card => card.Id, StringComparer.Ordinal);
            return SpellbookIds
                .Select(id => byId.GetValueOrDefault(id))
                .OfType<LibraryCard>()
                .ToList();
        }
    }

    public async Task EnsureLoadedAsync()
    {
        if (Loaded || Loading)
            return;

        Loading = true;
        Status = "";

        try
        {
            Cards.Clear();
            SpellbookIds.Clear();

            try
            {
                var custom =
                    await auth.DownloadJsonAsync<StoredCardDeck>(CustomKey);

                if (custom?.Cards is not null)
                {
                    foreach (var card in custom.Cards)
                    {
                        if (
                            string.IsNullOrWhiteSpace(card.Source) ||
                            card.Source.Equals(
                                "Custom",
                                StringComparison.OrdinalIgnoreCase
                            )
                        )
                        {
                            card.Source = "Shaelvien";
                        }
                    }

                    Cards.AddRange(custom.Cards);
                }
            }
            catch
            {
            }

            try
            {
                var spellbook =
                    await auth.DownloadJsonAsync<StoredSpellbook>(
                        SpellbookKey
                    );

                if (spellbook?.CardIds is not null)
                {
                    SpellbookIds.AddRange(
                        spellbook.CardIds.Distinct(StringComparer.Ordinal)
                    );
                }
            }
            catch
            {
            }

            Loaded = true;
        }
        finally
        {
            Loading = false;
            Changed?.Invoke();
        }
    }

    public async Task CreateCustomAsync(CardDraft draft)
    {
        var name = draft.Name.Trim();

        if (string.IsNullOrWhiteSpace(name))
        {
            Status = "Give the card a name.";
            Changed?.Invoke();
            return;
        }

        var card = new LibraryCard
        {
            Id = "custom-" + Guid.NewGuid().ToString("N"),

            Name = name,

            Description = draft.Description.Trim(),

            School = draft.Category.Trim(),

            ImageDataUrl = draft.ImageDataUrl,

            Type =
                string.IsNullOrWhiteSpace(draft.Type)
                    ? "Standard"
                    : draft.Type,

            Source =
                string.IsNullOrWhiteSpace(draft.LibraryName)
                    ? "Shaelvien"
                    : draft.LibraryName.Trim(),

            Custom = true
        };

        Cards.Add(card);

        await SaveCustomAsync();

        Status = $"Created {card.Name}.";

        Changed?.Invoke();
    }

    public async Task ImportCustomAsync(Stream source)
    {
        Loading = true;
        Status = "";

        try
        {
            var drafts =
                await JsonSerializer.DeserializeAsync<List<CardDraft>>(
                    source,
                    JsonOptions
                )
                ?? throw new InvalidDataException(
                    "The custom card file is empty."
                );

            var imported = 0;

            foreach (var draft in drafts)
            {
                var name = draft.Name.Trim();

                if (string.IsNullOrWhiteSpace(name))
                    continue;

                Cards.Add(
                    new LibraryCard
                    {
                        Id =
                            "custom-" +
                            Guid.NewGuid().ToString("N"),

                        Name = name,

                        Description =
                            draft.Description.Trim(),

                        School =
                            draft.Category.Trim(),

                        ImageDataUrl =
                            draft.ImageDataUrl,

                        Type =
                            string.IsNullOrWhiteSpace(draft.Type)
                                ? "Standard"
                                : draft.Type,

                        Source =
                            string.IsNullOrWhiteSpace(
                                draft.LibraryName
                            )
                                ? "Shaelvien"
                                : draft.LibraryName.Trim(),

                        Custom = true
                    }
                );

                imported++;
            }

            if (imported == 0)
            {
                throw new InvalidDataException(
                    "No named custom cards were found."
                );
            }

            await SaveCustomAsync();

            Loaded = true;

            Status =
                imported == 1
                    ? "Imported 1 custom card."
                    : $"Imported {imported:N0} custom cards.";
        }
        catch (Exception ex)
        {
            Status = "Import failed: " + ex.Message;
        }
        finally
        {
            Loading = false;
            Changed?.Invoke();
        }
    }

    public void BeginDrag(LibraryCard card)
    {
        DraggingCard = card;
    }

    public async Task DropOnSpellbookAsync()
    {
        if (DraggingCard is null)
            return;

        await AddToSpellbookAsync(DraggingCard);

        DraggingCard = null;
    }

    public async Task AddToSpellbookAsync(
        LibraryCard card
    )
    {
        if (!SpellbookIds.Contains(card.Id, StringComparer.Ordinal))
        {
            SpellbookIds.Add(card.Id);

            await SaveSpellbookAsync();

            Status =
                $"{card.Name} added to the active character's spellbook.";

            Changed?.Invoke();
        }
    }

    public async Task RemoveFromSpellbookAsync(
        LibraryCard card
    )
    {
        if (SpellbookIds.Remove(card.Id))
        {
            await SaveSpellbookAsync();

            Changed?.Invoke();
        }
    }

    public void Reset()
    {
        if (
            !Loaded &&
            Cards.Count == 0 &&
            SpellbookIds.Count == 0 &&
            string.IsNullOrEmpty(Status)
        )
        {
            return;
        }

        Cards.Clear();
        SpellbookIds.Clear();

        DraggingCard = null;

        Loaded = false;
        Loading = false;

        Status = "";

        Changed?.Invoke();
    }

    async Task SaveCustomAsync()
    {
        var custom =
            Cards
                .Where(card => card.Custom)
                .ToList();

        await auth.UploadTextAsync(
            CustomKey,

            JsonSerializer.Serialize(
                new StoredCardDeck(
                    "shaelvien-private-cards",
                    "Shaelvien cards",
                    "private",
                    custom
                ),
                JsonOptions
            ),

            "application/json"
        );
    }

    async Task SaveSpellbookAsync()
    {
        await auth.UploadTextAsync(
            SpellbookKey,

            JsonSerializer.Serialize(
                new StoredSpellbook(
                    SpellbookIds
                ),
                JsonOptions
            ),

            "application/json"
        );
    }
}

public sealed record StoredCardDeck(
    string DeckId,
    string Title,
    string Visibility,
    List<LibraryCard> Cards
);

public sealed record StoredSpellbook(
    List<string> CardIds
);

public sealed class CardDraft
{
    public string LibraryName { get; set; } =
        "Shaelvien";

    public string Name { get; set; } = "";

    public string Type { get; set; } = "";

    public string Category { get; set; } = "";

    public string Description { get; set; } = "";

    public string ImageDataUrl { get; set; } = "";
}

public sealed class LibraryCard
{
    public string Id { get; set; } = "";

    public string Name { get; set; } = "";

    public string Description { get; set; } = "";

    public string School { get; set; } = "";

    public string ImageDataUrl { get; set; } = "";

    public string Type { get; set; } = "Standard";

    public string Source { get; set; } = "Shaelvien";

    public bool Custom { get; set; }
}
