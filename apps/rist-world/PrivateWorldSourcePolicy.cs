namespace RistWorld;

// A private-storage descriptor authorizes only that account's isolated namespace.
// It never grants a shared-world membership or authority over Shaelvien.
public static class PrivateWorldSourcePolicy
{
    public static bool MatchesOwner(string worldId, string accountId, string? savedWorldId, string? savedOwnerId) =>
        !string.IsNullOrWhiteSpace(worldId)
        && !string.Equals(worldId, "shaelvien-geonaph-alpha-001", StringComparison.Ordinal)
        && !string.IsNullOrWhiteSpace(accountId)
        && string.Equals(worldId, savedWorldId, StringComparison.Ordinal)
        && string.Equals(accountId, savedOwnerId, StringComparison.Ordinal);
}
