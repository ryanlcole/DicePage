using System.Text.Json;
using System.Text.Json.Nodes;

namespace RistWorld;

public sealed partial class WorldSession
{
    // All Shaelvien deed representations currently share one WORLDSOURCE item.
    // A save may replace only its own layer scope: Endemar owns unscoped layers,
    // while a deed owns layers carrying that deed's regionId. Metadata outside
    // the editor's map fields is preserved unless explicitly supplied.
    public static JsonElement MergeWorldBuilderRepresentationState(
        JsonElement incomingState,
        JsonElement? currentState,
        string regionScopeId = "")
    {
        if (incomingState.ValueKind != JsonValueKind.Object)
            return incomingState.Clone();

        var incoming = JsonNode.Parse(incomingState.GetRawText()) as JsonObject ?? new JsonObject();
        JsonObject? current = null;
        if (currentState is JsonElement existing && existing.ValueKind == JsonValueKind.Object)
            current = JsonNode.Parse(existing.GetRawText()) as JsonObject;

        if (current is not null)
        {
            foreach (var property in current)
            {
                if (string.Equals(property.Key, "userLayers", StringComparison.Ordinal)) continue;
                if (!incoming.ContainsKey(property.Key))
                    incoming[property.Key] = property.Value?.DeepClone();
            }
        }

        var scope = (regionScopeId ?? "").Trim();

        static string LayerRegionId(JsonNode? node)
            => node is JsonObject obj ? (obj["regionId"]?.GetValue<string>() ?? "").Trim() : "";

        bool InScope(JsonNode? node)
        {
            var layerRegionId = LayerRegionId(node);
            return scope.Length == 0
                ? layerRegionId.Length == 0
                : string.Equals(layerRegionId, scope, StringComparison.Ordinal);
        }

        var mergedLayers = new JsonArray();
        if (current?["userLayers"] is JsonArray currentLayers)
            foreach (var layer in currentLayers)
                if (!InScope(layer))
                    mergedLayers.Add(layer?.DeepClone());

        if (incoming["userLayers"] is JsonArray incomingLayers)
            foreach (var layer in incomingLayers)
                if (InScope(layer))
                    mergedLayers.Add(layer?.DeepClone());

        incoming["userLayers"] = mergedLayers;
        using var document = JsonDocument.Parse(incoming.ToJsonString());
        return document.RootElement.Clone();
    }

    private async Task<bool> HasOwnedPrivateWorldDescriptorAsync(string worldId, string accountId)
    {
        if (!IsLoggedIn || string.Equals(worldId, GeonaphWorldId, StringComparison.Ordinal)
            || string.IsNullOrWhiteSpace(worldId) || string.IsNullOrWhiteSpace(accountId)) return false;
        try
        {
            // The storage API derives users/{authenticated-user}/ on the server.
            // Reading this descriptor cannot read or authorize another user's world.
            var descriptor = await auth.DownloadJsonAsync<WorldRelationshipDescriptor>($"worlds/{worldId}/world.json");
            return PrivateWorldSourcePolicy.MatchesOwner(worldId, accountId, descriptor?.WorldId, descriptor?.OwnerAccountId);
        }
        catch { return false; }
    }

    public async Task<AwsAuthorityClient.WorldSource?> LoadWorldBuilderSourceAsync()
    {
        if (!IsLoggedIn || !HasActiveWorld) return null;
        var worldId = WorldId;
        var accountId = WorldOwnerAccountId;
        var token = auth.SessionToken;
        if (await HasOwnedPrivateWorldDescriptorAsync(worldId, accountId))
        {
            if (WorldId != worldId || WorldOwnerAccountId != accountId || auth.SessionToken != token) return null;
            var source = await auth.DownloadJsonAsync<AwsAuthorityClient.WorldSource>($"worlds/{worldId}/worldbuilder-source.json");
            if (source is not null && !string.Equals(source.WorldId, worldId, StringComparison.Ordinal))
                throw new InvalidOperationException("Private map identity does not match the selected world.");
            return source;
        }
        if (WorldId != worldId || WorldOwnerAccountId != accountId || auth.SessionToken != token) return null;
        var authority = await GetClaimAuthorityClientAsync();
        return authority is null ? null : await authority.GetWorldSourceAsync(worldId);
    }

