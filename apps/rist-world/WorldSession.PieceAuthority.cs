namespace RistWorld;

public sealed partial class WorldSession
{
    AwsAuthorityClient? _pieceAuthorityClient;
    bool _pieceAuthorityInitialized;
    readonly SemaphoreSlim _pieceAuthorityGate = new(1, 1);

    public sealed record PieceMutationResult(bool Success, string Message);

    async Task<AwsAuthorityClient?> GetPieceAuthorityClientAsync()
    {
        _pieceAuthorityClient ??= new AwsAuthorityClient(http, auth);
        if (!_pieceAuthorityInitialized)
        {
            await _pieceAuthorityClient.InitializeAsync();
            _pieceAuthorityInitialized = true;
        }
        return _pieceAuthorityClient.IsConfigured ? _pieceAuthorityClient : null;
    }

    PieceItem EnsurePieceAuthorityIdentity(PieceItem piece)
    {
        var index = Pieces.IndexOf(piece);
        if (index < 0) return piece;
        if (!string.IsNullOrWhiteSpace(piece.PieceId)) return piece;

        var identified = piece with { PieceId = Guid.NewGuid().ToString("N") };
        Pieces[index] = identified;
        Notify();
        return identified;
    }

    object PieceAuthorityPayload(PieceItem piece, double x, double y, bool removed = false) => new
    {
        entityType = "piece",
        pieceId = piece.PieceId,
        kind = piece.Kind,
        label = piece.Label,
        x = Math.Clamp(x, 0, 1),
        y = Math.Clamp(y, 0, 1),
        placementZoom = Math.Max(piece.PlacementZoom, .01),
        cubeX = piece.CubeX,
        cubeY = piece.CubeY,
        cubeZ = piece.CubeZ,
        planeIndex = piece.PlaneIndex,
        tierIndex = piece.TierIndex,
        layerOffset = piece.LayerOffset,
        removed
    };

    // Shared authority boundary for every UI that moves a piece. Offline/local worlds
    // retain local tabletop behavior. Authenticated worlds must be accepted by the AWS
    // authority endpoint before client truth is changed.
    public async Task<PieceMutationResult> MovePieceAuthorizedAsync(PieceItem piece, double x, double y)
    {
        var index = Pieces.IndexOf(piece);
        if (index < 0) return new(false, "That piece is no longer present.");

        x = Math.Clamp(x, 0, 1);
        y = Math.Clamp(y, 0, 1);

        if (!IsLoggedIn || !HasActiveWorld)
        {
            MovePiece(piece, x, y);
            return new(true, "Piece moved in the local world.");
        }

        await _pieceAuthorityGate.WaitAsync();
        try
        {
            piece = EnsurePieceAuthorityIdentity(piece);
            index = Pieces.IndexOf(piece);
            if (index < 0) return new(false, "That piece is no longer present.");

            var authority = await GetPieceAuthorityClientAsync();
            if (authority is null)
                return new(false, "Piece movement is locked because server authority is unavailable.");

            var entityId = $"piece-{piece.PieceId}";
            AwsAuthorityClient.WorldEntity? updated;
            try
            {
                updated = await authority.MutateAsync(
                    WorldId,
                    entityId,
                    "piece.move",
                    PieceAuthorityPayload(piece, x, y),
                    piece.AuthorityVersion,
                    string.IsNullOrWhiteSpace(piece.OwnerUserId) ? auth.Profile?.UserId : piece.OwnerUserId);
            }
            catch (HttpRequestException)
            {
                return new(false, "Piece movement was rejected because the server copy changed. Reload the world and try again.");
            }

            if (updated is null)
                return new(false, "You do not have authority to move that piece.");

            var owner = string.IsNullOrWhiteSpace(updated.OwnerUserId) ? piece.OwnerUserId : updated.OwnerUserId;
            Pieces[index] = piece with
            {
                X = x,
                Y = y,
                OwnerUserId = owner,
                AuthorityVersion = updated.Version
            };
            Notify();
            return new(true, "Piece move authorized and committed.");
        }
        finally
        {
            _pieceAuthorityGate.Release();
        }
    }

    public async Task<PieceMutationResult> RemovePieceAuthorizedAsync(PieceItem piece)
    {
        var index = Pieces.IndexOf(piece);
        if (index < 0) return new(false, "That piece is no longer present.");

        if (!IsLoggedIn || !HasActiveWorld)
        {
            RemovePiece(piece);
            return new(true, "Piece removed from the local world.");
        }

        await _pieceAuthorityGate.WaitAsync();
        try
        {
            piece = EnsurePieceAuthorityIdentity(piece);
            index = Pieces.IndexOf(piece);
            if (index < 0) return new(false, "That piece is no longer present.");

            var authority = await GetPieceAuthorityClientAsync();
            if (authority is null)
                return new(false, "Piece removal is locked because server authority is unavailable.");

            AwsAuthorityClient.WorldEntity? updated;
            try
            {
                updated = await authority.MutateAsync(
                    WorldId,
                    $"piece-{piece.PieceId}",
                    "piece.remove",
                    PieceAuthorityPayload(piece, piece.X, piece.Y, removed: true),
                    piece.AuthorityVersion,
                    string.IsNullOrWhiteSpace(piece.OwnerUserId) ? auth.Profile?.UserId : piece.OwnerUserId);
            }
            catch (HttpRequestException)
            {
                return new(false, "Piece removal was rejected because the server copy changed. Reload the world and try again.");
            }

            if (updated is null)
                return new(false, "You do not have authority to remove that piece.");

            Pieces.RemoveAt(index);
            Notify();
            return new(true, "Piece removal authorized and committed.");
        }
        finally
        {
            _pieceAuthorityGate.Release();
        }
    }
}
