using System.Text.Json;

namespace RistWorld;

public enum RistCardPrintTarget
{
    StandardPrinter,
    CardMaker,
    ThreeDimensional
}

public sealed class RistCardPrintManifest
{
    public string Format { get; set; } = "RISTCARDPRINT";
    public int Version { get; set; } = 2;
    public RistCardPrintTarget Target { get; set; }
    public string OutputFormat { get; set; } = "tiff";
    public string CardId { get; set; } = "";
    public string CreatorProvenanceId { get; set; } = "";
    public string ManifestHash { get; set; } = "";
    public string ArtDataMark { get; set; } = "";
    public RistCardLanguage Language { get; set; } = new();
    public RistCardFace Face { get; set; } = new();
    public string RasterQuality { get; set; } = "standard";
    public string GlyphPresentation { get; set; } = "visible";
    public bool EmbedFullResolutionArtwork { get; set; }
    public bool EmbedCreatorProvenance { get; set; } = true;
    public bool PreserveTierLayerGeometry { get; set; }
    public List<RistPrintLayer> Layers { get; set; } = [];
}

public sealed class RistPrintLayer
{
    public string AssetId { get; set; } = "";
    public string Image { get; set; } = "";
    public int TierIndex { get; set; }
    public int LayerOffset { get; set; }
    public int SceneZ { get; set; }
    public double X { get; set; }
    public double Y { get; set; }
    public double Footprint { get; set; } = 1;
    public int RotationQuarterTurns { get; set; }
    public string PlacementTreatment { get; set; } = "normal";
}

public sealed partial class WorldSession
{
    public RistCardPrintManifest BuildActiveMapCardPrintManifest(RistCardPrintTarget target)
    {
        var card = JsonSerializer.Deserialize<MapCardDocument>(ExportActiveMapCardJson(), MapReadOptions)
            ?? throw new InvalidOperationException("The active map card could not be prepared for printing.");

        var creator = ComputeCreatorProvenanceId(card.OwnerAccountId);
        var layers = card.Tiles
            .Select(tile => new RistPrintLayer
            {
                AssetId = tile.Id,
                Image = tile.Image ?? "",
                TierIndex = tile.TierIndex,
                LayerOffset = tile.LayerOffset,
                SceneZ = tile.TierIndex * 10 + tile.LayerOffset,
                X = tile.X,
                Y = tile.Y,
                Footprint = Math.Clamp(1.0 / Math.Max(tile.PlacementZoom, 0.000001), 0.001, GridColumns),
                RotationQuarterTurns = tile.RotationQuarterTurns,
                PlacementTreatment = tile.PlacementTreatment
            })
            .OrderBy(x => x.SceneZ)
            .ThenBy(x => x.Y)
            .ThenBy(x => x.X)
            .ToList();

        return new RistCardPrintManifest
        {
            Target = target,
            OutputFormat = target == RistCardPrintTarget.ThreeDimensional ? "3mf" : "tiff",
            CardId = card.CardId,
            CreatorProvenanceId = creator,
            ManifestHash = card.ManifestHash,
            ArtDataMark = card.ArtDataMark,
            Language = card.Language,
            Face = card.Face,
            RasterQuality = target switch
            {
                RistCardPrintTarget.StandardPrinter => "standard",
                RistCardPrintTarget.CardMaker => "production",
                RistCardPrintTarget.ThreeDimensional => "source",
                _ => "standard"
            },
            GlyphPresentation = target switch
            {
                RistCardPrintTarget.StandardPrinter => "visible-code",
                RistCardPrintTarget.CardMaker => "integrated-art-mark",
                RistCardPrintTarget.ThreeDimensional => "physical-mark",
                _ => "visible-code"
            },
            EmbedFullResolutionArtwork = target != RistCardPrintTarget.StandardPrinter,
            EmbedCreatorProvenance = true,
            PreserveTierLayerGeometry = target == RistCardPrintTarget.ThreeDimensional,
            Layers = layers
        };
    }

    public string ExportActiveMapCardPrintManifestJson(RistCardPrintTarget target) =>
        JsonSerializer.Serialize(BuildActiveMapCardPrintManifest(target), MapWriteOptions);
}
