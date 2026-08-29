namespace RistWorld;

public sealed partial class WorldSession
{
    public bool TutorialWelcomeOpen { get; private set; } = true;
    public string TutorialPath { get; private set; } = "";
    public string TutorialStep { get; private set; } = "welcome";
    public string TutorialMapSource { get; private set; } = "";

    public void ChooseTutorialPath(string path)
    {
        TutorialPath = path ?? "";
        var worldbuilder = TutorialPath.Contains("Worldbuilder", StringComparison.Ordinal);
        SetUserMode(worldbuilder ? "GameMaster" : "Player");
        TutorialStep = worldbuilder ? "map-source" : "player-start";
        if (TutorialStep == "player-start") TutorialWelcomeOpen = false;
        Notify();
    }

    public void ChooseTutorialMapSource(string source)
    {
        TutorialMapSource = source ?? "";
        if (TutorialMapSource == "paint")
        {
            TutorialWelcomeOpen = false;
            Mode = "tile";
            Notify();
            return;
        }
        TutorialStep = TutorialMapSource == "attach" ? "map-attach" : "map-random";
        Notify();
    }
}
