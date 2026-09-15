namespace RistWorld;

public sealed partial class WorldSession
{
    static double AccessibilityCellCenter(int cell, int count)
    {
        count = Math.Max(1, count);
        var clamped = Math.Clamp(cell, 1, count);
        return (clamped - 0.5d) / count;
    }

    public bool PlaceAccessibleStaged(string stagedKey, int column, int row, out string message)
    {
        message = "The staged asset could not be placed.";
        var staged = StagedAssets.FirstOrDefault(x => string.Equals(x.Key, stagedKey, StringComparison.Ordinal));
        if (staged is null)
        {
            message = "The selected staged asset is no longer available.";
            return false;
        }
        if (Role == "PC" && staged.ApprovalStatus != HandCard.Approved)
        {
            message = $"{staged.Name} is awaiting GameMaster approval.";
            return false;
        }
        if (staged.Kind == "tile" && !CanEditTiles)
        {
            message = "Tile placement requires GameMaster worldbuilder authority.";
            return false;
        }

        var x = AccessibilityCellCenter(column, ViewerGridColumns);
        var y = AccessibilityCellCenter(row, ViewerGridRows);
        var safeColumn = Math.Clamp(column, 1, Math.Max(1, ViewerGridColumns));
        var safeRow = Math.Clamp(row, 1, Math.Max(1, ViewerGridRows));

        if (staged.Kind == "tile")
        {
            PlaceStaged(staged, x, y, Math.Max(ViewZoom, .01));
        }
        else
        {
            Pieces.Add(new PieceItem(
                staged.Kind,
                x,
                y,
                staged.Kind == "pin" ? Math.Max(ViewZoom, .01) : 1,
                staged.Name,
                CubeX,
                CubeY,
                CubeZ,
                PlaneIndex,
                TierIndex,
                LayerOffset));
            Notify();
        }

        message = $"Placed {staged.Name} at column {safeColumn}, row {safeRow}. {WorldCoordinateLabel}.";
        return true;
    }

    public async Task<PieceMutationResult> MoveAccessiblePieceAsync(int pieceIndex, int column, int row)
    {
        if (pieceIndex < 0 || pieceIndex >= Pieces.Count)
            return new(false, "Choose an existing piece first.");

        var piece = Pieces[pieceIndex];
        var x = AccessibilityCellCenter(column, ViewerGridColumns);
        var y = AccessibilityCellCenter(row, ViewerGridRows);
        var safeColumn = Math.Clamp(column, 1, Math.Max(1, ViewerGridColumns));
        var safeRow = Math.Clamp(row, 1, Math.Max(1, ViewerGridRows));
        var result = await MovePieceAuthorizedAsync(piece, x, y);
        if (!result.Success) return result;

        var name = string.IsNullOrWhiteSpace(piece.Label) ? piece.Kind : piece.Label;
        return new(true, $"Moved {name} to column {safeColumn}, row {safeRow}.");
    }

    public bool PlaceAccessibleFeature(AssetByMetadata metadata, int column, int row, out string message)
    {
        message = "The world feature could not be added.";
        if (!CanEditTiles)
        {
            message = "Semantic world editing requires GameMaster worldbuilder authority.";
            return false;
        }
        if (metadata is null || string.IsNullOrWhiteSpace(metadata.AssetType))
        {
            message = "Feature type is required.";
            return false;
        }

        var x = AccessibilityCellCenter(column, ViewerGridColumns);
        var y = AccessibilityCellCenter(row, ViewerGridRows);
        var safeColumn = Math.Clamp(column, 1, Math.Max(1, ViewerGridColumns));
        var safeRow = Math.Clamp(row, 1, Math.Max(1, ViewerGridRows));
        PlaceAbmTile(metadata, x, y, Math.Max(ViewZoom, .01));
        message = $"Added {DescribeAbm(metadata)} at column {safeColumn}, row {safeRow}.";
        return true;
    }

    public string AccessibilityWorldSummary()
    {
        if (!HasActiveWorld) return "No world is loaded.";
        var descriptions = GetDescriptionOnlyMap();
        var featureText = descriptions.Count == 0
            ? "No authored world features are present at this location."
            : $"There are {descriptions.Count} authored world features at this location.";
        var pieceText = Pieces.Count == 0
            ? "No pieces are placed here."
            : $"There are {Pieces.Count} placed pieces here.";
        return $"{WorldDisplayName}. {WorldCoordinateLabel}. {Layer} scale. Viewer grid {ViewerGridSizeLabel}. {featureText} {pieceText}";
    }
}
