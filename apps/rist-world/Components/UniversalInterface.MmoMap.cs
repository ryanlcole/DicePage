using System.Globalization;
using System.Text.Json;

namespace RistWorld.Components;

public partial class UniversalInterface
{
    const string MmoCanonicalSurfaceUrl =
        "https://d2d6rnm6fnsp89.cloudfront.net/library/terrains/standard/world/whole_maps/geonaph/geonaph_full_static_canonical_surface_v001.png";

    int _mmoSelectedCell = WorldSession.EndemarOriginCell;
    int _mmoLeftIndex;
    bool _mmoInspectMode;
    bool _mmoMapBusy;
    bool _mmoManageOpen;
    string _mmoManageName = "";
    string _mmoManageVisibility = "Restricted";
    string _mmoManageReason = "";
    readonly List<int> _mmoMapCells = [];
    readonly List<MmoSurfaceLayer> _mmoSurfaceLayers = [];

    sealed record MmoLeftChoice(string Label, string Kind, int? CellIndex = null);
    sealed record MmoSurfaceLayer(
        string RegionId,
        string Name,
        string Src,
        int Layer,
        double X,
        double Y,
        double Size,
        double Rotation,
        double Opacity);

    IReadOnlyList<MmoLeftChoice> MmoLeftChoices
    {
        get
        {
            var result = new List<MmoLeftChoice>
            {
                new("ENTER COORDINATES", "coordinates")
            };

            if (_mmoInspectMode)
            {
                result.Add(new("ENTER USER ID", "user"));
                return result;
            }

            result.AddRange(
                Session.MmoParcels
                    .Where(parcel => Session.IsMmoParcelOwnedByCurrentUser(parcel.CellIndex))
                    .OrderBy(parcel => parcel.DisplayName, StringComparer.OrdinalIgnoreCase)
                    .ThenBy(parcel => parcel.CellIndex)
                    .Select(parcel => new MmoLeftChoice(
                        string.IsNullOrWhiteSpace(parcel.DisplayName) ? MmoCoordinate(parcel.CellIndex) : parcel.DisplayName.ToUpperInvariant(),
                        "owned",
                        parcel.CellIndex)));
            return result;
        }
    }

    int MmoLeftOptionCount => Math.Max(1, MmoLeftChoices.Count);
    string MmoLeftValue => MmoLeftChoices[Math.Clamp(_mmoLeftIndex, 0, MmoLeftChoices.Count - 1)].Label;
    string MmoLeftPrompt => _mmoInspectMode
        ? "SLIDE ↑↓ · COORDINATES / USER ID"
        : MmoLeftOptionCount > 1
            ? "SLIDE ↑↓ · COORDINATES / OWNED ZONES"
            : "TOUCH · ENTER X,Y";

    AwsAuthorityClient.MmoParcel? MmoSelectedParcel =>
        Session.MmoParcels.FirstOrDefault(parcel => parcel.CellIndex == _mmoSelectedCell);

    bool MmoSelectedIsEndemar => _mmoSelectedCell == WorldSession.EndemarOriginCell;
    bool MmoSelectedIsOpen => !MmoSelectedIsEndemar && MmoSelectedParcel is null && Session.IsMmoParcelOpen(_mmoSelectedCell);
    bool MmoSelectedIsOwned => MmoSelectedParcel is { } parcel && Session.IsMmoParcelOwnedByCurrentUser(parcel.CellIndex);
    bool MmoSelectedIsRefunded => string.Equals(MmoSelectedParcel?.Status, "Refunded", StringComparison.OrdinalIgnoreCase);
    bool MmoSelectedIsShaelvienRoleplayZone =>
        MmoSelectedIsEndemar || IsCanonicalShaelvienRoleplayZone(MmoSelectedParcel);

    static bool IsCanonicalShaelvienRoleplayZone(AwsAuthorityClient.MmoParcel? parcel)
    {
        if (parcel is null) return false;
        var name = (parcel.DisplayName ?? "").Trim();
        return string.Equals(name, "The Sunken Tundra", StringComparison.OrdinalIgnoreCase)
            || string.Equals(name, "Sunken Tundra", StringComparison.OrdinalIgnoreCase);
    }

