using System.Text.Json;

namespace RistWorld;

public sealed class RistCardStack
{
    public string Format { get; set; } = "RISTCARDSTACK";
    public int Version { get; set; } = 1;
    public string StackId { get; set; } = "";
    public string OwnerAccountId { get; set; } = "";
    public string CreatorProvenanceId { get; set; } = "";
    public string WorldId { get; set; } = "";
    public string Name { get; set; } = "Table Stack";
    public DateTimeOffset UpdatedAtUtc { get; set; }
    public string CompositionHash { get; set; } = "";
    public List<RistCardStackEntry> Cards { get; set; } = [];
}

public sealed class RistCardStackEntry
{
    public int Order { get; set; }
    public string CardId { get; set; } = "";
    public RistCardType CardType { get; set; }
    public string ManifestHash { get; set; } = "";
    public string CreatorProvenanceId { get; set; } = "";
    public string GlyphToken { get; set; } = "";
    public DateTimeOffset ScannedAtUtc { get; set; }
}

public sealed class RistStackMeshManifest
{
    public string Format { get; set; } = "RISTSTACKMESH";
    public int Version { get; set; } = 1;
    public string StackId { get; set; } = "";
    public string CompositionHash { get; set; } = "";
    public List<RistCardStackEntry> Cards { get; set; } = [];
}

public sealed partial class WorldSession
{
    public const string CardStackStoragePrefix = "card-stacks";
    RistCardStack _activeCardStack = new();

    public RistCardStack ActiveCardStack => _activeCardStack;
    public string ActiveCardStackId => $"{WorldId}-table-stack-001";
    public string ActiveCardStackLocalKey => $"rist.cardstack.{ActiveCardStackId}";
    public string ActiveCardStackCloudKey => $"{CardStackStoragePrefix}/{ActiveCardStackId}.json";

    public async Task<bool> AddScannedCardToActiveStackAsync(string glyphToken)
    {
        if (!TryParseGlyphToken(glyphToken, out var parsed)) return false;

        if (_ownedCardEnvelopes.Count == 0 && IsLoggedIn)
            await LoadOwnedCardEnvelopesAsync();

        var envelope = _ownedCardEnvelopes.FirstOrDefault(x => string.Equals(x.CardId, parsed.CardId, StringComparison.Ordinal));
        var type = parsed.CardType ?? envelope?.CardType ?? RistCardType.World;
        var provenance = !string.IsNullOrWhiteSpace(parsed.CreatorProvenanceId)
            ? parsed.CreatorProvenanceId
            : envelope?.CreatorProvenanceId ?? "";
        var manifestHash = !string.IsNullOrWhiteSpace(parsed.ManifestHash)
            ? parsed.ManifestHash
            : envelope?.ManifestHash ?? "";

        if (_activeCardStack.Cards.Any(x => string.Equals(x.CardId, parsed.CardId, StringComparison.Ordinal) &&
                                            string.Equals(x.ManifestHash, manifestHash, StringComparison.Ordinal)))
            return true;

        EnsureActiveCardStackIdentity();
        _activeCardStack.Cards.Add(new RistCardStackEntry
        {
            Order = _activeCardStack.Cards.Count,
            CardId = parsed.CardId,
            CardType = type,
            ManifestHash = manifestHash,
            CreatorProvenanceId = provenance,
            GlyphToken = glyphToken,
            ScannedAtUtc = DateTimeOffset.UtcNow
        });
        await SaveActiveCardStackAsync();
        return true;
    }

    public async Task<bool> RemoveCardFromActiveStackAsync(int order)
    {
        if (order < 0 || order >= _activeCardStack.Cards.Count) return false;
        _activeCardStack.Cards.RemoveAt(order);
        NormalizeActiveStackOrder();
        await SaveActiveCardStackAsync();
        return true;
    }

    public async Task<bool> MoveCardInActiveStackAsync(int fromOrder, int toOrder)
    {
        if (fromOrder < 0 || fromOrder >= _activeCardStack.Cards.Count) return false;
        toOrder = Math.Clamp(toOrder, 0, _activeCardStack.Cards.Count - 1);
        if (fromOrder == toOrder) return true;
        var card = _activeCardStack.Cards[fromOrder];
        _activeCardStack.Cards.RemoveAt(fromOrder);
        _activeCardStack.Cards.Insert(toOrder, card);
        NormalizeActiveStackOrder();
        await SaveActiveCardStackAsync();
        return true;
    }

    public async Task ClearActiveCardStackAsync()
    {
        EnsureActiveCardStackIdentity();
        _activeCardStack.Cards.Clear();
        await SaveActiveCardStackAsync();
    }

    public async Task SaveActiveCardStackAsync()
    {
        EnsureActiveCardStackIdentity();
        NormalizeActiveStackOrder();
        _activeCardStack.UpdatedAtUtc = DateTimeOffset.UtcNow;
        _activeCardStack.CompositionHash = ComputeCardManifestHash(new
        {
            _activeCardStack.StackId,
            _activeCardStack.WorldId,
            Cards = _activeCardStack.Cards.Select(x => new
            {
                x.Order,
                x.CardId,
                x.CardType,
                x.ManifestHash,
                x.CreatorProvenanceId
            })
        });

        var json = JsonSerializer.Serialize(_activeCardStack, MapWriteOptions);
        try { await js.InvokeVoidAsync("localStorage.setItem", ActiveCardStackLocalKey, json); } catch { }
        if (IsLoggedIn)
            await auth.UploadTextAsync(ActiveCardStackCloudKey, json, "application/json");
        Notify();
    }

