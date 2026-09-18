namespace RistWorld;

public sealed partial class WorldSession
{
    AwsAuthorityClient? _claimAuthorityClient;
    bool _claimAuthorityInitialized;
    readonly SemaphoreSlim _claimAuthorityGate = new(1, 1);

    public sealed record WorldClaimSubmissionResult(
        bool Success,
        string Message,
        AwsAuthorityClient.WorldClaimRequest? Request = null);

    async Task<AwsAuthorityClient?> GetClaimAuthorityClientAsync()
    {
        _claimAuthorityClient ??= new AwsAuthorityClient(http, auth);
        if (!_claimAuthorityInitialized)
        {
            await _claimAuthorityClient.InitializeAsync();
            _claimAuthorityInitialized = true;
        }
        return _claimAuthorityClient.IsConfigured ? _claimAuthorityClient : null;
    }

    public async Task<WorldClaimSubmissionResult> SubmitWorldClaimRequestAsync(
        string workspace,
        int tierIndex,
        IEnumerable<int> selectedCells,
        IEnumerable<int> sourceLayerOffsets,
        string gridShape,
        string requestedResourceId = "")
    {
        if (!IsLoggedIn || !HasActiveWorld)
            return new(false, "Log in and choose a world before requesting a claim.");
        if (HasTrustedWorldBuilderAuthority)
            return new(false, "This account already has direct world-building authority.");
        if (!CanRequestWorldClaim)
            return new(false, "Claim requests are blocked for this world membership.");

        var requesterUserId = auth.Profile?.UserId?.Trim() ?? "";
        if (requesterUserId.Length == 0)
            return new(false, "The authenticated user identity could not be verified.");

        var cells = (selectedCells ?? [])
            .Where(cell => cell >= 0 && cell < GridColumns * GridRows)
            .Distinct()
            .Order()
            .ToList();
        if (cells.Count == 0)
            return new(false, "Select at least one map tile before requesting a claim.");

        var layers = (sourceLayerOffsets ?? [])
            .Where(layer => layer >= 0 && layer < LayersPerTier)
            .Distinct()
            .Order()
            .ToList();
        if (layers.Count == 0)
            return new(false, "Select at least one source layer before requesting a claim.");

        tierIndex = Math.Clamp(tierIndex, 0, 2);
        gridShape = string.Equals(gridShape, "hex", StringComparison.OrdinalIgnoreCase) ? "hex" : "square";
        workspace = string.Equals(workspace, "worldbuilder", StringComparison.OrdinalIgnoreCase)
            ? "worldbuilder"
            : "regiondefiner";

        await _claimAuthorityGate.WaitAsync();
        try
        {
            var client = await GetClaimAuthorityClientAsync();
            if (client is null)
                return new(false, "Claim requests are unavailable because server authority is offline.");

            AwsAuthorityClient.WorldClaimRequest? request;
            try
            {
                request = await client.SubmitClaimRequestAsync(new AwsAuthorityClient.WorldClaimRequestCreate(
                    WorldId,
                    requesterUserId,
                    auth.Account?.PlayerAlias ?? auth.Profile?.Username ?? requesterUserId,
                    workspace,
                    tierIndex,
                    cells,
                    layers,
                    gridShape,
                    requestedResourceId));
            }
            catch (HttpRequestException)
            {
                return new(false, "The claim request could not be delivered to the GM. Nothing was granted.");
            }

            if (request is null)
                return new(false, "The claim request was not accepted. Nothing was granted.");

            return new(true, "Claim request sent to the GM for permission review.", request);
        }
        finally
        {
            _claimAuthorityGate.Release();
        }
    }

    public async Task<IReadOnlyList<AwsAuthorityClient.WorldClaimRequest>> LoadPendingWorldClaimRequestsAsync()
    {
        if (!HasTrustedWorldBuilderAuthority || !HasActiveWorld) return [];

        var client = await GetClaimAuthorityClientAsync();
        if (client is null) return [];
        try
        {
            return await client.GetClaimRequestsAsync(WorldId, "pending") ?? [];
        }
        catch
        {
            return [];
        }
    }

    public async Task<WorldClaimSubmissionResult> DecideWorldClaimRequestAsync(
        AwsAuthorityClient.WorldClaimRequest request,
        WorldClaimPermission permission,
        IEnumerable<int>? approvedCells = null,
        IEnumerable<int>? approvedLayerOffsets = null,
        string approvedResourceId = "",
        string note = "",
        string writtenApproval = "")
    {
        if (!HasTrustedWorldBuilderAuthority)
            return new(false, "Only a trusted GM/owner may decide claim permissions.");
        if (request is null || !string.Equals(request.WorldId, WorldId, StringComparison.Ordinal))
            return new(false, "The claim request does not belong to the active world.");

        var cells = (approvedCells ?? request.SelectedCells ?? [])
            .Where(cell => cell >= 0 && cell < GridColumns * GridRows)
            .Distinct()
            .Order()
            .ToList();
        var layers = (approvedLayerOffsets ?? request.SourceLayerOffsets ?? [])
            .Where(layer => layer >= 0 && layer < LayersPerTier)
            .Distinct()
            .Order()
            .ToList();

        if (permission == WorldClaimPermission.Blocked)
        {
            cells.Clear();
            layers.Clear();
        }
        else if (permission is WorldClaimPermission.Restricted or WorldClaimPermission.Limited or WorldClaimPermission.Cooperative)
        {
            if (cells.Count == 0 || layers.Count == 0)
                return new(false, "Approved claims require an explicit spatial and layer scope.");
        }

        if (permission == WorldClaimPermission.ReleaseOwnership)
        {
            if (string.IsNullOrWhiteSpace(approvedResourceId))
                return new(false, "Release Ownership requires the exact resource being transferred.");
            var required = WorldClaimAuthorityPolicy.ReleaseOwnershipApprovalText(approvedResourceId, request.RequesterUserId);
            if (!string.Equals((writtenApproval ?? "").Trim(), required, StringComparison.Ordinal))
                return new(false, $"Type exactly: {required}");
        }

        var client = await GetClaimAuthorityClientAsync();
        if (client is null)
            return new(false, "Claim decisions are unavailable because server authority is offline.");

        try
        {
            var updated = await client.DecideClaimRequestAsync(new AwsAuthorityClient.WorldClaimDecision(
                WorldId,
                request.RequestId,
                permission.ToString(),
                cells,
                layers,
                approvedResourceId,
                note,
                writtenApproval));
            return updated is null
                ? new(false, "The server did not accept the claim decision.")
                : new(true, $"Claim decision saved as {permission}.", updated);
        }
        catch (HttpRequestException)
        {
            return new(false, "The claim decision could not be committed to server authority.");
        }
    }
}
