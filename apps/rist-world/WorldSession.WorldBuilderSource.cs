using System.Text.Json;

namespace RistWorld;

public sealed partial class WorldSession
{
    public async Task<AwsAuthorityClient.WorldSource?> LoadWorldBuilderSourceAsync()
    {
        if (!IsLoggedIn || !HasActiveWorld) return null;
        var authority = await GetClaimAuthorityClientAsync();
        return authority is null ? null : await authority.GetWorldSourceAsync(WorldId);
    }

    public async Task<AwsAuthorityClient.WorldSource?> SaveWorldBuilderSourceAsync(JsonElement state)
    {
        if (!HasTrustedWorldBuilderAuthority)
            throw new UnauthorizedAccessException("World Builder authority is required to save the shared world source.");
        if (!HasActiveWorld)
            throw new InvalidOperationException("Choose a world before saving the shared world source.");
        if (state.ValueKind != JsonValueKind.Object)
            throw new InvalidOperationException("World source state must be an object.");

        if (state.TryGetProperty("worldId", out var stateWorldId))
        {
            var value = stateWorldId.GetString()?.Trim() ?? "";
            if (value.Length > 0 && !string.Equals(value, WorldId, StringComparison.Ordinal))
                throw new InvalidOperationException("World source identity does not match the active world.");
        }

        var authority = await GetClaimAuthorityClientAsync();
        if (authority is null)
            throw new InvalidOperationException("World source database authority is unavailable.");

        return await authority.SaveWorldSourceAsync(WorldId, state);
    }
}
