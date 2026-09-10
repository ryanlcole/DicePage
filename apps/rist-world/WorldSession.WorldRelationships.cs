using System.Text.Json;

namespace RistWorld;

public sealed partial class WorldSession
{
    public string WorldDirectoryKey => $"{WorldsStoragePrefix}/index.json";
    public string WorldDescriptorKey => $"{WorldStoragePrefix}/world.json";

    public async Task EnsureWorldRelationshipAsync()
    {
        if (!IsLoggedIn) return;

        var accountId = WorldOwnerAccountId?.Trim() ?? "";
        if (accountId.Length == 0)
            throw new InvalidOperationException("The authenticated RIST account has no Account ID.");

        var now = DateTimeOffset.UtcNow;
        var descriptor = await auth.DownloadJsonAsync<WorldRelationshipDescriptor>(WorldDescriptorKey);
        if (descriptor is not null)
        {
            if (!string.Equals(descriptor.WorldId, WorldId, StringComparison.Ordinal))
                throw new InvalidOperationException("World descriptor identity does not match the active World ID.");
            if (!string.Equals(descriptor.OwnerAccountId, accountId, StringComparison.Ordinal))
                throw new InvalidOperationException("World ownership does not match the authenticated account.");
        }

        descriptor = descriptor is null
            ? new WorldRelationshipDescriptor(
                WorldId,
                accountId,
                WorldDisplayName,
                "Shaelvien",
                "active",
                now,
                now)
            : descriptor with
            {
                DisplayName = WorldDisplayName,
                UpdatedAtUtc = now
            };

        await auth.UploadTextAsync(
            WorldDescriptorKey,
            JsonSerializer.Serialize(descriptor, MapWriteOptions),
            "application/json");

        var directory = await auth.DownloadJsonAsync<AccountWorldDirectory>(WorldDirectoryKey);
        if (directory is not null &&
            !string.IsNullOrWhiteSpace(directory.AccountId) &&
            !string.Equals(directory.AccountId, accountId, StringComparison.Ordinal))
            throw new InvalidOperationException("World directory ownership does not match the authenticated account.");

        var worlds = (directory?.Worlds ?? [])
            .Where(world => !string.IsNullOrWhiteSpace(world.WorldId))
            .GroupBy(world => world.WorldId, StringComparer.Ordinal)
            .Select(group => group.First())
            .Where(world => !string.Equals(world.WorldId, WorldId, StringComparison.Ordinal))
            .ToList();

        worlds.Add(new AccountWorldReference(
            WorldId,
            WorldDisplayName,
            "owner",
            WorldDescriptorKey,
            WorldCheckpointKey,
            now));

        var nextDirectory = new AccountWorldDirectory(
            accountId,
            WorldId,
            worlds.OrderBy(world => world.WorldId, StringComparer.Ordinal).ToList(),
            now);

        await auth.UploadTextAsync(
            WorldDirectoryKey,
            JsonSerializer.Serialize(nextDirectory, MapWriteOptions),
            "application/json");
    }
}

public sealed record AccountWorldDirectory(
    string AccountId,
    string ActiveWorldId,
    List<AccountWorldReference> Worlds,
    DateTimeOffset UpdatedAtUtc);

public sealed record AccountWorldReference(
    string WorldId,
    string DisplayName,
    string Relationship,
    string DescriptorKey,
    string CheckpointKey,
    DateTimeOffset UpdatedAtUtc);

public sealed record WorldRelationshipDescriptor(
    string WorldId,
    string OwnerAccountId,
    string DisplayName,
    string Domain,
    string Status,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc);
