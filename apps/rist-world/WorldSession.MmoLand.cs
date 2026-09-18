namespace RistWorld;

public sealed partial class WorldSession
{
    public const int MmoParcelGridColumns = 30;
    public const int MmoParcelGridRows = 30;
    public const int MmoParcelPixels = 2048;
    public const int MmoParcelMaxHeight = 10;
    public const int EndemarOriginColumn = 15;
    public const int EndemarOriginRow = 15;
    public const int EndemarOriginCell = EndemarOriginRow * MmoParcelGridColumns + EndemarOriginColumn;

    readonly List<AwsAuthorityClient.WorldToken> _mmoWorldTokens = [];
    readonly List<AwsAuthorityClient.MmoParcel> _mmoParcels = [];
    string _mmoLandStatus = "";

    public IReadOnlyList<AwsAuthorityClient.WorldToken> MmoWorldTokens => _mmoWorldTokens;
    public IReadOnlyList<AwsAuthorityClient.MmoParcel> MmoParcels => _mmoParcels;
    public string MmoLandStatus => _mmoLandStatus;

    public AwsAuthorityClient.WorldToken? UnspentMmoWorldToken =>
        _mmoWorldTokens.FirstOrDefault(token =>
            string.Equals(token.Status, "unspent", StringComparison.OrdinalIgnoreCase));

    public bool HasUnspentMmoWorldToken => UnspentMmoWorldToken is not null;

    public string MmoWorldTokenLabel => HasUnspentMmoWorldToken
        ? "1 SHAELVIEN WORLD TOKEN · READY"
        : _mmoWorldTokens.Count == 0
            ? "SHAELVIEN WORLD TOKEN · PROFILE REQUIRED"
            : "SHAELVIEN WORLD TOKEN · SPENT";

    public AwsAuthorityClient.MmoParcel? OwnedMmoParcel
    {
        get
        {
            var userId = auth.Profile?.UserId?.Trim() ?? "";
            return userId.Length == 0
                ? null
                : _mmoParcels.FirstOrDefault(parcel =>
                    string.Equals(parcel.OwnerUserId, userId, StringComparison.Ordinal));
        }
    }

    public AwsAuthorityClient.MmoParcel? EditableMmoParcel =>
        _mmoParcels.FirstOrDefault(CanEditMmoParcel);

    public bool HasEditableMmoParcel => EditableMmoParcel is not null;

    public bool CanEditMmoParcel(AwsAuthorityClient.MmoParcel? parcel)
    {
        if (parcel is null) return false;
        if (HasTrustedWorldBuilderAuthority) return true;

        var userId = auth.Profile?.UserId?.Trim() ?? "";
        if (userId.Length > 0 && string.Equals(parcel.OwnerUserId, userId, StringComparison.Ordinal))
            return true;

        return string.Equals(parcel.EffectivePermission, "Edit", StringComparison.OrdinalIgnoreCase)
            || string.Equals(parcel.EffectivePermission, "Manage", StringComparison.OrdinalIgnoreCase)
            || string.Equals(parcel.EffectivePermission, "Owner", StringComparison.OrdinalIgnoreCase);
    }

    public bool CanManageMmoParcel(AwsAuthorityClient.MmoParcel? parcel)
    {
        if (parcel is null) return false;
        if (HasTrustedWorldBuilderAuthority) return true;
        var userId = auth.Profile?.UserId?.Trim() ?? "";
        if (userId.Length > 0 && string.Equals(parcel.OwnerUserId, userId, StringComparison.Ordinal))
            return true;
        return string.Equals(parcel.EffectivePermission, "Manage", StringComparison.OrdinalIgnoreCase)
            || string.Equals(parcel.EffectivePermission, "Owner", StringComparison.OrdinalIgnoreCase);
    }

    public bool IsMmoParcelClaimed(int cellIndex) =>
        _mmoParcels.Any(parcel => parcel.CellIndex == cellIndex);

    public bool IsMmoParcelOwnedByCurrentUser(int cellIndex)
    {
        var userId = auth.Profile?.UserId?.Trim() ?? "";
        return userId.Length > 0 && _mmoParcels.Any(parcel =>
            parcel.CellIndex == cellIndex &&
            string.Equals(parcel.OwnerUserId, userId, StringComparison.Ordinal));
    }

