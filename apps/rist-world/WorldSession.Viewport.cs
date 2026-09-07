namespace RistWorld;

public sealed partial class WorldSession
{
    public void RequestMapViewReset()
    {
        _ = ResetMapViewportAsync();
    }

    async Task ResetMapViewportAsync()
    {
        try
        {
            await js.InvokeVoidAsync("eval", "(()=>{const map=document.querySelector('.viewer-map .map');if(!map)return;map.focus({preventScroll:true});map.dispatchEvent(new KeyboardEvent('keydown',{key:'0',bubbles:true}));})()");
        }
        catch (JSException)
        {
        }
    }
}
