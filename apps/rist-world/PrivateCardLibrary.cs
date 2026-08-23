using System.IO.Compression;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace RistWorld;

public sealed class PrivateCardLibrary(DiscordAuthClient auth)
{
    const string PathfinderKey = "cards/decks/naeja-pathfinder-1e-private-test.json";
    const string CustomKey = "cards/decks/custom-cards.json";
    const string SpellbookKey = "cards/spellbooks/active-character.json";
    static readonly JsonSerializerOptions JsonOptions = new() { PropertyNameCaseInsensitive = true };

    public event Action? Changed;
    public List<LibraryCard> Cards { get; } = [];
    public List<string> SpellbookIds { get; } = [];
    public LibraryCard? DraggingCard { get; private set; }
    public bool Loading { get; private set; }
    public bool Loaded { get; private set; }
    public string Status { get; private set; } = "";

    public IEnumerable<LibraryCard> SpellbookCards =>
        SpellbookIds.Select(id => Cards.FirstOrDefault(card => card.Id == id)).Where(card => card is not null)!;

    public async Task EnsureLoadedAsync()
    {
        if (Loaded || Loading) return;
        Loading = true; Status = "";
        try
        {
            Cards.Clear();
            try
            {
                var pathfinder = await auth.DownloadJsonAsync<StoredCardDeck>(PathfinderKey);
                if (pathfinder?.Cards is not null) Cards.AddRange(pathfinder.Cards);
            }
            catch { }
            try
            {
                var custom = await auth.DownloadJsonAsync<StoredCardDeck>(CustomKey);
                if (custom?.Cards is not null) Cards.AddRange(custom.Cards);
            }
            catch { }
            try
            {
                var spellbook = await auth.DownloadJsonAsync<StoredSpellbook>(SpellbookKey);
                if (spellbook?.CardIds is not null) SpellbookIds.AddRange(spellbook.CardIds.Distinct());
            }
            catch { }
            Loaded = true;
        }
        finally { Loading = false; Changed?.Invoke(); }
    }

    public async Task ImportPathfinderAsync(Stream source)
    {
        Loading = true; Status = "";
        try
        {
            using var memory = new MemoryStream();
            await source.CopyToAsync(memory);
            memory.Position = 0;
            using var archive = new ZipArchive(memory, ZipArchiveMode.Read);
            var manifestEntry = archive.Entries.FirstOrDefault(x => x.FullName.EndsWith("spell-cards/data/manifest.json", StringComparison.OrdinalIgnoreCase))
                ?? throw new InvalidDataException("The Pathfinder deck manifest is missing.");
            DeckManifest manifest;
            await using (var manifestStream = manifestEntry.Open())
                manifest = await JsonSerializer.DeserializeAsync<DeckManifest>(manifestStream, JsonOptions)
                    ?? throw new InvalidDataException("The Pathfinder deck manifest is invalid.");
            if (manifest.DeckId != "naeja-pathfinder-1e-private-test" || manifest.Visibility != "private-test-only")
                throw new InvalidDataException("This is not the approved private Pathfinder deck.");

            var imported = new List<LibraryCard>(manifest.SpellCount);
            foreach (var chunk in manifest.Chunks)
            {
                var normalized = chunk.File.Replace('\\', '/');
                var entry = archive.Entries.FirstOrDefault(x => x.FullName.EndsWith(normalized, StringComparison.OrdinalIgnoreCase))
                    ?? throw new InvalidDataException("A spell-data chunk is missing.");
                await using var chunkStream = entry.Open();
                imported.AddRange(await JsonSerializer.DeserializeAsync<List<LibraryCard>>(chunkStream, JsonOptions) ?? []);
            }
            if (imported.Count != manifest.SpellCount)
                throw new InvalidDataException($"Expected {manifest.SpellCount} spells but found {imported.Count}.");

            Cards.RemoveAll(card => card.Source == "Pathfinder 1e" || !card.Custom);
            foreach (var card in imported) { card.Source = "Pathfinder 1e"; card.Type = "Spell"; }
            Cards.AddRange(imported);
            await auth.UploadTextAsync(PathfinderKey, JsonSerializer.Serialize(new StoredCardDeck(manifest.DeckId, manifest.Title, manifest.Visibility, imported), JsonOptions), "application/json");
            Loaded = true; Status = $"{imported.Count:N0} private spell cards saved.";
        }
        catch (Exception ex) { Status = "Import failed: " + ex.Message; }
        finally { Loading = false; Changed?.Invoke(); }
    }

