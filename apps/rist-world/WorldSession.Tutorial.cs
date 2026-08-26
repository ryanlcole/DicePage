namespace RistWorld;

public sealed partial class WorldSession
{
    public bool TutorialWelcomeOpen { get; private set; } = true;
    public string TutorialPath { get; private set; } = "";

    public void ChooseTutorialPath(string path)
    {
        TutorialPath = path;
        Role = path.Contains("Worldbuilder", StringComparison.Ordinal) ? "GM" : "PC";
        TutorialWelcomeOpen = false;
        Notify();
    }

    public void SkipTutorial()
    {
        TutorialPath = "Skipped";
        TutorialWelcomeOpen = false;
        Notify();
    }
}
