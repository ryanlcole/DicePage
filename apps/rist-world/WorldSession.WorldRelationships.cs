using System.Text.Json;

namespace RistWorld;

public sealed partial class WorldSession
{
    public string WorldDirectoryKey => $"{WorldsStoragePrefix}/index.json";
    public string WorldDescriptorKey => $"{WorldStoragePrefix}/world.json";

    public async Task<AccountWorldDirectory> LoadWorldDirectoryAsync()
    {
        if (!IsLoggedIn)
            return new AccountWorldDirectory("", "", [], DateTimeOffset.UtcNow);

        var accountId = WorldOwnerAccountId?.Trim() ?? "";
        if (accountId.Length == 0)
            throw new InvalidOperationException("The authenticated RIST account has no Account ID.");

        var directory = await auth.DownloadJsonAsync<AccountWorldDirectory>(WorldDirectoryKey);
        if (directory is not null &&
            !string.IsNullOrWhiteSpace(directory.AccountId) &&
            !string.Equals(directory.AccountId, accountId, StringComparison.Ordinal))
            throw new InvalidOperationException("World directory ownership does not match the authenticated account.");

        var worlds = (directory?.Worlds ?? [])
            .Where(world => !string.IsNullOrWhiteSpace(world.WorldId))
            .GroupBy(world => world.WorldId, StringComparer.Ordinal)
            .Select(group => group.OrderByDescending(x => x.UpdatedAtUtc).First())
            .ToList();

        // Discovery/migration for accounts created before the world directory existed.
        if (worlds.All(x => !string.Equals(x.WorldId, LegacyAlphaWorldId, StringComparison.Ordinal)))
        {
            var legacyDescriptor = await auth.DownloadJsonAsync<WorldRelationshipDescriptor>(
                $"{WorldsStoragePrefix}/{LegacyAlphaWorldId}/world.json");
            var legacySave = await auth.DownloadJsonAsync<SavedWorld>(
                $"{WorldsStoragePrefix}/{LegacyAlphaWorldId}/current.ristmap");
            legacySave ??= await auth.DownloadJsonAsync<SavedWorld>(LegacyPrivateWorldCheckpointKey);

            if (legacyDescriptor is not null || legacySave is not null)
            {
                var name = legacyDescriptor?.DisplayName;
                if (string.IsNullOrWhiteSpace(name)) name = legacySave?.WorldName;
                if (string.IsNullOrWhiteSpace(name)) name = "Shaelvien";
                worlds.Add(new AccountWorldReference(
                    LegacyAlphaWorldId,
                    name!,
                    "owner",
                    $"{WorldsStoragePrefix}/{LegacyAlphaWorldId}/world.json",
                    $"{WorldsStoragePrefix}/{LegacyAlphaWorldId}/current.ristmap",
                    legacyDescriptor?.UpdatedAtUtc ?? DateTimeOffset.UtcNow));
            }
        }

        return new AccountWorldDirectory(
            accountId,
            directory?.ActiveWorldId ?? "",
            worlds.OrderByDescending(world => world.UpdatedAtUtc).ThenBy(world => world.DisplayName, StringComparer.OrdinalIgnoreCase).ToList(),
            directory?.UpdatedAtUtc ?? DateTimeOffset.UtcNow);
    }

    public async Task<AccountWorldReference> CreateWorldAsync(string worldName)
    {
        var displayName = NormalizeWorldName(worldName);
        if (HasActiveWorld) await AutoSavePrivateAsync();

        var worldId = NewWorldId(displayName);
        SetActiveWorldIdentity(worldId, displayName);
        ResetToCanonicalOrigin();
        await SavePrivateCheckpointAsync(showSuccess: false);
        await EnsureWorldRelationshipAsync();

        return new AccountWorldReference(
            WorldId, WorldDisplayName, "owner", WorldDescriptorKey, WorldCheckpointKey, DateTimeOffset.UtcNow);
    }

    public async Task LoadWorldAsync(AccountWorldReference world)
    {
        if (world is null || string.IsNullOrWhiteSpace(world.WorldId))
            throw new InvalidOperationException("Choose a valid world.");
        var displayName = NormalizeWorldName(world.DisplayName);
        if (HasActiveWorld && !string.Equals(WorldId, world.WorldId, StringComparison.Ordinal))
            await AutoSavePrivateAsync();

        SetActiveWorldIdentity(world.WorldId, displayName);
        await LoadPrivateCheckpointAsync();
    }

    public async Task<AccountWorldReference> ImportWorldAsync(string json, string? preferredName = null)
    {
        if (string.IsNullOrWhiteSpace(json)) throw new InvalidOperationException("The imported world file is empty.");
        using (var document = JsonDocument.Parse(json))
        {
            if (!document.RootElement.TryGetProperty("Format", out var format) ||
                !string.Equals(format.GetString(), "RISTMAP", StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException("This file is not a RIST world export.");
        }

        var imported = JsonSerializer.Deserialize<SavedWorld>(json, MapReadOptions)
            ?? throw new InvalidOperationException("The imported world could not be read.");
        var displayName = !string.IsNullOrWhiteSpace(preferredName)
            ? NormalizeWorldName(preferredName)
            : !string.IsNullOrWhiteSpace(imported.WorldName)
                ? NormalizeWorldName(imported.WorldName)
                : "Imported World";

        if (HasActiveWorld) await AutoSavePrivateAsync();
        var worldId = NewWorldId(displayName);
        SetActiveWorldIdentity(worldId, displayName);
        ResetToCanonicalOrigin();
        imported.WorldId = worldId;
        imported.WorldName = displayName;
        LoadMapJson(JsonSerializer.Serialize(imported, MapWriteOptions));
        await SavePrivateCheckpointAsync(showSuccess: false);
        await EnsureWorldRelationshipAsync();

        return new AccountWorldReference(
            WorldId, WorldDisplayName, "owner", WorldDescriptorKey, WorldCheckpointKey, DateTimeOffset.UtcNow);
    }

    public async Task EnsureWorldRelationshipAsync()
    {
        if (!IsLoggedIn || !HasActiveWorld) return;

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

    static string NormalizeWorldName(string? name)
    {
        var value = (name ?? "").Trim();
        if (value.Length == 0) throw new InvalidOperationException("Enter a World Name.");
        if (value.Length > 80) throw new InvalidOperationException("World Name must be 80 characters or fewer.");
        return value;
    }

    static string NewWorldId(string displayName)
    {
        var chars = displayName.ToLowerInvariant().Select(c => c is >= 'a' and <= 'z' or >= '0' and <= '9' ? c : '-').ToArray();
        var slug = new string(chars);
        while (slug.Contains("--", StringComparison.Ordinal)) slug = slug.Replace("--", "-", StringComparison.Ordinal);
        slug = slug.Trim('-');
        if (slug.Length == 0) slug = "world";
        if (slug.Length > 36) slug = slug[..36].TrimEnd('-');
        return $"{slug}-{Guid.NewGuid():N}"[..Math.Min(slug.Length + 1 + 12, slug.Length + 1 + 32)];
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
