namespace RistWorld.Components;

public partial class WorldBuilderStudio
{
    bool _saveMenuOpen;
    bool _loadMenuOpen;
    bool _publishMenuOpen;
    bool _zFrameMenuOpen;
    bool _autoSave = true;
    double _zFrameDraft;
    double _tileSizeKmAtOrigin = 1.0;

    void OpenSaveMenu(){_saveMenuOpen=true;_loadMenuOpen=false;_publishMenuOpen=false;}
    void CloseSaveMenu()=>_saveMenuOpen=false;
    void OpenLoadMenu(){_loadMenuOpen=true;_saveMenuOpen=false;_publishMenuOpen=false;}
    void CloseLoadMenu()=>_loadMenuOpen=false;
    void OpenPublishMenu(){_publishMenuOpen=true;_saveMenuOpen=false;_loadMenuOpen=false;}
    void ClosePublishMenu()=>_publishMenuOpen=false;
    void ToggleAutoSave()=>_autoSave=!_autoSave;

    void OpenZFrameMenu(double sceneZ){_zFrameDraft=sceneZ;_zFrameMenuOpen=true;}
    void CloseZFrameMenu()=>_zFrameMenuOpen=false;
    void AddLayerAtDraft()
    {
        var target=(int)Math.Round(_zFrameDraft);
        while(Session.SceneZ<target)Session.MoveLayer(1);
        while(Session.SceneZ>target)Session.MoveLayer(-1);
        _zFrameMenuOpen=false;
    }
    void AddTierAtDraft()
    {
        var target=Math.Max(0,(int)Math.Floor(_zFrameDraft/10.0));
        while(Session.TierIndex<target)Session.MoveTier(1);
        while(Session.TierIndex>target)Session.MoveTier(-1);
        _zFrameMenuOpen=false;
    }
    void SetTileSizeKmAtOrigin(ChangeEventArgs e)
    {
        if(double.TryParse(e.Value?.ToString(),out var value)&&double.IsFinite(value)&&value>0)
            _tileSizeKmAtOrigin=value;
    }

    async Task SaveMenuSaveAsync(){await SaveAsync();_saveMenuOpen=false;}
    async Task LoadMenuLoadAsync(){await LoadLocalAsync();_loadMenuOpen=false;}
    Task ExportWorldAsync()=>JS.InvokeVoidAsync("ristWorld.exportCurrentWorld").AsTask();
    Task ImportWorldAsync()=>JS.InvokeVoidAsync("ristWorld.importCurrentWorld").AsTask();
    void PublishCurrent(){_publishMode=true;_publishMenuOpen=false;}
    void UnpublishCurrent(){_publishMode=false;_publishMenuOpen=false;}
}
