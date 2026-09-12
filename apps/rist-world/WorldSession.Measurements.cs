namespace RistWorld;

public sealed partial class WorldSession
{
    const double MinMeasurementPerCell = 0.000001d;
    const double MaxMeasurementPerCell = 1_000_000_000d;

    public bool IsMeasurefict { get; private set; }
    public string MeasurefictSingular { get; private set; } = "";
    public string MeasurefictPlural { get; private set; } = "";
    public string MeasurefictAbbreviation { get; private set; } = "";
    public string MeasurementKind => IsMeasurefict ? "measurefict" : "physical";

    public string MeasurementUnitName(double value = 2d)
    {
        if (!IsMeasurefict) return DistanceUnit;
        if (!string.IsNullOrWhiteSpace(MeasurefictAbbreviation)) return MeasurefictAbbreviation;
        return Math.Abs(value - 1d) < 0.0000001d ? MeasurefictSingular : MeasurefictPlural;
    }

    public string MeasurementCellSummary => IsMeasurefict
        ? $"1 cell = {FormatMeasurementNumber(GridDistance)} {MeasurementUnitName(GridDistance)}"
        : $"1 cell = {FormatMeasurementNumber(GridDistance)} {DistanceUnit}";

    public bool SetMeasurefict(string? singular, string? plural, string? abbreviation, double unitsPerCell)
    {
        if (EncounterActive) return false;

        singular = NormalizeMeasurefictText(singular, 48);
        if (singular.Length == 0) return false;
        plural = NormalizeMeasurefictText(plural, 48);
        if (plural.Length == 0) plural = singular + "s";
        abbreviation = NormalizeMeasurefictText(abbreviation, 12);
        unitsPerCell = Math.Clamp(unitsPerCell, MinMeasurementPerCell, MaxMeasurementPerCell);

        var unitToken = abbreviation.Length > 0 ? abbreviation : singular;
        if (IsMeasurefict
            && string.Equals(MeasurefictSingular, singular, StringComparison.Ordinal)
            && string.Equals(MeasurefictPlural, plural, StringComparison.Ordinal)
            && string.Equals(MeasurefictAbbreviation, abbreviation, StringComparison.Ordinal)
            && string.Equals(DistanceUnit, unitToken, StringComparison.Ordinal)
            && Math.Abs(GridDistance - unitsPerCell) < 0.0000000001d)
            return true;

        IsMeasurefict = true;
        MeasurefictSingular = singular;
        MeasurefictPlural = plural;
        MeasurefictAbbreviation = abbreviation;
        DistanceUnit = unitToken;
        GridDistance = unitsPerCell;
        GridCalibrationZoom = Math.Max(ViewZoom, .01);
        Notify();
        return true;
    }

    void RestoreMeasurefict(string? singular, string? plural, string? abbreviation, double unitsPerCell)
    {
        singular = NormalizeMeasurefictText(singular, 48);
        if (singular.Length == 0)
        {
            RestorePhysicalMeasurement("km", 1d);
            return;
        }
        plural = NormalizeMeasurefictText(plural, 48);
        if (plural.Length == 0) plural = singular + "s";
        abbreviation = NormalizeMeasurefictText(abbreviation, 12);
        IsMeasurefict = true;
        MeasurefictSingular = singular;
        MeasurefictPlural = plural;
        MeasurefictAbbreviation = abbreviation;
        DistanceUnit = abbreviation.Length > 0 ? abbreviation : singular;
        GridDistance = Math.Clamp(unitsPerCell, MinMeasurementPerCell, MaxMeasurementPerCell);
    }

    void RestorePhysicalMeasurement(string unit, double distance)
    {
        IsMeasurefict = false;
        MeasurefictSingular = "";
        MeasurefictPlural = "";
        MeasurefictAbbreviation = "";
        DistanceUnit = unit;
        GridDistance = Math.Max(MinMeasurementPerCell, distance);
    }

    static string NormalizeMeasurefictText(string? value, int maxLength)
    {
        var text = (value ?? "").Trim();
        if (text.Length > maxLength) text = text[..maxLength];
        return text;
    }

    internal static string FormatMeasurementNumber(double value)
    {
        if (Math.Abs(value - Math.Round(value)) < 0.0000001d) return Math.Round(value).ToString("0");
        return value.ToString("0.######");
    }
}
