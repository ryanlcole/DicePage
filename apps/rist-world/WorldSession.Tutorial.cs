namespace RistWorld;

public sealed partial class WorldSession
{
    public bool TutorialWelcomeOpen { get; private set; } = true;
    public string TutorialPath { get; private set; } = "";
    public string TutorialStep { get; private set; } = "welcome";
    public string TutorialMapSource { get; private set; } = "";

    public void ChooseTutorialPath(string path)
    {
        TutorialPath = path;
        Role = path.Contains("Worldbuilder", StringComparison.Ordinal) ? "GM" : "PC";
        TutorialStep = path.Contains("Worldbuilder", StringComparison.Ordinal) ? "map-source" : "player-start";
        if(TutorialStep == "player-start") TutorialWelcomeOpen = false;
        Notify();
    }

    public void ChooseTutorialMapSource(string source)
    {
        TutorialMapSource = source;
        if(source == "paint")
        {
            TutorialWelcomeOpen = false;
            Mode = "tile";
            Notify();
            return;
        }
        TutorialStep = source == "attach" ? "map-attach" : "map-random";
        Notify();
    }
}