    string MmoBidLabel
    {
        get
        {
            var bid = MmoSelectedParcel?.CurrentBid ?? 0m;
            var bidder = string.IsNullOrWhiteSpace(MmoSelectedParcel?.CurrentBidUsername)
                ? "NO BIDS"
                : MmoSelectedParcel!.CurrentBidUsername.Trim();
            return $"BID (CURRENT BID {bid.ToString("0.##", CultureInfo.InvariantCulture)} {bidder})";
        }
    }

    string MmoSelectedName =>
        MmoSelectedIsEndemar
            ? WorldSession.EndemarStartingPointDisplayName
            : MmoSelectedParcel is not null && !string.IsNullOrWhiteSpace(MmoSelectedParcel.DisplayName)
                ? MmoSelectedParcel.DisplayName
                : MmoSelectedIsOpen
                    ? $"Available deed {MmoCoordinate(_mmoSelectedCell)}"
                    : MmoCoordinate(_mmoSelectedCell);

    string MmoRightValue
    {
        get
        {
            if (_mmoInspectMode) return "MANAGE";
            if (MmoSelectedIsRefunded) return MmoBidLabel;
            if (MmoSelectedIsShaelvienRoleplayZone) return "ROLEPLAY";
            if (MmoSelectedParcel is not null)
                return MmoSelectedIsOwned ? "MANAGE" : "REQUEST DEED FROM GM";
            if (MmoSelectedIsOpen)
                return Session.HasUnspentMmoWorldToken ? "CLAIM DEED" : "PURCHASE TOKEN AND CLAIM DEED";
            return "UNAVAILABLE";
        }
    }

    string MmoRightPrompt
    {
        get
        {
            if (_mmoInspectMode) return $"TOUCH · {MmoSelectedName.ToUpperInvariant()}";
            if (MmoSelectedIsRefunded) return MmoBidLabel;
            if (MmoSelectedIsShaelvienRoleplayZone) return $"TOUCH · ROLEPLAY · {MmoSelectedName.ToUpperInvariant()}";
            if (MmoSelectedParcel is not null)
                return MmoSelectedIsOwned ? "TOUCH · MANAGE DEED" : "TOUCH · SEND REQUEST";
            if (MmoSelectedIsOpen && Session.HasUnspentMmoWorldToken)
            {
                var count = Session.UnspentMmoWorldTokenCount;
                return $"USE 1/{count} TOKEN{(count == 1 ? "" : "S")}";
            }
            if (MmoSelectedIsOpen) return "TOKEN REQUIRED";
            return "NO ACTION";
        }
    }

    string MmoMapModeLabel => _mmoInspectMode ? "DEVELOPER INSPECT" : "MMO DEED MAP";
    string MmoTokenBadge => _mmoInspectMode
        ? "CLAIM DISABLED"
        : $"{Session.UnspentMmoWorldTokenCount} TOKEN{(Session.UnspentMmoWorldTokenCount == 1 ? "" : "S")}";

    // The MMO map is the currently-created Shaelvien footprint, not a crop of
    // Endemar. Claimed deeds plus their open flat-side frontier define the
    // visible extent, so the representation expands as the world expands.
    int MmoViewMinColumn => _mmoMapCells.Count == 0
        ? WorldSession.EndemarOriginColumn
        : _mmoMapCells.Min(CellColumn);
    int MmoViewMaxColumn => _mmoMapCells.Count == 0
        ? WorldSession.EndemarOriginColumn
        : _mmoMapCells.Max(CellColumn);
    int MmoViewMinRow => _mmoMapCells.Count == 0
        ? WorldSession.EndemarOriginRow
        : _mmoMapCells.Min(CellRow);
    int MmoViewMaxRow => _mmoMapCells.Count == 0
        ? WorldSession.EndemarOriginRow
        : _mmoMapCells.Max(CellRow);
    int MmoViewColumns => Math.Max(1, MmoViewMaxColumn - MmoViewMinColumn + 1);
    int MmoViewRows => Math.Max(1, MmoViewMaxRow - MmoViewMinRow + 1);

