namespace RistWorld;

public sealed partial class WorldSession
{
    static readonly HashSet<string> AssetRailTypes = new(StringComparer.OrdinalIgnoreCase)
    {
        "all","cards","tokens","minis","tiles","terrain","bits"
    };

    public string PublicAssetType { get; private set; } = "all";

    public void SetPublicAssetType(string type)
    {
        var normalized = string.IsNullOrWhiteSpace(type) ? "all" : type.Trim().ToLowerInvariant();
        if (!AssetRailTypes.Contains(normalized) || PublicAssetType == normalized) return;
        PublicAssetType = normalized;
        Notify();
    }
}
