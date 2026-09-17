using Microsoft.JSInterop;

namespace RistWorld.Components;

public partial class WorldBuilderStudio
{
    [JSInvokable]
    public Task<WorldBuilderFocusState> GetWorldBuilderFocusStateFromJs() =>
        Task.FromResult(Session.GetWorldBuilderFocusState());

    [JSInvokable]
    public async Task<WorldBuilderFocusState> SelectWorldBuilderFocusOptionFromJs(string key)
    {
        var state = Session.SelectWorldBuilderFocusOption(key);
        await InvokeAsync(StateHasChanged);
        return state;
    }

    [JSInvokable]
    public async Task<WorldBuilderFocusState> LockWorldBuilderFocusFromJs()
    {
        var state = Session.LockWorldBuilderFocus();
        await InvokeAsync(StateHasChanged);
        return state;
    }

    [JSInvokable]
    public async Task<WorldBuilderFocusState> UnlockWorldBuilderFocusFromJs()
    {
        var state = Session.UnlockWorldBuilderFocus();
        await InvokeAsync(StateHasChanged);
        return state;
    }

    [JSInvokable]
    public async Task<WorldBuilderFocusState> ResetWorldBuilderFocusFromJs()
    {
        var state = Session.ResetWorldBuilderFocus();
        await InvokeAsync(StateHasChanged);
        return state;
    }
}