    public async Task<bool> LoadActiveCardStackAsync()
    {
        RistCardStack? stack = null;
        if (IsLoggedIn)
        {
            try { stack = await auth.DownloadJsonAsync<RistCardStack>(ActiveCardStackCloudKey); } catch { }
        }
        if (stack is null)
        {
            try
            {
                var raw = await js.InvokeAsync<string?>("localStorage.getItem", ActiveCardStackLocalKey);
                if (!string.IsNullOrWhiteSpace(raw))
                    stack = JsonSerializer.Deserialize<RistCardStack>(raw, MapReadOptions);
            }
            catch { }
        }
        if (stack is null || !string.Equals(stack.Format, "RISTCARDSTACK", StringComparison.Ordinal) ||
            !string.Equals(stack.WorldId, WorldId, StringComparison.Ordinal))
        {
            EnsureActiveCardStackIdentity();
            return false;
        }

        _activeCardStack = stack;
        EnsureActiveCardStackIdentity();
        NormalizeActiveStackOrder();
        Notify();
        return true;
    }

    public RistStackMeshManifest BuildActiveCardStackMeshManifest()
    {
        EnsureActiveCardStackIdentity();
        NormalizeActiveStackOrder();
        return new RistStackMeshManifest
        {
            StackId = _activeCardStack.StackId,
            CompositionHash = _activeCardStack.CompositionHash,
            Cards = _activeCardStack.Cards.Select(x => new RistCardStackEntry
            {
                Order = x.Order,
                CardId = x.CardId,
                CardType = x.CardType,
                ManifestHash = x.ManifestHash,
                CreatorProvenanceId = x.CreatorProvenanceId,
                GlyphToken = x.GlyphToken,
                ScannedAtUtc = x.ScannedAtUtc
            }).ToList()
        };
    }

    public string ExportActiveCardStackMeshManifestJson() =>
        JsonSerializer.Serialize(BuildActiveCardStackMeshManifest(), MapWriteOptions);

    void EnsureActiveCardStackIdentity()
    {
        _activeCardStack.StackId = ActiveCardStackId;
        _activeCardStack.OwnerAccountId = WorldOwnerAccountId;
        _activeCardStack.CreatorProvenanceId = ComputeCreatorProvenanceId(WorldOwnerAccountId);
        _activeCardStack.WorldId = WorldId;
        if (string.IsNullOrWhiteSpace(_activeCardStack.Name)) _activeCardStack.Name = "Table Stack";
    }

    void NormalizeActiveStackOrder()
    {
        for (var i = 0; i < _activeCardStack.Cards.Count; i++)
            _activeCardStack.Cards[i].Order = i;
    }

    static bool TryParseGlyphToken(string? token, out ParsedGlyphCard parsed)
    {
        parsed = new ParsedGlyphCard();
        if (string.IsNullOrWhiteSpace(token)) return false;
        var parts = token.Split('|');
        if (parts.Length >= 3 && string.Equals(parts[0], "RIST1", StringComparison.Ordinal))
        {
            parsed.CardId = parts[1];
            parsed.ManifestHash = parts[2];
            return !string.IsNullOrWhiteSpace(parsed.CardId);
        }
        if (parts.Length >= 5 && string.Equals(parts[0], "RIST2", StringComparison.Ordinal))
        {
            parsed.CardType = TryParseCardTypeSlug(parts[1]);
            parsed.CardId = parts[2];
            parsed.ManifestHash = parts[3];
            parsed.CreatorProvenanceId = parts[4];
            return !string.IsNullOrWhiteSpace(parsed.CardId);
        }
        return false;
    }

    static RistCardType? TryParseCardTypeSlug(string? slug) => slug?.Trim().ToLowerInvariant() switch
    {
        "world" => RistCardType.World,
        "region" => RistCardType.Region,
        "local" => RistCardType.Local,
        "instance" => RistCardType.Instance,
        "encounter" => RistCardType.Encounter,
        "npc" => RistCardType.Npc,
        "monster" => RistCardType.Monster,
        "creature" => RistCardType.Creature,
        "actor" => RistCardType.Actor,
        "armor-piece" => RistCardType.ArmorPiece,
        "armor-set" => RistCardType.ArmorSet,
        "weapon" => RistCardType.Weapon,
        "enchantment" => RistCardType.Enchantment,
        "spell" => RistCardType.Spell,
        "lore" => RistCardType.Lore,
        "asset-pack" => RistCardType.AssetPack,
        _ => null
    };

    sealed class ParsedGlyphCard
    {
        public string CardId { get; set; } = "";
        public RistCardType? CardType { get; set; }
        public string ManifestHash { get; set; } = "";
        public string CreatorProvenanceId { get; set; } = "";
    }
}
