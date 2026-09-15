namespace RistWorld;

public sealed partial class WorldSession
{
    public sealed record TileMutationResult(bool Success, string Message, TileItem? Tile = null);

    TileItem BuildStagedTile(StagedAsset staged, double x, double y, double placementZoom)
    {
        var footprint = staged.DefaultFootprint > 0
            ? staged.DefaultFootprint
            : 1.0 / Math.Max(placementZoom, .01);
        return new TileItem(
            staged.Key.StartsWith("tile:", StringComparison.Ordinal) ? staged.Key[5..] : staged.Key,
            staged.Name,
            staged.Image,
            Math.Clamp(x, 0, 1),
            Math.Clamp(y, 0, 1),
            staged.SourceWidth,
            staged.SourceHeight,
            staged.CropX,
            staged.CropY,
            staged.CropWidth,
            staged.CropHeight,
            1.0 / Math.Max(footprint, .01))
        {
            CubeX = CubeX,
            CubeY = CubeY,
            CubeZ = CubeZ,
            PlaneIndex = PlaneIndex,
            TierIndex = staged.AuthoredDepth ? staged.DefaultTierIndex : TierIndex,
            LayerOffset = staged.AuthoredDepth ? staged.DefaultLayerOffset : LayerOffset,
            AssetKind = staged.AssetKind,
            AuthoredDepth = staged.AuthoredDepth,
            FrameCount = Math.Max(1, staged.FrameCount),
            FramesPerSecond = Math.Max(0, staged.FramesPerSecond)
        };
    }

    object TileAuthorityPayload(TileItem tile) => new
    {
        entityType = "tile",
        placementId = tile.PlacementId,
        assetId = tile.Id,
        name = tile.Name,
        typeId = GetTileTypeId(tile),
        assetKind = tile.AssetKind,
        shaepId = tile.ShaepId,
        authoredDepth = tile.AuthoredDepth,
        x = Math.Clamp(tile.X, 0, 1),
        y = Math.Clamp(tile.Y, 0, 1),
        placementZoom = Math.Clamp(tile.PlacementZoom, 1.0 / 1_000_000.0, 300),
        cubeX = tile.CubeX,
        cubeY = tile.CubeY,
        cubeZ = tile.CubeZ,
        planeIndex = tile.PlaneIndex,
        tierIndex = tile.TierIndex,
        layerOffset = tile.LayerOffset,
        rotationQuarterTurns = Math.Clamp(tile.RotationQuarterTurns, 0, 3),
        placementTreatment = tile.PlacementTreatment,
        zoneId = tile.ZoneId,
        zoneLabel = tile.ZoneLabel,
        locked = tile.Locked
    };

    TileItem WithTileAuthority(TileItem tile, AwsAuthorityClient.WorldEntity updated)
    {
        var owner = string.IsNullOrWhiteSpace(updated.OwnerUserId) ? tile.OwnerUserId : updated.OwnerUserId;
        return tile with { OwnerUserId = owner, AuthorityVersion = updated.Version };
    }

    async Task<(AwsAuthorityClient.WorldEntity? Entity, string? Error)> MutateTileServerAsync(
        TileItem tile,
        string action,
        long expectedVersion)
    {
        var authority = await GetPieceAuthorityClientAsync();
        if (authority is null)
            return (null, "Tile editing is locked because server authority is unavailable.");

        try
        {
            var updated = await authority.MutateAsync(
                WorldId,
                tile.PlacementId,
                action,
                TileAuthorityPayload(tile),
                expectedVersion,
                string.IsNullOrWhiteSpace(tile.OwnerUserId) ? auth.Profile?.UserId : tile.OwnerUserId);
            return updated is null
                ? (null, "You do not have authority to change that tile.")
                : (updated, null);
        }
        catch (HttpRequestException)
        {
            return (null, "Tile change was rejected because the server copy changed. Reload the world and try again.");
        }
    }

    public async Task<TileMutationResult> CreateTileAuthorizedAsync(TileItem tile)
    {
        var identified = NormalizePlacedTileIdentity(tile);
        if (!IsLoggedIn || !HasActiveWorld)
        {
            PlacedTiles.Add(identified);
            RecordPureStateCommit();
            Notify();
            return new(true, "Tile placed in the local world.", identified);
        }

        await _pieceAuthorityGate.WaitAsync();
        try
        {
            var (updated, error) = await MutateTileServerAsync(identified, "tile.create", 0);
            if (updated is null) return new(false, error ?? "Tile placement was not authorized.");

            var committed = WithTileAuthority(identified, updated);
            PlacedTiles.Add(committed);
            RecordPureStateCommit();
            Notify();
            return new(true, "Tile placement authorized and committed.", committed);
        }
        finally
        {
            _pieceAuthorityGate.Release();
        }
    }

