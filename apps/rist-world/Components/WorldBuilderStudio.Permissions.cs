using Microsoft.AspNetCore.Components;

namespace RistWorld.Components;

public partial class WorldBuilderStudio
{
    readonly List<WorldBuilderPermissionPrincipal> _scopePermissionPrincipals = [];
    readonly Dictionary<string, string> _scopePermissionCache = new(StringComparer.Ordinal);
    bool _scopePermissionDirectoryLoaded;
    bool _scopePermissionBusy;
    string _scopePermissionPrincipal = "EVERYONE";
    string _scopePermissionEditorPlacementId = "";
    string _scopePermissionGrant = "None";
    string _scopePermissionStatus = "";

    IReadOnlyList<WorldBuilderPermissionPrincipal> ScopePermissionPrincipals
    {
        get
        {
            if (_scopePermissionPrincipals.Count == 0)
                return [new("EVERYONE", "EVERYONE")];
            return _scopePermissionPrincipals;
        }
    }

    RecursiveScopePlacement? ScopePermissionEditorPlacement =>
        string.IsNullOrWhiteSpace(_scopePermissionEditorPlacementId)
            ? null
            : Session.FindRecursiveScopePlacement("WORLD", Session.WorldId, _scopePermissionEditorPlacementId);

    async Task EnsureScopePermissionDirectoryAsync()
    {
        if (_scopePermissionDirectoryLoaded || !Session.IsLoggedIn)
            return;

        _scopePermissionBusy = true;
        _scopePermissionStatus = "";
        try
        {
            var rows = await Authority.GetConnectionsAsync() ?? [];
            _scopePermissionPrincipals.Clear();
            _scopePermissionPrincipals.Add(new("EVERYONE", "EVERYONE"));
            _scopePermissionPrincipals.AddRange(rows
                .Where(row => !string.IsNullOrWhiteSpace(row.LinkedUserId))
                .OrderBy(row => row.DisplayName, StringComparer.OrdinalIgnoreCase)
                .Select(row => new WorldBuilderPermissionPrincipal(
                    row.LinkedUserId,
                    string.IsNullOrWhiteSpace(row.DisplayName) ? row.LinkedUserId : row.DisplayName)));
            _scopePermissionDirectoryLoaded = true;
        }
        catch (Exception ex)
        {
            _scopePermissionStatus = "Permission directory unavailable · " + ex.Message;
        }
        finally
        {
            _scopePermissionBusy = false;
            await InvokeAsync(StateHasChanged);
        }
    }

    async Task ChangeScopePermissionPrincipalAsync(ChangeEventArgs e)
    {
        var requested = e.Value?.ToString()?.Trim() ?? "EVERYONE";
        _scopePermissionPrincipal = ScopePermissionPrincipals.Any(item =>
            string.Equals(item.UserId, requested, StringComparison.Ordinal))
            ? requested
            : "EVERYONE";
        _scopePermissionCache.Clear();
        _scopePermissionEditorPlacementId = "";
        _scopePermissionGrant = "None";
        _scopePermissionStatus = "";
        await InvokeAsync(StateHasChanged);
    }

    string ScopePermissionCellLabel(RecursiveScopePlacement placement)
    {
        if (!Session.IsLoggedIn) return "SIGN IN";
        if (string.IsNullOrWhiteSpace(placement.PermissionResourceId)) return "NO ID";
        return _scopePermissionCache.TryGetValue(placement.PermissionResourceId, out var permission)
            ? PermissionLabel(permission)
            : "SET";
    }

    static string PermissionLabel(string? permission) => permission switch
    {
        "Public" => "PUBLIC",
        "View" => "VIEW",
        "Edit" => "EDIT",
        "Deny" => "DENY",
        _ => "WAITING"
    };

    async Task OpenScopePermissionAsync(RecursiveScopePlacement placement)
    {
        if (!Session.IsLoggedIn)
        {
            _scopePermissionStatus = "Sign in to edit server-authoritative permissions.";
            return;
        }

        await EnsureScopePermissionDirectoryAsync();
        if (string.IsNullOrWhiteSpace(placement.PermissionResourceId))
        {
            _scopePermissionStatus = "This asset has no permission resource identity.";
            return;
        }

        _scopePermissionBusy = true;
        _scopePermissionStatus = "";
        try
        {
            var permissions = await Authority.GetResourcePermissionsAsync(
                Session.WorldId,
                placement.PermissionResourceId) ?? [];
            var current = permissions.FirstOrDefault(permission =>
                string.Equals(permission.UserId, _scopePermissionPrincipal, StringComparison.Ordinal));
            _scopePermissionGrant = current?.Permission ?? "None";
            if (_scopePermissionPrincipal == "EVERYONE" &&
                _scopePermissionGrant is not ("Public" or "None"))
                _scopePermissionGrant = "None";

            _scopePermissionCache[placement.PermissionResourceId] = _scopePermissionGrant;
            _scopePermissionEditorPlacementId = placement.AssetId;
        }
        catch (Exception ex)
        {
            _scopePermissionStatus = "Permission load failed · " + ex.Message;
        }
        finally
        {
            _scopePermissionBusy = false;
            await InvokeAsync(StateHasChanged);
        }
    }

    void ChangeScopePermissionGrant(ChangeEventArgs e)
    {
        var requested = e.Value?.ToString() ?? "None";
        _scopePermissionGrant = _scopePermissionPrincipal == "EVERYONE"
            ? requested is "Public" ? "Public" : "None"
            : requested is "View" or "Edit" or "Deny" ? requested : "None";
    }

    async Task SaveScopePermissionAsync()
    {
        var placement = ScopePermissionEditorPlacement;
        if (placement is null || !Session.IsLoggedIn || _scopePermissionBusy)
            return;

        var resourceId = placement.PermissionResourceId;
        if (string.IsNullOrWhiteSpace(resourceId))
            return;

        _scopePermissionBusy = true;
        _scopePermissionStatus = "";
        try
        {
            var result = await Authority.SetResourcePermissionAsync(
                Session.WorldId,
                resourceId,
                _scopePermissionPrincipal,
                _scopePermissionGrant);
            if (result?.Ok == true)
            {
                _scopePermissionCache[resourceId] = _scopePermissionGrant;
                _scopePermissionStatus = _scopePermissionGrant == "None"
                    ? "Explicit grant removed · inherited/default authority applies."
                    : "Permission saved.";
            }
            else
            {
                _scopePermissionStatus = "Permission was not changed.";
            }
        }
        catch (Exception ex)
        {
            _scopePermissionStatus = "Permission save failed · " + ex.Message;
        }
        finally
        {
            _scopePermissionBusy = false;
            await InvokeAsync(StateHasChanged);
        }
    }

    void CloseScopePermissionEditor()
    {
        _scopePermissionEditorPlacementId = "";
        _scopePermissionStatus = "";
    }
}

public sealed record WorldBuilderPermissionPrincipal(string UserId, string Label);
