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

    int _historyDepthIndex;
    int _historyTaskIndex;
    bool _historyContextOpen;
    readonly HashSet<int> _historyCompletedTasks = [];

    string HistoryDepthLabel => HistoryDepthLabels[Math.Clamp(_historyDepthIndex, 0, HistoryDepthLabels.Length - 1)];
    string HistoryTaskLabel => HistoryTaskLabels[Math.Clamp(_historyTaskIndex, 0, HistoryTaskLabels.Length - 1)];
    bool HistoryAtInstance => _historyDepthIndex >= HistoryDepthLabels.Length - 1;
    bool HistoryAllTasksComplete => _historyCompletedTasks.Count >= HistoryTaskLabels.Length;

    void EnterGeonaphHistoryCampaign()
    {
        _historyDepthIndex = 0;
        _historyTaskIndex = 0;
        _historyContextOpen = false;
        _historyCompletedTasks.Clear();
        _stage = Stage.HistoryCampaign;
        _message = "Geonaph history begins at the oldest installed factual node: West Turkana → Lomekwi 3 → LOM3. Facts are fixed; reconstruction and fiction are labeled separately.";
    }

    void HistoryApplyX(int direction)
    {
        if (!HistoryAtInstance || direction == 0) return;
        _historyTaskIndex = Wrap(_historyTaskIndex + Math.Sign(direction), HistoryTaskLabels.Length);
        _message = $"Historical task: {HistoryTaskLabel}.";
    }

    void HistoryApplyY(int direction)
    {
        if (direction == 0) return;
        _historyDepthIndex = Math.Clamp(_historyDepthIndex - Math.Sign(direction), 0, HistoryDepthLabels.Length - 1);
        _historyContextOpen = false;
        _message = $"{HistoryDepthLabel} selected.";
    }

    void HistoryPressLeft()
    {
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
        _historyContextOpen = !_historyContextOpen;
        _message = _historyContextOpen
            ? "Context opened. Original language status, translation status, fact, reconstruction, fiction, and sources remain separated."
            : "Context closed.";
    }

    void HistoryGoBack()
    {
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
