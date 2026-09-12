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

        // Only the configured developer account, or an account already bound by a
        // persisted Geonaph descriptor, may establish/refresh Geonaph ownership.
        await EnsureGeonaphOwnerBootstrapAsync(accountId);

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

        // Geonaph remains discoverable to accounts that already possess a legacy
        // migration artifact, but only the bound owner receives owner authority.
        if (worlds.All(x => !string.Equals(x.WorldId, GeonaphWorldId, StringComparison.Ordinal)))
        {
            var legacyDescriptor = await auth.DownloadJsonAsync<WorldRelationshipDescriptor>(
                $"{WorldsStoragePrefix}/{GeonaphWorldId}/world.json");
            var legacySave = await auth.DownloadJsonAsync<SavedWorld>(
                $"{WorldsStoragePrefix}/{GeonaphWorldId}/current.ristmap");
            legacySave ??= await auth.DownloadJsonAsync<SavedWorld>(LegacyPrivateWorldCheckpointKey);

            var ownsGeonaph = auth.IsOwnerDiscordAccount ||
                              (legacyDescriptor is not null &&
                               string.Equals(legacyDescriptor.OwnerAccountId, accountId, StringComparison.Ordinal));

            if (ownsGeonaph || legacyDescriptor is not null || legacySave is not null)
            {
                var name = ownsGeonaph ? GeonaphDisplayName : legacyDescriptor?.DisplayName;
                if (string.IsNullOrWhiteSpace(name)) name = legacySave?.WorldName;
                if (string.IsNullOrWhiteSpace(name)) name = GeonaphDisplayName;
                worlds.Add(new AccountWorldReference(
                    GeonaphWorldId,
                    name!,
                    ownsGeonaph ? "owner" : "participant",
                    $"{WorldsStoragePrefix}/{GeonaphWorldId}/world.json",
                    $"{WorldsStoragePrefix}/{GeonaphWorldId}/current.ristmap",
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
        var accountId = WorldOwnerAccountId?.Trim() ?? "";

        if (HasActiveWorld && !string.Equals(WorldId, world.WorldId, StringComparison.Ordinal))
        {
            // A participant may leave Geonaph without attempting an owner-only write.
            var currentReadOnlyGeonaph = IsGeonaphWorld && !await HasGeonaphOwnerAuthorityAsync(accountId);
            if (!currentReadOnlyGeonaph)
                await AutoSavePrivateAsync();
        }

        SetActiveWorldIdentity(world.WorldId, displayName);

        if (IsGeonaphWorld && !await HasGeonaphOwnerAuthorityAsync(accountId))
        {
            // Geonaph is public/readable even when its mutation authority belongs to
            // another account. Build the canonical production chunk locally rather
            // than routing a participant through owner relationship writes.
            ResetToCanonicalOrigin();
            EnsureGianaphWorld();
            return;
        }

        await LoadPrivateCheckpointAsync();
        if (IsGeonaphWorld)
            EnsureGianaphWorld();
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
        var persistedGeonaphOwner = descriptor is not null &&
                                    string.Equals(descriptor.WorldId, GeonaphWorldId, StringComparison.Ordinal) &&
                                    string.Equals(descriptor.OwnerAccountId, accountId, StringComparison.Ordinal);
        if (IsGeonaphWorld && !auth.IsOwnerDiscordAccount && !persistedGeonaphOwner)
            throw new InvalidOperationException("Geonaph owner authority is reserved for the configured developer account.");

        if (descriptor is not null)
        {
            if (!string.Equals(descriptor.WorldId, WorldId, StringComparison.Ordinal))
                throw new InvalidOperationException("World descriptor identity does not match the active World ID.");
            if (!string.IsNullOrWhiteSpace(descriptor.OwnerAccountId) &&
                !string.Equals(descriptor.OwnerAccountId, accountId, StringComparison.Ordinal))
                throw new InvalidOperationException("World ownership does not match the authenticated account.");
        }

        var extentMode = IsWorldExtentUnbounded ? "unbounded" : "bounded";
        var maxTilesX = IsWorldExtentUnbounded ? null : WorldTileLimit;
        var maxTilesY = IsWorldExtentUnbounded ? null : WorldTileLimit;
        var authoritySpatialAddress = IsGeonaphWorld ? GeonaphOriginAuthoritySpatialAddress : descriptor?.AuthoritySpatialAddress ?? "";
        var authorityRole = IsGeonaphWorld ? GeonaphOriginAuthorityRole : descriptor?.AuthorityRole ?? "";
        descriptor = descriptor is null
            ? new WorldRelationshipDescriptor(
                WorldId,
                accountId,
                WorldDisplayName,
                "Shaelvien",
                "active",
                now,
                now,
                extentMode,
                maxTilesX,
                maxTilesY,
                authoritySpatialAddress,
                authorityRole)
            : descriptor with
            {
                OwnerAccountId = accountId,
                DisplayName = WorldDisplayName,
                UpdatedAtUtc = now,
                ExtentMode = extentMode,
                MaxTilesX = maxTilesX,
                MaxTilesY = maxTilesY,
                AuthoritySpatialAddress = authoritySpatialAddress,
                AuthorityRole = authorityRole
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

    async Task<bool> HasGeonaphOwnerAuthorityAsync(string accountId)
    {
        if (!IsGeonaphWorld || accountId.Length == 0) return false;
        if (auth.IsOwnerDiscordAccount) return true;

        var descriptor = await auth.DownloadJsonAsync<WorldRelationshipDescriptor>(WorldDescriptorKey);
        return descriptor is not null &&
               string.Equals(descriptor.WorldId, GeonaphWorldId, StringComparison.Ordinal) &&
               string.Equals(descriptor.OwnerAccountId, accountId, StringComparison.Ordinal);
    }

    async Task EnsureGeonaphOwnerBootstrapAsync(string accountId)
    {
        var descriptorKey = $"{WorldsStoragePrefix}/{GeonaphWorldId}/world.json";
        var checkpointKey = $"{WorldsStoragePrefix}/{GeonaphWorldId}/current.ristmap";
        var now = DateTimeOffset.UtcNow;
        var descriptor = await auth.DownloadJsonAsync<WorldRelationshipDescriptor>(descriptorKey);
        var persistedOwner = descriptor is not null &&
                             string.Equals(descriptor.WorldId, GeonaphWorldId, StringComparison.Ordinal) &&
                             string.Equals(descriptor.OwnerAccountId, accountId, StringComparison.Ordinal);

        // A missing static owner ID must not lock an already-bound developer account
        // out of its own world. Persisted ownership is authoritative for migration.
        if (!auth.IsOwnerDiscordAccount && !persistedOwner) return;

        if (descriptor is not null)
        {
            if (!string.Equals(descriptor.WorldId, GeonaphWorldId, StringComparison.Ordinal))
                throw new InvalidOperationException("Geonaph descriptor identity does not match the canonical World ID.");
            if (!string.IsNullOrWhiteSpace(descriptor.OwnerAccountId) &&
                !string.Equals(descriptor.OwnerAccountId, accountId, StringComparison.Ordinal))
                throw new InvalidOperationException("Geonaph is already bound to a different RIST account.");
        }

        descriptor = descriptor is null
            ? new WorldRelationshipDescriptor(
                GeonaphWorldId,
                accountId,
                GeonaphDisplayName,
                "Shaelvien",
                "active",
                now,
                now,
                "unbounded",
                null,
                null,
                GeonaphOriginAuthoritySpatialAddress,
                GeonaphOriginAuthorityRole)
            : descriptor with
            {
                OwnerAccountId = accountId,
                DisplayName = GeonaphDisplayName,
                Domain = "Shaelvien",
                Status = "active",
                UpdatedAtUtc = now,
                ExtentMode = "unbounded",
                MaxTilesX = null,
                MaxTilesY = null,
                AuthoritySpatialAddress = GeonaphOriginAuthoritySpatialAddress,
                AuthorityRole = GeonaphOriginAuthorityRole
            };

        await auth.UploadTextAsync(
            descriptorKey,
            JsonSerializer.Serialize(descriptor, MapWriteOptions),
            "application/json");

        // Never overwrite an existing world. Only create the canonical sparse sea-level
        // seed when neither the World-ID checkpoint nor the legacy migration checkpoint exists.
        var checkpoint = await auth.DownloadJsonAsync<SavedWorld>(checkpointKey);
        if (checkpoint is not null) return;
        var legacyCheckpoint = await auth.DownloadJsonAsync<SavedWorld>(LegacyPrivateWorldCheckpointKey);
        if (legacyCheckpoint is not null) return;

        await auth.UploadTextAsync(
            checkpointKey,
            JsonSerializer.Serialize(CreateGeonaphOriginSeed(), MapWriteOptions),
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
    DateTimeOffset UpdatedAtUtc,
    string ExtentMode = "bounded",
    int? MaxTilesX = null,
    int? MaxTilesY = null,
    string AuthoritySpatialAddress = "",
    string AuthorityRole = "");