    public async Task<TileMutationResult> UpdateTileAuthorizedAsync(TileItem tile, TileItem next)
    {
        var index = PlacedTiles.IndexOf(tile);
        if (index < 0) return new(false, "That tile is no longer present.");
        if (!CanEditTiles || tile.Locked && !next.Locked)
            return new(false, "That tile is locked.");

        var identified = NormalizePlacedTileIdentity(tile);
        next = next with
        {
            PlacementId = identified.PlacementId,
            OwnerUserId = identified.OwnerUserId,
            AuthorityVersion = identified.AuthorityVersion
        };

        if (!IsLoggedIn || !HasActiveWorld)
        {
            PlacedTiles[index] = next;
            RecordPureStateCommit();
            Notify();
            return new(true, "Tile changed in the local world.", next);
        }

        await _pieceAuthorityGate.WaitAsync();
        try
        {
            var action = identified.AuthorityVersion == 0 ? "tile.create" : "tile.update";
            var expected = identified.AuthorityVersion;
            var (updated, error) = await MutateTileServerAsync(next, action, expected);
            if (updated is null) return new(false, error ?? "Tile change was not authorized.");

            var committed = WithTileAuthority(next, updated);
            index = PlacedTiles.IndexOf(tile);
            if (index < 0) return new(false, "That tile changed locally before the server commit completed.");
            PlacedTiles[index] = committed;
            RecordPureStateCommit();
            Notify();
            return new(true, "Tile change authorized and committed.", committed);
        }
        finally
        {
            _pieceAuthorityGate.Release();
        }
    }

    public Task<TileMutationResult> MoveTileAuthorizedAsync(TileItem tile, double x, double y) =>
        UpdateTileAuthorizedAsync(tile, tile with { X = Math.Clamp(x, 0, 1), Y = Math.Clamp(y, 0, 1) });

    public async Task<TileMutationResult> RemoveTileAuthorizedAsync(TileItem tile)
    {
        var index = PlacedTiles.IndexOf(tile);
        if (index < 0) return new(false, "That tile is no longer present.");
        if (!CanEditTiles || tile.Locked) return new(false, "That tile is locked.");

        var identified = NormalizePlacedTileIdentity(tile);
        if (!IsLoggedIn || !HasActiveWorld)
        {
            PlacedTiles.RemoveAt(index);
            RecordPureStateCommit();
            Notify();
            return new(true, "Tile removed from the local world.");
        }

        await _pieceAuthorityGate.WaitAsync();
        try
        {
            if (identified.AuthorityVersion == 0)
            {
                var (adopted, adoptError) = await MutateTileServerAsync(identified, "tile.create", 0);
                if (adopted is null) return new(false, adoptError ?? "Tile could not be adopted by server authority.");
                identified = WithTileAuthority(identified, adopted);
            }

            var (removed, error) = await MutateTileServerAsync(identified, "tile.remove", identified.AuthorityVersion);
            if (removed is null) return new(false, error ?? "Tile removal was not authorized.");

            index = PlacedTiles.IndexOf(tile);
            if (index < 0) return new(false, "That tile changed locally before the server commit completed.");
            PlacedTiles.RemoveAt(index);
            RecordPureStateCommit();
            Notify();
            return new(true, "Tile removal authorized and committed.");
        }
        finally
        {
            _pieceAuthorityGate.Release();
        }
    }

    public Task<TileMutationResult> PlaceStagedTileAuthorizedAsync(
        StagedAsset staged,
        double x,
        double y,
        double placementZoom)
    {
        if (staged.Kind != "tile")
            return Task.FromResult(new TileMutationResult(false, "The staged asset is not a tile."));
        if (Role == "PC" && staged.ApprovalStatus != HandCard.Approved)
            return Task.FromResult(new TileMutationResult(false, $"{staged.Name} is awaiting GameMaster approval."));
        if (!CanEditTiles)
            return Task.FromResult(new TileMutationResult(false, "Tile placement requires GameMaster worldbuilder authority."));
        return CreateTileAuthorizedAsync(BuildStagedTile(staged, x, y, placementZoom));
    }

    public Task<TileMutationResult> PlaceAbmTileAuthorizedAsync(
        AssetByMetadata metadata,
        double x,
        double y,
        double placementZoom = 1.0) =>
        CreateTileAuthorizedAsync(CreateAbmTile(metadata, x, y, placementZoom));
}
