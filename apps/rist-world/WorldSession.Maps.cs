namespace RistWorld;

public sealed partial class WorldSession
{
    public string ActiveProceduralMapId { get; private set; } = "random-world";
    public int ActiveProceduralMapSeed { get; private set; } = Random.Shared.Next(1, int.MaxValue);
    public int ActiveMapColumns { get; private set; } = 800;
    public int ActiveMapRows { get; private set; } = 600;
    public string ActiveMapLayer { get; private set; } = "WORLD";

    public void LoadProceduralMap(string id)
    {
        var map = id switch
        {
            "verdant-reach" => (Name: "Verdant Reach", Layer: "REGION", Columns: 320, Rows: 240, Seed: 170041),
            "ember-basin" => (Name: "Ember Basin", Layer: "REGION", Columns: 320, Rows: 240, Seed: 824911),
            "frost-march" => (Name: "Frost March", Layer: "REGION", Columns: 320, Rows: 240, Seed: 510337),
            _ => (Name: "Random World", Layer: "WORLD", Columns: 800, Rows: 600, Seed: Random.Shared.Next(1, int.MaxValue))
        };

        ActiveProceduralMapId = id;
        ActiveProceduralMapSeed = map.Seed;
        ActiveMapColumns = map.Columns;
        ActiveMapRows = map.Rows;
        ActiveMapLayer = map.Layer;
        MapName = map.Name;
        CardBrowserOpen = false;
        TileBrowserOpen = false;
        CloseHeaderMenus();
        Notify();
    }

    public void RegenerateWorld()
    {
        ActiveProceduralMapId = "random-world";
        ActiveProceduralMapSeed = Random.Shared.Next(1, int.MaxValue);
        ActiveMapColumns = 800;
        ActiveMapRows = 600;
        ActiveMapLayer = "WORLD";
        MapName = "Random World";
        Notify();
    }
}