    string MmoMapStageStyle => $"aspect-ratio:{MmoViewColumns}/{MmoViewRows};";

    string MmoCellStyle(int cellIndex)
    {
        var column = CellColumn(cellIndex);
        var row = CellRow(cellIndex);
        var left = (column - MmoViewMinColumn) / (double)MmoViewColumns * 100;
        var top = (row - MmoViewMinRow) / (double)MmoViewRows * 100;
        return $"left:{left:0.####}%;top:{top:0.####}%;width:{100d / MmoViewColumns:0.####}%;height:{100d / MmoViewRows:0.####}%;";
    }

    string? MmoCellSurfaceUrl(int cellIndex)
    {
        // Shaelvien is the growing deed lattice, not a prebuilt map beneath it.
        // Endemar is the origin deed at (0,0), so its complete canonical surface
        // is clipped to that single square. Claimed deeds may render only their
        // own Tier 0 top surface. Unclaimed frontier intentionally has no terrain.
        if (cellIndex == WorldSession.EndemarOriginCell)
            return MmoCanonicalSurfaceUrl;

        var parcel = Session.MmoParcels.FirstOrDefault(item => item.CellIndex == cellIndex);
        if (parcel is null || string.IsNullOrWhiteSpace(parcel.RegionId))
            return null;

        return _mmoSurfaceLayers
            .FirstOrDefault(layer => string.Equals(layer.RegionId, parcel.RegionId, StringComparison.Ordinal))
            ?.Src;
    }

    string MmoCellClass(int cellIndex)
    {
        var classes = new List<string> { "mmo-deed-cell" };
        var parcel = Session.MmoParcels.FirstOrDefault(item => item.CellIndex == cellIndex);

        if (cellIndex == WorldSession.EndemarOriginCell) classes.Add("endemar");
        else if (parcel is not null)
        {
            if (string.Equals(parcel.Status, "Refunded", StringComparison.OrdinalIgnoreCase)) classes.Add("refunded");
            else if (Session.IsMmoParcelOwnedByCurrentUser(parcel.CellIndex)) classes.Add("owned");
            else classes.Add(string.Equals(parcel.Visibility, "Public", StringComparison.OrdinalIgnoreCase) ? "public" : "private");
        }
        else classes.Add("available");

        if (cellIndex == _mmoSelectedCell) classes.Add("selected");
        return string.Join(' ', classes);
    }

    string MmoCellText(int cellIndex)
    {
        if (cellIndex == WorldSession.EndemarOriginCell) return WorldSession.EndemarStartingPointDisplayName;
        var parcel = Session.MmoParcels.FirstOrDefault(item => item.CellIndex == cellIndex);
        return parcel?.DisplayName?.Trim() ?? "";
    }

    string MmoCellAriaLabel(int cellIndex)
    {
        var text = MmoCellText(cellIndex);
        if (string.IsNullOrWhiteSpace(text)) text = "Available deed";
        return $"{text} {MmoCoordinate(cellIndex)}";
    }

    static int CellColumn(int cellIndex) => cellIndex % WorldSession.MmoParcelGridColumns;
    static int CellRow(int cellIndex) => cellIndex / WorldSession.MmoParcelGridColumns;

    static string MmoCoordinate(int cellIndex)
    {
        var column = CellColumn(cellIndex);
        var row = CellRow(cellIndex);
        var x = column - WorldSession.EndemarOriginColumn;
        var y = WorldSession.EndemarOriginRow - row;
        return $"({x},{y})";
    }

