using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace RistWorld;

public enum RistCardType
{
    World,
    Region,
    Local,
    Instance,
    Encounter,
    Npc,
    Monster,
    Creature,
    Actor,
    ArmorPiece,
    ArmorSet,
    Weapon,
    Enchantment,
    Spell,
    Lore,
    AssetPack
}

public sealed record RistCardReference(string CardId, string Relation, RistCardType? Type = null);

public sealed class RistCardEnvelope
{
    public string Format { get; set; } = "RISTCARD";
    public int Version { get; set; } = 1;
    public string CardId { get; set; } = "";
    public RistCardType CardType { get; set; }
    public string OwnerAccountId { get; set; } = "";
    public string WorldId { get; set; } = "";
    public string Name { get; set; } = "";
    public string Visibility { get; set; } = "private";
    public bool Published { get; set; }
    public DateTimeOffset UpdatedAtUtc { get; set; }
    public string ArtAssetId { get; set; } = "";
    public string ArtDataMark { get; set; } = "";
    public string ManifestHash { get; set; } = "";
    public List<RistCardReference> References { get; set; } = [];
    public List<string> AssetPackIds { get; set; } = [];
    public JsonElement Payload { get; set; }
}

public sealed partial class WorldSession
{
    public const string CardStoragePrefix = "cards";
    public const string PublishedCardStoragePrefix = "published-cards";
    readonly List<RistCardEnvelope> _ownedCardEnvelopes = [];
    public IReadOnlyList<RistCardEnvelope> OwnedCardEnvelopes => _ownedCardEnvelopes;

    public static string CardTypeSlug(RistCardType type) => type switch
    {
        RistCardType.Npc => "npc",
        RistCardType.ArmorPiece => "armor-piece",
        RistCardType.ArmorSet => "armor-set",
        RistCardType.AssetPack => "asset-pack",
        _ => type.ToString().ToLowerInvariant()
    };

    // Cards belong to the account, not to a browser or a single world. WorldId in
    // the envelope links a card into a world when appropriate, but ownership stays
    // at the account boundary so cards can move between campaigns and future devices.
    public string PrivateCardKey(RistCardType type, string cardId) =>
        $"{CardStoragePrefix}/{CardTypeSlug(type)}/{cardId}.json";

    public string PublishedCardKey(RistCardType type, string cardId) =>
        $"{PublishedCardStoragePrefix}/{CardTypeSlug(type)}/{cardId}.json";

    public static string ComputeCardManifestHash<T>(T manifest)
    {
        var json = JsonSerializer.Serialize(manifest);
        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(json))).ToLowerInvariant();
    }

    // Shaelvien's machine-readable art mark is derived from canonical identity and
    // reconstruction data, not from another trading-card layout. A renderer can
    // encode this value into Shaelvien artwork metadata/patterns or a future physical
    // marker without changing card identity.
    public static string ComputeArtDataMark(string cardId, RistCardType type, string manifestHash)
    {
        var material = $"RIST|{cardId}|{CardTypeSlug(type)}|{manifestHash}";
        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(material))).ToLowerInvariant();
    }

    public async Task SaveCardEnvelopeAsync(RistCardEnvelope card)
    {
        if (string.IsNullOrWhiteSpace(card.CardId)) throw new ArgumentException("Card ID is required.", nameof(card));
        card.OwnerAccountId = string.IsNullOrWhiteSpace(card.OwnerAccountId) ? WorldOwnerAccountId : card.OwnerAccountId;
        card.UpdatedAtUtc = DateTimeOffset.UtcNow;
        card.ManifestHash = ComputeCardManifestHash(new
        {
            card.CardId,
            card.CardType,
            card.OwnerAccountId,
            card.WorldId,
            card.Name,
            card.Visibility,
            card.Published,
            card.References,
            card.AssetPackIds,
            card.Payload
        });
        card.ArtDataMark = ComputeArtDataMark(card.CardId, card.CardType, card.ManifestHash);

        var existing = _ownedCardEnvelopes.FindIndex(x => string.Equals(x.CardId, card.CardId, StringComparison.Ordinal));
        if (existing >= 0) _ownedCardEnvelopes[existing] = card;
        else _ownedCardEnvelopes.Add(card);
        Notify();

        if (!IsLoggedIn) return;
        var json = JsonSerializer.Serialize(card, MapWriteOptions);
        await auth.UploadTextAsync(PrivateCardKey(card.CardType, card.CardId), json, "application/json");
        if (card.Published)
            await auth.UploadTextAsync(PublishedCardKey(card.CardType, card.CardId), json, "application/json");
    }

    public async Task LoadOwnedCardEnvelopesAsync()
    {
        _ownedCardEnvelopes.Clear();
        if (!IsLoggedIn) { Notify(); return; }
        try
        {
            var listing = await auth.ListAsync(CardStoragePrefix + "/");
            if (listing?.Items is null) { Notify(); return; }
            foreach (var item in listing.Items
                .Where(x => x.Key.EndsWith(".json", StringComparison.OrdinalIgnoreCase))
                .OrderByDescending(x => x.LastModified)
                .Take(100))
            {
                try
                {
                    var card = await auth.DownloadJsonAsync<RistCardEnvelope>(item.Key);
                    if (card is not null && string.Equals(card.Format, "RISTCARD", StringComparison.Ordinal))
                        _ownedCardEnvelopes.Add(card);
                }
                catch { }
            }
        }
        catch { }
        Notify();
    }
}
