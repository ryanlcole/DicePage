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

    public static string CardTypeSlug(RistCardType type) => type switch
    {
        RistCardType.Npc => "npc",
        RistCardType.ArmorPiece => "armor-piece",
        RistCardType.ArmorSet => "armor-set",
        RistCardType.AssetPack => "asset-pack",
        _ => type.ToString().ToLowerInvariant()
    };

    public string PrivateCardKey(RistCardType type, string cardId) =>
        $"{WorldStoragePrefix}/{CardStoragePrefix}/{CardTypeSlug(type)}/{cardId}.json";

    public string PublishedCardKey(RistCardType type, string cardId) =>
        $"{WorldStoragePrefix}/{PublishedCardStoragePrefix}/{CardTypeSlug(type)}/{cardId}.json";

    public static string ComputeCardManifestHash<T>(T manifest)
    {
        var json = JsonSerializer.Serialize(manifest);
        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(json))).ToLowerInvariant();
    }

    // The art-data mark is intentionally derived from canonical identity rather than
    // visual styling. Renderers may encode this mark into Shaelvien-created artwork
    // (metadata, machine-readable pattern, future physical marker, etc.) without
    // changing the identity or copying another trading-card visual system.
    public static string ComputeArtDataMark(string cardId, RistCardType type, string manifestHash)
    {
        var material = $"RIST|{cardId}|{CardTypeSlug(type)}|{manifestHash}";
        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(material))).ToLowerInvariant();
    }

    public async Task SaveCardEnvelopeAsync(RistCardEnvelope card)
    {
        if (string.IsNullOrWhiteSpace(card.CardId)) throw new ArgumentException("Card ID is required.", nameof(card));
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
        if (!IsLoggedIn) return;
        await EnsureWorldRelationshipAsync();
        var json = JsonSerializer.Serialize(card, MapWriteOptions);
        await auth.UploadTextAsync(PrivateCardKey(card.CardType, card.CardId), json, "application/json");
        if (card.Published)
            await auth.UploadTextAsync(PublishedCardKey(card.CardType, card.CardId), json, "application/json");
    }
}
