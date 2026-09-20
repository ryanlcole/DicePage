using System.Text.Json;

namespace RistWorld;

public sealed partial class WorldSession
{
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

    public async Task<AwsAuthorityClient.WorldSource?> SaveRegionMapLayersAsync(string regionId, JsonElement userLayers)
    {
        if (!HasActiveWorld)
            throw new InvalidOperationException("Choose a world before saving map changes.");
        if (userLayers.ValueKind != JsonValueKind.Array)
            throw new InvalidOperationException("Region map layers must be an array.");

        var region = _regions.FirstOrDefault(item =>
            string.Equals(item.RegionId, (regionId ?? "").Trim(), StringComparison.Ordinal));
        if (region is null || !CanEditRegion(region))
            throw new UnauthorizedAccessException("Region edit authority is required to save this part of the world map.");

        var authority = await GetClaimAuthorityClientAsync();
        if (authority is null)
            throw new InvalidOperationException("World map database authority is unavailable.");

        return await authority.SaveWorldRegionMapAsync(WorldId, region.RegionId, userLayers);
    }

    public async Task<AwsAuthorityClient.WorldSource?> SaveWorldBuilderSourceAsync(JsonElement state)
    {
        if (!HasWorldBuilderEditAuthority)
            throw new UnauthorizedAccessException("World Builder authority is required to save the canonical world map.");
        if (!HasActiveWorld)
            throw new InvalidOperationException("Choose a world before saving the shared world source.");
        if (state.ValueKind != JsonValueKind.Object)
            throw new InvalidOperationException("World map state must be an object.");

        if (state.TryGetProperty("worldId", out var stateWorldId))
        {
            var value = stateWorldId.GetString()?.Trim() ?? "";
            if (value.Length > 0 && !string.Equals(value, WorldId, StringComparison.Ordinal))
                throw new InvalidOperationException("World map identity does not match the active world.");
        }

        var worldId = WorldId;
        var accountId = WorldOwnerAccountId;
        var token = auth.SessionToken;
        var privateOwner = await HasOwnedPrivateWorldDescriptorAsync(worldId, accountId);
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

        return await authority.SaveWorldSourceAsync(WorldId, state);
    }
}