    void RefreshMmoMapCells()
    {
        var cells = new HashSet<int> { WorldSession.EndemarOriginCell };
        foreach (var parcel in Session.MmoParcels)
            if (parcel.CellIndex >= 0 && parcel.CellIndex < WorldSession.MmoParcelGridColumns * WorldSession.MmoParcelGridRows)
                cells.Add(parcel.CellIndex);

        for (var cell = 0; cell < WorldSession.MmoParcelGridColumns * WorldSession.MmoParcelGridRows; cell++)
            if (Session.IsMmoParcelOpen(cell))
                cells.Add(cell);

        _mmoMapCells.Clear();
        _mmoMapCells.AddRange(cells.OrderBy(CellRow).ThenBy(CellColumn));

        if (!_mmoMapCells.Contains(_mmoSelectedCell))
            _mmoSelectedCell = WorldSession.EndemarOriginCell;
    }

    async Task EnterMmoMapAsync(bool inspect)
    {
        await EnsureShaelvienEnvironmentAsync();
        _mmoInspectMode = inspect && Session.TrustedPlatformDeveloper;
        _mmoLeftIndex = 0;
        _mmoSelectedCell = WorldSession.EndemarOriginCell;
        _mmoManageOpen = false;
        _mmoManageReason = "";
        RefreshMmoMapCells();
        await LoadMmoTierZeroSurfaceAsync();
        _stage = Stage.MmoMap;
        _message = _mmoInspectMode
            ? "Inspect · Tier 0 surface. Analog selects a zone. Left rail accepts coordinates or user ID. Claiming is disabled."
            : "Shaelvien MMO · Each visible deed owns its flattened Tier 0 top surface. Analog selects the next deed zone in the direction moved.";
        await InvokeAsync(StateHasChanged);
    }

