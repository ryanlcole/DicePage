namespace RistWorld;

public static class ContentAllowancePolicy
{
    public const string Version = "2026-08-31";

    public const string General = "general";
    public const string Minor = "minor";
    public const string Adult18 = "adult18";
    public const string Adult21 = "adult21";

    public static readonly ContentDescriptor[] Descriptors =
    [
        new("mature-conversation", "Mature conversation", "Adult themes, strong language, or emotionally mature discussion.", Adult18),
        new("violence-gore", "Violence / gore", "Graphic or disturbing descriptions of injury, death, or violence.", Adult18),
        new("alcohol", "Alcohol", "References to, depiction of, or role-play involving alcoholic beverages or intoxication.", Adult18),
        new("tobacco-smoking", "Smoking / tobacco", "References to, depiction of, or role-play involving smoking or tobacco use.", Adult18),
        new("drugs", "Drugs", "References to, depiction of, or role-play involving recreational or illicit drugs.", Adult18),
        new("gambling", "Gambling", "References to or role-play involving wagering or gambling activity.", Adult18),
        new("sexual-themes", "Sexual themes / references", "Sexual discussion, innuendo, romance with sexual themes, or non-explicit sexual references.", Adult21),
        new("explicit-sexual-content", "Explicit sexual content", "Explicit sexual description or role-play. This is a separate opt-in content level.", Adult21)
    ];

    public static IReadOnlyList<string> AllowedForBand(string? band)
        => band switch
        {
            Adult21 => Descriptors.Select(x => x.Id).ToArray(),
            Adult18 => Descriptors.Where(x => x.MinimumBand == Adult18).Select(x => x.Id).ToArray(),
            _ => Array.Empty<string>()
        };

    public static IReadOnlyList<string> Sanitize(string? band, IEnumerable<string>? requested, IEnumerable<string>? guardianApproved = null)
    {
        var requestedSet = new HashSet<string>(requested ?? [], StringComparer.Ordinal);
        if (band == Minor)
        {
            var guardianSet = new HashSet<string>(guardianApproved ?? [], StringComparer.Ordinal);
            requestedSet.IntersectWith(guardianSet);
            requestedSet.IntersectWith(Descriptors.Select(x => x.Id));
            return requestedSet.OrderBy(x => x, StringComparer.Ordinal).ToArray();
        }

        requestedSet.IntersectWith(AllowedForBand(band));
        return requestedSet.OrderBy(x => x, StringComparer.Ordinal).ToArray();
    }

    public static bool Allows(string? band, IEnumerable<string>? accountAllowed, string descriptorId, IEnumerable<string>? guardianApproved = null)
        => Sanitize(band, accountAllowed, guardianApproved).Contains(descriptorId, StringComparer.Ordinal);

    public static bool CampaignAllowed(
        string? band,
        IEnumerable<string>? accountAllowed,
        IEnumerable<string>? campaignDescriptors,
        IEnumerable<string>? guardianApproved = null)
    {
        var effective = new HashSet<string>(Sanitize(band, accountAllowed, guardianApproved), StringComparer.Ordinal);
        return (campaignDescriptors ?? []).All(effective.Contains);
    }

    public sealed record ContentDescriptor(string Id, string Label, string Reason, string MinimumBand);
}