    public async Task<AwsAuthorityClient.WorldSource?> SaveRegionMapLayersAsync(
        string regionId,
        JsonElement userLayers,
        bool inspectionEdit = false,
        string inspectionReason = "")
    {
        if (!HasActiveWorld)
            throw new InvalidOperationException("Choose a world before saving map changes.");
        if (userLayers.ValueKind != JsonValueKind.Array)
            throw new InvalidOperationException("Region map layers must be an array.");

        var region = _regions.FirstOrDefault(item =>
            string.Equals(item.RegionId, (regionId ?? "").Trim(), StringComparison.Ordinal));
        if (region is null || (!CanEditRegion(region) && !(inspectionEdit && TrustedPlatformDeveloper)))
            throw new UnauthorizedAccessException("Region edit authority is required to save this part of the world map.");

        var authority = await GetClaimAuthorityClientAsync();
        if (authority is null)
            throw new InvalidOperationException("World map database authority is unavailable.");

        return await authority.SaveWorldRegionMapAsync(
            WorldId,
            region.RegionId,
            userLayers,
            inspectionEdit,
            inspectionReason);
    }

    public async Task<AwsAuthorityClient.WorldSource?> SaveWorldBuilderSourceAsync(
        JsonElement state,
        bool inspectionEdit = false,
        string inspectionReason = "")
    {
        if (!HasActiveWorld)
            throw new InvalidOperationException("Choose a world before saving the shared world source.");

        // Capture the authenticated world identity before any asynchronous ownership
        // read. A world/account switch during descriptor verification must fail closed
        // before validating or writing the supplied map state.
        var worldId = WorldId;
        var accountId = WorldOwnerAccountId;
        var token = auth.SessionToken;
        var privateOwnerAtEntry = await HasOwnedPrivateWorldDescriptorAsync(worldId, accountId);
        if (WorldId != worldId || WorldOwnerAccountId != accountId || auth.SessionToken != token)
            throw new UnauthorizedAccessException("The active world or account changed while saving.");
        if (!HasTrustedWorldBuilderAuthority
            && !privateOwnerAtEntry
            && !(IsGeonaphWorld && OwnsCanonicalGeanaphZone)
            && !(inspectionEdit && TrustedPlatformDeveloper))
            throw new UnauthorizedAccessException("World Builder authority is required to save the canonical world map.");
        if (state.ValueKind != JsonValueKind.Object)
            throw new InvalidOperationException("World map state must be an object.");

        if (state.TryGetProperty("worldId", out var stateWorldId))
        {
            var value = stateWorldId.GetString()?.Trim() ?? "";
            if (value.Length > 0 && !string.Equals(value, worldId, StringComparison.Ordinal))
                throw new InvalidOperationException("World map identity does not match the active world.");
        }

        var privateOwner = privateOwnerAtEntry && await HasOwnedPrivateWorldDescriptorAsync(worldId, accountId);
        if (WorldId != worldId || WorldOwnerAccountId != accountId || auth.SessionToken != token)
            throw new UnauthorizedAccessException("The active world or account changed while saving.");
        if (privateOwner)
        {
            var source = new AwsAuthorityClient.WorldSource(worldId, state.Clone(), DateTimeOffset.UtcNow.ToString("O"));
            await auth.UploadTextAsync($"worlds/{worldId}/worldbuilder-source.json",
                JsonSerializer.Serialize(source, MapWriteOptions), "application/json");
            return source;
        }
        if (_trustedPrivateWorldOwner)
            throw new UnauthorizedAccessException("Private world ownership could not be verified.");

        var authority = await GetClaimAuthorityClientAsync();
        if (authority is null)
            throw new InvalidOperationException("World map database authority is unavailable.");

        return await authority.SaveWorldSourceAsync(
            WorldId,
            state,
            inspectionEdit,
            inspectionReason);
    }
}