    async Task LoadMmoTierZeroSurfaceAsync()
    {
        _mmoSurfaceLayers.Clear();
        try
        {
            var source = await Session.LoadWorldBuilderSourceAsync();
            if (source?.State is not JsonElement state || state.ValueKind != JsonValueKind.Object) return;
            if (!state.TryGetProperty("userLayers", out var layers) || layers.ValueKind != JsonValueKind.Array) return;

            var topByRegion = new Dictionary<string, MmoSurfaceLayer>(StringComparer.Ordinal);
            foreach (var item in layers.EnumerateArray())
            {
                if (item.ValueKind != JsonValueKind.Object) continue;
                var tier = JsonInt(item, "tier", 0);
                if (tier != 0) continue;
                var regionId = JsonString(item, "regionId");
                if (string.IsNullOrWhiteSpace(regionId)) continue;

                var src = JsonString(item, "transparentSrc");
                if (string.IsNullOrWhiteSpace(src)) src = JsonString(item, "originalSrc");
                if (string.IsNullOrWhiteSpace(src)) continue;

                var layer = new MmoSurfaceLayer(
                    regionId,
                    JsonString(item, "name"),
                    src,
                    JsonInt(item, "layer", 0),
                    JsonDouble(item, "x", .5),
                    JsonDouble(item, "y", .5),
                    Math.Max(.001, JsonDouble(item, "size", 1)),
                    JsonDouble(item, "rotation", 0),
                    JsonDouble(item, "opacity", 1));

                if (!topByRegion.TryGetValue(regionId, out var current) || layer.Layer > current.Layer)
                    topByRegion[regionId] = layer;
            }

            _mmoSurfaceLayers.AddRange(topByRegion.Values.OrderBy(layer => layer.Layer).ThenBy(layer => layer.RegionId, StringComparer.Ordinal));
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"MMO Tier 0 surface load failed: {ex}");
            _message = "The deed lattice loaded, but authored Tier 0 surface overlays could not be read.";
        }
    }

    static string JsonString(JsonElement item, string name) =>
        item.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.String
            ? value.GetString()?.Trim() ?? ""
            : "";

    static int JsonInt(JsonElement item, string name, int fallback)
    {
        if (!item.TryGetProperty(name, out var value)) return fallback;
        if (value.ValueKind == JsonValueKind.Number && value.TryGetInt32(out var result)) return result;
        if (value.ValueKind == JsonValueKind.String && int.TryParse(value.GetString(), NumberStyles.Integer, CultureInfo.InvariantCulture, out result)) return result;
        return fallback;
    }

    static double JsonDouble(JsonElement item, string name, double fallback)
    {
        if (!item.TryGetProperty(name, out var value)) return fallback;
        if (value.ValueKind == JsonValueKind.Number && value.TryGetDouble(out var result)) return result;
        if (value.ValueKind == JsonValueKind.String && double.TryParse(value.GetString(), NumberStyles.Float, CultureInfo.InvariantCulture, out result)) return result;
        return fallback;
    }

    void SelectMmoMapCell(int cellIndex)
    {
        if (!_mmoMapCells.Contains(cellIndex)) return;
        _mmoSelectedCell = cellIndex;
        _mmoManageOpen = false;
        _message = $"{MmoSelectedName} {MmoCoordinate(cellIndex)} selected.";
    }

    void MoveMmoSelection(int dx, int dy)
    {
        dx = Math.Sign(dx);
        dy = Math.Sign(dy);
        if (dx == 0 && dy == 0) return;

        // A stick move is one flat-side topology step. Never jump across a
        // missing deed/frontier cell to a more distant zone.
        var nextColumn = CellColumn(_mmoSelectedCell) + dx;
        var nextRow = CellRow(_mmoSelectedCell) + dy;
        if (nextColumn < 0 || nextColumn >= WorldSession.MmoParcelGridColumns
            || nextRow < 0 || nextRow >= WorldSession.MmoParcelGridRows)
        {
            _message = "That direction is outside the Shaelvien deed lattice.";
            return;
        }

        var nextCell = nextRow * WorldSession.MmoParcelGridColumns + nextColumn;
        if (!_mmoMapCells.Contains(nextCell))
        {
            _message = $"No adjacent deed zone exists at {MmoCoordinate(nextCell)}.";
            return;
        }

        SelectMmoMapCell(nextCell);
    }

    void CycleMmoLeftOption(int direction)
    {
        var choices = MmoLeftChoices;
        if (choices.Count <= 1) return;
        _mmoLeftIndex = Wrap(_mmoLeftIndex + Math.Sign(direction), choices.Count);
        _message = $"Left action: {MmoLeftValue}.";
    }

    async Task PressMmoLeftAsync()
    {
        var choices = MmoLeftChoices;
        var choice = choices[Math.Clamp(_mmoLeftIndex, 0, choices.Count - 1)];
        if (choice.Kind == "owned" && choice.CellIndex is int cell)
        {
            SelectMmoMapCell(cell);
            return;
        }

        if (choice.Kind == "user")
        {
            var userId = (await JS.InvokeAsync<string?>("prompt", "Enter the exact user ID to inspect:", ""))?.Trim() ?? "";
            if (string.IsNullOrWhiteSpace(userId)) return;
            var match = Session.MmoParcels
                .Where(parcel => string.Equals(parcel.OwnerUserId, userId, StringComparison.Ordinal))
                .OrderBy(parcel => parcel.CellIndex)
                .FirstOrDefault();
            if (match is null)
            {
                _message = "No visible Shaelvien deed is owned by that user ID.";
                return;
            }
            SelectMmoMapCell(match.CellIndex);
            return;
        }

        var initial = MmoCoordinate(_mmoSelectedCell).Trim('(', ')');
        var coordinate = (await JS.InvokeAsync<string?>("prompt", "Enter Endemar-relative coordinates as x,y. Endemar is 0,0.", initial))?.Trim() ?? "";
        if (string.IsNullOrWhiteSpace(coordinate)) return;
        var parts = coordinate.Trim('(', ')').Split(',', StringSplitOptions.TrimEntries | StringSplitOptions.RemoveEmptyEntries);
        if (parts.Length != 2
            || !int.TryParse(parts[0], NumberStyles.Integer, CultureInfo.InvariantCulture, out var x)
            || !int.TryParse(parts[1], NumberStyles.Integer, CultureInfo.InvariantCulture, out var y))
        {
            _message = "Coordinates must use x,y, for example 0,1.";
            return;
        }

        var column = WorldSession.EndemarOriginColumn + x;
        var row = WorldSession.EndemarOriginRow - y;
        if (column < 0 || column >= WorldSession.MmoParcelGridColumns || row < 0 || row >= WorldSession.MmoParcelGridRows)
        {
            _message = "Those coordinates are outside the Shaelvien deed lattice.";
            return;
        }

        var target = row * WorldSession.MmoParcelGridColumns + column;
        if (!_mmoMapCells.Contains(target))
        {
            _message = $"{MmoCoordinate(target)} is not currently a deed, claimed zone, or available frontier zone.";
            return;
        }
        SelectMmoMapCell(target);
    }

    async Task PressMmoRightAsync()
    {
        if (_mmoInspectMode)
        {
            OpenMmoManage();
            return;
        }

        if (MmoSelectedIsRefunded)
        {
            _message = "This deed is marked Refunded. The current bid is shown on the right; bid submission is not enabled until server-side auction settlement is implemented.";
            return;
        }

        if (MmoSelectedIsShaelvienRoleplayZone)
        {
            if (MmoSelectedParcel is { RegionId.Length: > 0 } roleplayParcel)
                Session.SetActiveRegion(roleplayParcel.RegionId);
            else
                Session.SetActiveRegion("");

            if (OnRoleplay.HasDelegate)
            {
                await OnRoleplay.InvokeAsync(MmoSelectedName);
                return;
            }

            _message = $"Roleplay selected for {MmoSelectedName}.";
            return;
        }

        if (MmoSelectedParcel is { } parcel)
        {
            if (MmoSelectedIsOwned)
            {
                var selected = PathWorldOptions.FirstOrDefault(option => string.Equals(option.Id, parcel.ParcelId, StringComparison.Ordinal));
                if (selected is not null)
                {
                    SetSelectedDeed(selected);
                    if (!string.IsNullOrWhiteSpace(parcel.RegionId)) Session.SetActiveRegion(parcel.RegionId);
                    _stage = Stage.PathSelect;
                    _message = $"{parcel.DisplayName} selected. World Builder is on the left; Context is on the right.";
                }
                return;
            }

            _mmoMapBusy = true;
            try
            {
                var requested = await Session.RequestMmoDeedAsync(_mmoSelectedCell);
                _message = requested
                    ? $"Deed request sent to the GameMaster for {parcel.DisplayName}."
                    : "The deed request could not be sent.";
            }
            catch (Exception ex)
            {
                _message = string.IsNullOrWhiteSpace(ex.Message) ? "The deed request could not be sent." : ex.Message;
            }
            finally
            {
                _mmoMapBusy = false;
            }
            return;
        }

        if (!MmoSelectedIsOpen) return;

        if (!Session.HasUnspentMmoWorldToken)
        {
            _message = "Purchase Token and Claim Deed is reserved in the interface, but paid Shaelvien Token checkout is not implemented yet. No purchase was attempted.";
            return;
        }

        var suggested = $"Shaelvien {MmoCoordinate(_mmoSelectedCell)}";
        var name = (await JS.InvokeAsync<string?>("prompt", "Name this deed before claiming it:", suggested))?.Trim() ?? "";
        if (string.IsNullOrWhiteSpace(name)) return;

        _mmoMapBusy = true;
        try
        {
            var claimed = await Session.ClaimMmoParcelAsync(_mmoSelectedCell, name);
            RefreshMmoMapCells();
            await CompleteShaelvienDeedAsync(claimed);
        }
        catch (Exception ex)
        {
            await Session.RefreshMmoLandAsync();
            RefreshMmoMapCells();
            _message = string.IsNullOrWhiteSpace(ex.Message) ? "The deed could not be claimed." : ex.Message;
        }
        finally
        {
            _mmoMapBusy = false;
        }
    }

    void OpenMmoManage()
    {
        if (!_mmoInspectMode || !Session.TrustedPlatformDeveloper)
        {
            _message = "Developer Inspect authority is required.";
            return;
        }

        var parcel = MmoSelectedParcel;
        if (!MmoSelectedIsEndemar && parcel is null)
        {
            _message = "Select Endemar or a claimed zone to manage.";
            return;
        }

        _mmoManageName = MmoSelectedIsEndemar
            ? WorldSession.EndemarStartingPointDisplayName
            : parcel!.DisplayName;
        _mmoManageVisibility = MmoSelectedIsEndemar
            ? "Public"
            : string.Equals(parcel!.Visibility, "Public", StringComparison.OrdinalIgnoreCase) ? "Public" : "Restricted";
        _mmoManageReason = "";
        _mmoManageOpen = true;
        _message = MmoSelectedIsEndemar
            ? "Manage Endemar. Enter a reason, then open World Builder for audited structural editing."
            : $"Manage {parcel!.DisplayName}. Every committed Inspect change requires a reason.";
    }

    async Task OpenMmoInspectEditorAsync()
    {
        if (!_mmoInspectMode || !Session.TrustedPlatformDeveloper)
        {
            _message = "Developer Inspect authority is required.";
            return;
        }

        var reason = (_mmoManageReason ?? "").Trim();
        if (reason.Length < 3)
        {
            _message = "Enter a reason before opening the Inspect World Builder.";
            return;
        }

        await Session.LoadRegionsAsync();

        ControllerWorldOption selected;
        if (MmoSelectedIsEndemar)
        {
            selected = new ControllerWorldOption(
                "__endemar__",
                WorldSession.EndemarStartingPointDisplayName,
                "SHAELVIEN_ORIGIN",
                null,
                null);
            Session.SetActiveRegion("");
        }
        else if (MmoSelectedParcel is { } parcel)
        {
            selected = new ControllerWorldOption(
                parcel.ParcelId,
                parcel.DisplayName,
                "SHAELVIEN",
                null,
                parcel);
            if (!string.IsNullOrWhiteSpace(parcel.RegionId))
                Session.SetActiveRegion(parcel.RegionId);
        }
        else
        {
            _message = "Select Endemar or a claimed zone to inspect.";
            return;
        }

        SetSelectedDeed(selected);
        _exploreReadOnlyMode = false;
        _inspectionEditMode = true;
        _inspectionEditReason = reason.Length > 500 ? reason[..500] : reason;
        _mmoManageOpen = false;
        _stage = Stage.PathSelect;
        _pathIndex = 0;
        _pathMenuIndex = 0;
        _message = $"Inspect edit · {_selectedDeedName}. World Builder is on the left; Context is on the right. Every committed edit requires an audit reason.";
        await InvokeAsync(StateHasChanged);
    }

    void CloseMmoManage()
    {
        _mmoManageOpen = false;
        _mmoManageReason = "";
    }

    async Task SaveMmoManageAsync()
    {
        var parcel = MmoSelectedParcel;
        if (!_mmoInspectMode || parcel is null || string.IsNullOrWhiteSpace(parcel.ParcelId)) return;

        var reason = _mmoManageReason.Trim();
        if (reason.Length < 3)
        {
            _message = "Enter a reason before committing an Inspect change.";
            return;
        }

        _mmoMapBusy = true;
        try
        {
            var updated = await Session.InspectEditMmoParcelAsync(
                parcel.ParcelId,
                _mmoManageName.Trim(),
                _mmoManageVisibility,
                reason);
            if (updated is null)
            {
                _message = "The Inspect change was not accepted.";
                return;
            }

            await Session.RefreshMmoLandAsync();
            RefreshMmoMapCells();
            await LoadMmoTierZeroSurfaceAsync();
            _mmoManageOpen = false;
            _mmoManageReason = "";
            _message = $"{updated.DisplayName} updated and audit reason recorded.";
        }
        catch (Exception ex)
        {
            _message = string.IsNullOrWhiteSpace(ex.Message) ? "The Inspect change could not be saved." : ex.Message;
        }
        finally
        {
            _mmoMapBusy = false;
        }
    }
}