    public bool IsMmoParcelClaimable(int cellIndex)
    {
        if (!IsLoggedIn || !IsGeonaphWorld || !HasUnspentMmoWorldToken) return false;
        if (cellIndex < 0 || cellIndex >= MmoParcelGridColumns * MmoParcelGridRows) return false;

        var column = cellIndex % MmoParcelGridColumns;
        var row = cellIndex / MmoParcelGridColumns;
        if (column == EndemarOriginColumn && row == EndemarOriginRow) return false;
        if (IsMmoParcelClaimed(cellIndex)) return false;

        var frontier = _mmoParcels.Select(parcel => (parcel.Column, parcel.Row)).ToHashSet();
        frontier.Add((EndemarOriginColumn, EndemarOriginRow));

        for (var dy = -1; dy <= 1; dy++)
        for (var dx = -1; dx <= 1; dx++)
        {
            if (dx == 0 && dy == 0) continue;
            if (frontier.Contains((column + dx, row + dy))) return true;
        }

        return false;
    }

    public async Task RefreshMmoLandAsync(bool loadParcels = true)
    {
        if (!IsLoggedIn)
        {
            _mmoWorldTokens.Clear();
            _mmoParcels.Clear();
            _mmoLandStatus = "";
            Notify();
            return;
        }

        try
        {
            var authority = new AwsAuthorityClient(http, auth);
            await authority.InitializeAsync();
            if (!authority.IsConfigured)
            {
                _mmoLandStatus = "Shaelvien land authority is awaiting deployment.";
                Notify();
                return;
            }

            if (auth.Account is not null)
            {
                await authority.CompleteProfileAsync(
                    auth.Account.AccountId,
                    auth.Account.PlayerAlias);
            }

            var tokens = await authority.GetWorldTokensAsync() ?? [];
            _mmoWorldTokens.Clear();
            _mmoWorldTokens.AddRange(tokens);

            if (loadParcels && IsGeonaphWorld)
            {
                var parcels = await authority.GetMmoParcelsAsync(WorldId) ?? [];
                _mmoParcels.Clear();
                _mmoParcels.AddRange(parcels);
            }

            _mmoLandStatus = HasUnspentMmoWorldToken
                ? "World token ready. Choose an available square touching Endemar or the claimed frontier."
                : OwnedMmoParcel is not null
                    ? "Your world token is bound to your Shaelvien parcel."
                    : "No unspent Shaelvien world token is available.";
        }
        catch
        {
            // The launcher remains usable while an updated authority stack deploys.
            // Claiming itself fails closed because no client-only token or parcel state is authoritative.
            _mmoLandStatus = "Shaelvien land authority could not be reached.";
        }

        Notify();
    }

    public async Task<AwsAuthorityClient.MmoParcel> ClaimMmoParcelAsync(int cellIndex, string displayName)
    {
        if (!IsLoggedIn) throw new InvalidOperationException("Log in before claiming a Shaelvien world.");
        if (!IsGeonaphWorld) throw new InvalidOperationException("MMO world tokens may only claim land in Shaelvien.");
        if (!IsMmoParcelClaimable(cellIndex))
            throw new InvalidOperationException("Choose an unclaimed square touching Endemar or the existing Shaelvien frontier.");

        displayName = (displayName ?? "").Trim();
        if (displayName.Length == 0) throw new InvalidOperationException("Name your world before claiming it.");
        if (displayName.Length > 80) throw new InvalidOperationException("World name must be 80 characters or fewer.");

        var authority = new AwsAuthorityClient(http, auth);
        await authority.InitializeAsync();
        var claimed = await authority.ClaimMmoParcelAsync(WorldId, cellIndex, displayName)
            ?? throw new InvalidOperationException("The Shaelvien parcel claim was not accepted.");

        await RefreshMmoLandAsync();
        await LoadRegionsAsync();
        if (!string.IsNullOrWhiteSpace(claimed.RegionId))
            SetActiveRegion(claimed.RegionId);

        _mmoLandStatus = $"{claimed.DisplayName} claimed · {claimed.PixelWidth}×{claimed.PixelHeight} px · height {claimed.MaxHeight}.";
        Notify();
        return claimed;
    }

    public async Task<bool> DelegateMmoParcelAsync(string parcelId, string userId, string permission)
    {
        parcelId = (parcelId ?? "").Trim();
        userId = (userId ?? "").Trim();
        permission = (permission ?? "None").Trim();
        if (parcelId.Length == 0 || userId.Length == 0) return false;

        var owned = _mmoParcels.FirstOrDefault(parcel =>
            string.Equals(parcel.ParcelId, parcelId, StringComparison.Ordinal));
        if (owned is null) return false;

        if (!CanManageMmoParcel(owned))
            return false;

        if (!(permission is "View" or "Edit" or "Manage" or "None"))
            permission = "None";

        var authority = new AwsAuthorityClient(http, auth);
        await authority.InitializeAsync();
        var result = await authority.DelegateMmoParcelAsync(WorldId, parcelId, userId, permission);
        if (result?.Ok != true) return false;

        _mmoLandStatus = permission == "None"
            ? "Parcel permission removed."
            : $"{permission} permission handed off for {owned.DisplayName}.";
        Notify();
        return true;
    }
}