    public async Task CreateCustomAsync(CardDraft draft)
    {
        var name = draft.Name.Trim();
        if (string.IsNullOrWhiteSpace(name)) { Status = "Give the card a name."; Changed?.Invoke(); return; }
        var card = new LibraryCard
        {
            Id = "custom-" + Guid.NewGuid().ToString("N"),
            Name = name,
            Description = draft.Description.Trim(),
            School = draft.Category.Trim(),
            Type = string.IsNullOrWhiteSpace(draft.Type) ? "Spell" : draft.Type,
            Source = "Custom",
            Custom = true
        };
        Cards.Add(card);
        await SaveCustomAsync();
        Status = $"Created {card.Name}.";
        Changed?.Invoke();
    }

    public void BeginDrag(LibraryCard card) => DraggingCard = card;

    public async Task DropOnSpellbookAsync()
    {
        if (DraggingCard is null) return;
        await AddToSpellbookAsync(DraggingCard);
        DraggingCard = null;
    }

    public async Task AddToSpellbookAsync(LibraryCard card)
    {
        if (!SpellbookIds.Contains(card.Id))
        {
            SpellbookIds.Add(card.Id);
            await SaveSpellbookAsync();
            Status = $"{card.Name} added to the active character's spellbook.";
            Changed?.Invoke();
        }
    }

    public async Task RemoveFromSpellbookAsync(LibraryCard card)
    {
        if (SpellbookIds.Remove(card.Id))
        {
            await SaveSpellbookAsync();
            Changed?.Invoke();
        }
    }

    public void Reset()
    {
        Cards.Clear(); SpellbookIds.Clear(); DraggingCard = null; Loaded = false; Loading = false; Status = "";
        Changed?.Invoke();
    }

    async Task SaveCustomAsync()
    {
        var custom = Cards.Where(card => card.Custom).ToList();
        await auth.UploadTextAsync(CustomKey, JsonSerializer.Serialize(new StoredCardDeck("custom-private-cards", "Custom cards", "private", custom), JsonOptions), "application/json");
    }

    async Task SaveSpellbookAsync() =>
        await auth.UploadTextAsync(SpellbookKey, JsonSerializer.Serialize(new StoredSpellbook(SpellbookIds), JsonOptions), "application/json");
}

public sealed record StoredCardDeck(string DeckId, string Title, string Visibility, List<LibraryCard> Cards);
public sealed record StoredSpellbook(List<string> CardIds);
public sealed class CardDraft
{
    public string Name { get; set; } = "";
    public string Type { get; set; } = "Spell";
    public string Category { get; set; } = "";
    public string Description { get; set; } = "";
}
public sealed class DeckManifest
{
    [JsonPropertyName("deck_id")] public string DeckId { get; set; } = "";
    public string Title { get; set; } = "";
    public string Visibility { get; set; } = "";
    [JsonPropertyName("spell_count")] public int SpellCount { get; set; }
    public List<DeckChunk> Chunks { get; set; } = [];
}
public sealed class DeckChunk { public string File { get; set; } = ""; public int Count { get; set; } }
public sealed class LibraryCard
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public string Description { get; set; } = "";
    public string Rating { get; set; } = "";
    public string School { get; set; } = "";
    public string? Subschool { get; set; }
    [JsonPropertyName("casting_time")] public string? CastingTime { get; set; }
    public string? Range { get; set; }
    public string? Area { get; set; }
    public string? Effect { get; set; }
    public string? Targets { get; set; }
    public string? Duration { get; set; }
    [JsonPropertyName("saving_throw")] public string? SavingThrow { get; set; }
    [JsonPropertyName("spell_resistance")] public string? SpellResistance { get; set; }
    public string? Sourcebook { get; set; }
    public Dictionary<string, string> Classes { get; set; } = [];
    public string Type { get; set; } = "Spell";
    public string Source { get; set; } = "";
    public bool Custom { get; set; }
}
