namespace RistWorld;

public sealed partial class WorldSession
{
    public const int MmoParcelGridColumns = 30;
    public const int MmoParcelGridRows = 30;

    // Canonical Shaelvien property space purchased by one Shaelvien Token.
    // "Parcel" remains the persistence/geometry term; Property Space is the
    // player-facing ownership concept.
    public const int ShaelvienPropertySpacePixels = 2048;
    public const int ShaelvienPropertySpaceLayers = 100;
    public const int MmoParcelPixels = ShaelvienPropertySpacePixels;
    public const int MmoParcelMaxHeight = ShaelvienPropertySpaceLayers;
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
        ? "1 SHAELVIEN TOKEN · READY"
        : _mmoWorldTokens.Count == 0
            ? "SHAELVIEN TOKEN · PROFILE REQUIRED"
            : "SHAELVIEN TOKEN · SPENT";

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

    public bool CanAccessMmoParcel(AwsAuthorityClient.MmoParcel? parcel)
    {
        if (parcel is null || !IsLoggedIn) return false;
        if (HasTrustedWorldBuilderAuthority) return true;

        var userId = auth.Profile?.UserId?.Trim() ?? "";
        if (userId.Length > 0 && string.Equals(parcel.OwnerUserId, userId, StringComparison.Ordinal))
            return true;

        return string.Equals(parcel.EffectivePermission, "View", StringComparison.OrdinalIgnoreCase)
            || string.Equals(parcel.EffectivePermission, "Edit", StringComparison.OrdinalIgnoreCase)
            || string.Equals(parcel.EffectivePermission, "Manage", StringComparison.OrdinalIgnoreCase)
            || string.Equals(parcel.EffectivePermission, "Owner", StringComparison.OrdinalIgnoreCase);
    }

    public bool CanEditMmoParcel(AwsAuthorityClient.MmoParcel? parcel)
    {
        if (parcel is null || !IsLoggedIn) return false;
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
        if (parcel is null || !IsLoggedIn) return false;
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
                ? "Shaelvien Token ready. Choose an available property space touching Endemar or the claimed frontier."
                : OwnedMmoParcel is not null
                    ? "Your Shaelvien Token is bound to your Shaelvien property space."
                    : "No unspent Shaelvien Token is available.";
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
        if (!IsGeonaphWorld) throw new InvalidOperationException("Shaelvien Tokens may only claim property space in Shaelvien.");
        if (!IsMmoParcelClaimable(cellIndex))
            throw new InvalidOperationException("Choose an unclaimed square touching Endemar or the existing Shaelvien frontier.");

        displayName = (displayName ?? "").Trim();
        if (displayName.Length == 0) throw new InvalidOperationException("Name your world before claiming it.");
        if (displayName.Length > 80) throw new InvalidOperationException("World name must be 80 characters or fewer.");

        var authority = new AwsAuthorityClient(http, auth);
        await authority.InitializeAsync();
        AwsAuthorityClient.MmoParcel? claimed = null;
        string committedTokenId = "";

        for (var attempt = 0; attempt < 2 && claimed is null; attempt++)
        {
            var tokenId = UnspentMmoWorldToken?.TokenId ?? "";
            if (string.IsNullOrWhiteSpace(tokenId))
                throw new InvalidOperationException("No unspent Shaelvien Token is available for this claim.");

            try
            {
                claimed = await authority.ClaimMmoParcelAsync(WorldId, cellIndex, displayName, tokenId)
                    ?? throw new InvalidOperationException("The Shaelvien property-space claim was not accepted.");
                committedTokenId = tokenId;
            }
            catch (HttpRequestException ex)
            {
                await RefreshMmoLandAsync();

                // The authority may repair a legacy/newly-minted token binding while
                // processing the first claim. That repair is server-authoritative,
                // so transparently retry once with the freshly-read token instead
                // of making the player press CLAIM a second time.
                if (
                    attempt == 0
                    && ex.StatusCode == System.Net.HttpStatusCode.Conflict
                    && ex.Message.Contains("binding was refreshed", StringComparison.OrdinalIgnoreCase)
                    && HasUnspentMmoWorldToken
                )
                    continue;

                if (ex.StatusCode == System.Net.HttpStatusCode.Conflict)
                {
                    var occupied = _mmoParcels.FirstOrDefault(parcel => parcel.CellIndex == cellIndex);
                    if (occupied is not null)
                    {
                        if (CanEditMmoParcel(occupied))
                            throw new InvalidOperationException($"{occupied.DisplayName} is already bound to your account. Enter that property space instead.", ex);
                        throw new InvalidOperationException("That property space was just claimed. The map has been refreshed; choose another available square.", ex);
                    }

                    if (!HasUnspentMmoWorldToken)
                    {
                        if (OwnedMmoParcel is { } owned)
                            throw new InvalidOperationException($"Your Shaelvien Token is already bound to {owned.DisplayName}. Enter that property space instead.", ex);
                        throw new InvalidOperationException("Your Shaelvien Token is no longer available. Account state has been refreshed.", ex);
                    }
                }

                throw new InvalidOperationException(
                    string.IsNullOrWhiteSpace(ex.Message)
                        ? "The property-space claim could not be completed. The map has been refreshed."
                        : ex.Message,
                    ex);
            }
        }

        if (claimed is null)
            throw new InvalidOperationException("The Shaelvien property-space claim could not be completed.");

        // The POST response is the authoritative committed parcel. Reflect it
        // immediately in the client before doing any secondary region/directory
        // reads. A slow follow-up read must never make a successful claim look
        // unspent or leave the claim dialog open.
        var parcelIndex = _mmoParcels.FindIndex(parcel =>
            string.Equals(parcel.ParcelId, claimed.ParcelId, StringComparison.Ordinal));
        if (parcelIndex >= 0)
            _mmoParcels[parcelIndex] = claimed;
        else
            _mmoParcels.Add(claimed);

        var tokenIndex = _mmoWorldTokens.FindIndex(token =>
            string.Equals(token.TokenId, committedTokenId, StringComparison.Ordinal));
        if (tokenIndex >= 0)
        {
            var token = _mmoWorldTokens[tokenIndex];
            _mmoWorldTokens[tokenIndex] = token with
            {
                Status = "spent",
                PurchasedWorldId = WorldId,
                ParcelId = claimed.ParcelId,
                BindingHash = claimed.BindingHash
            };
        }

        _mmoLandStatus = $"{claimed.DisplayName} property space claimed · {claimed.PixelWidth}×{claimed.PixelHeight} px · {claimed.MaxHeight} layers.";
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
