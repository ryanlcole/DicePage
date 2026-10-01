namespace RistWorld.Components;

public partial class UniversalInterface
{
    static readonly string[] HistoryDepthLabels = ["REGION", "LOCAL", "INSTANCE"];
    static readonly string[] HistoryTaskLabels =
    [
        "READ THE STONE",
        "STABILIZE THE CORE",
        "BATTER",
        "REDUCE THE CORE",
        "RECORD THE RESULT"
    ];

    static readonly string[] HistoryOpeningLabels = ["THE FUTURE", "TRANSFORM", "FORGET", "AWAKEN", "LIVE"];

    int _historyOpeningStep;
    int _historyDepthIndex;
    int _historyTaskIndex;
    bool _historyContextOpen;
    readonly HashSet<int> _historyCompletedTasks = [];

    string HistoryOpeningLabel => HistoryOpeningLabels[Math.Clamp(_historyOpeningStep, 0, HistoryOpeningLabels.Length - 1)];
    bool HistoryOpeningComplete => _historyOpeningStep >= HistoryOpeningLabels.Length;
    string HistoryOpeningPrompt => HistoryOpeningComplete
        ? "Arrival complete. Live inside the evidence-bounded reconstruction."
        : HistoryOpeningLabel switch
        {
            "THE FUTURE" => "Humanity achieved immortality and then time travel. You chose to go back.",
            "TRANSFORM" => "Your matter must conform to the destination historical world-state.",
            "FORGET" => "The transformation preserves identity but removes almost all future memory.",
            "AWAKEN" => "You awaken near the Lomekwi 3 evidence node. Species, language, and social identity remain unresolved.",
            _ => "Live as a person of the time. Survive. History continues whether or not you do."
        };
    string HistoryDepthLabel => HistoryDepthLabels[Math.Clamp(_historyDepthIndex, 0, HistoryDepthLabels.Length - 1)];
    string HistoryTaskLabel => HistoryTaskLabels[Math.Clamp(_historyTaskIndex, 0, HistoryTaskLabels.Length - 1)];
    bool HistoryAtInstance => _historyDepthIndex >= HistoryDepthLabels.Length - 1;
    bool HistoryAllTasksComplete => _historyCompletedTasks.Count >= HistoryTaskLabels.Length;

    void EnterGeonaphHistoryCampaign()
    {
        _historyOpeningStep = 0;
        _historyDepthIndex = 0;
        _historyTaskIndex = 0;
        _historyContextOpen = false;
        _historyCompletedTasks.Clear();
        _stage = Stage.HistoryCampaign;
        _message = "Act 1 · Scene 1 — First Breath. Begin in the future, cross through temporal matter conformity, lose future memory, and awaken inside the oldest installed evidence-grounded node.";
    }

    void HistoryApplyX(int direction)
    {
        if (!HistoryOpeningComplete || !HistoryAtInstance || direction == 0) return;
        _historyTaskIndex = Wrap(_historyTaskIndex + Math.Sign(direction), HistoryTaskLabels.Length);
        _message = $"Historical task: {HistoryTaskLabel}.";
    }

    void HistoryApplyY(int direction)
    {
        if (direction == 0 || !HistoryOpeningComplete) return;
        _historyDepthIndex = Math.Clamp(_historyDepthIndex - Math.Sign(direction), 0, HistoryDepthLabels.Length - 1);
        _historyContextOpen = false;
        _message = $"{HistoryDepthLabel} selected.";
    }

    void HistoryPressLeft()
    {
        if (!HistoryOpeningComplete)
        {
            _historyOpeningStep++;
            _historyContextOpen = false;
            if (HistoryOpeningComplete)
            {
                Session.PrepareGeonaphTravelerCharacter();
                _message = "Arrival complete. Character sheet prepared without inventing species, language, culture, or unsupported future knowledge. Continue into West Turkana → Lomekwi 3 → LOM3.";
            }
            else
            {
                _message = HistoryOpeningPrompt;
            }
            return;
        }

        if (!HistoryAtInstance)
        {
            _historyDepthIndex++;
            _historyContextOpen = false;
            _message = $"Descended to {HistoryDepthLabel}.";
            return;
        }

        _historyCompletedTasks.Add(_historyTaskIndex);
        _message = HistoryAllTasksComplete
            ? "The installed Lomekwi 3 factual tasks are complete. The eastward bridge remains locked until the next historical node is verified."
            : $"{HistoryTaskLabel} completed. Historical progress records the action without inventing a new fact.";
    }

    void HistoryPressRight()
    {
        if (!HistoryOpeningComplete)
        {
            Session.PrepareGeonaphTravelerCharacter();
            _message = "Traveler character opened. Only the future-origin backbone is prefilled; era-specific identity remains unknown until established by the active campaign/system authority.";
            return;
        }

        _historyContextOpen = !_historyContextOpen;
        _message = _historyContextOpen
            ? "Context opened. Original language status, translation status, fact, reconstruction, fiction, and sources remain separated."
            : "Context closed.";
    }

    void HistoryGoBack()
    {
        if (!HistoryOpeningComplete)
        {
            if (_historyOpeningStep > 0)
            {
                _historyOpeningStep--;
                _message = HistoryOpeningPrompt;
                return;
            }

            _stage = Stage.MmoMap;
            _message = "Returned to the Shaelvien roleplayer zone map.";
            return;
        }

        if (_historyContextOpen)
        {
            _historyContextOpen = false;
            _message = "Context closed.";
            return;
        }

        if (_historyDepthIndex > 0)
        {
            _historyDepthIndex--;
            _message = $"Returned to {HistoryDepthLabel}.";
            return;
        }

        _stage = Stage.MmoMap;
        _message = "Returned to the Shaelvien roleplayer zone map.";
    }
}
