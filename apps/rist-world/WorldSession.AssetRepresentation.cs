namespace RistWorld;

/// <summary>
/// Separates world truth (placed tile identity + semantic TypeId) from the
/// representation pack (GroupId). Replacing a visual group never changes the
/// tile's original Id, PlacementId, TypeId, coordinates, depth, lock state,
/// rotation, treatment, metadata, or zone membership.
/// </summary>
public sealed partial class WorldSession
{
    public int AssetRepresentationRevision { get; private set; }

    static string IdentitySlug(string? value)
    {
        if (string.IsNullOrWhiteSpace(value)) return "unknown";
        var chars = value.Trim().ToLowerInvariant()
            .Select(ch => char.IsLetterOrDigit(ch) ? ch : '-')
            .ToArray();
        return string.Join('-', new string(chars).Split('-', StringSplitOptions.RemoveEmptyEntries));
    }

    AtlasTile? SourceAssetFor(TileItem tile) =>
        AtlasTiles.FirstOrDefault(asset => string.Equals(asset.Id, tile.Id, StringComparison.Ordinal));

    string EffectiveTypeId(AtlasTile asset) =>
        string.IsNullOrWhiteSpace(asset.TypeId) ? asset.Id : asset.TypeId.Trim();

    string EffectiveGroupId(AtlasTile asset) =>
        string.IsNullOrWhiteSpace(asset.GroupId)
            ? $"legacy:{IdentitySlug(asset.Author)}"
            : asset.GroupId.Trim();

    string EffectiveTypeId(TileItem tile)
    {
        if (!string.IsNullOrWhiteSpace(tile.TypeId)) return tile.TypeId.Trim();
        if (tile.Metadata is not null) return InferAbmTypeId(tile.Metadata);
        var source = SourceAssetFor(tile);
        return source is null ? tile.Id : EffectiveTypeId(source);
    }

    string EffectiveGroupId(TileItem tile)
    {
        if (!string.IsNullOrWhiteSpace(tile.GroupId)) return tile.GroupId.Trim();
        if (tile.Metadata is not null) return "abm:description";
        var source = SourceAssetFor(tile);
        return source is null ? "legacy:unknown" : EffectiveGroupId(source);
    }

    public string GetTileTypeId(TileItem tile) => EffectiveTypeId(tile);
    public string GetTileGroupId(TileItem tile) => EffectiveGroupId(tile);

    public IReadOnlyList<string> GetAssetGroupIds() =>
        AtlasTiles.Select(EffectiveGroupId)
            .Concat(PlacedTiles.Select(EffectiveGroupId))
            .Where(groupId => !string.IsNullOrWhiteSpace(groupId))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .OrderBy(groupId => groupId, StringComparer.OrdinalIgnoreCase)
            .ToList();

    TileItem NormalizePlacedTileIdentity(TileItem tile)
    {
        var source = SourceAssetFor(tile);
        var typeId = string.IsNullOrWhiteSpace(tile.TypeId)
            ? tile.Metadata is not null
                ? InferAbmTypeId(tile.Metadata)
                : source is null ? tile.Id : EffectiveTypeId(source)
            : tile.TypeId.Trim();
        var groupId = string.IsNullOrWhiteSpace(tile.GroupId)
            ? tile.Metadata is not null
                ? "abm:description"
                : source is not null ? EffectiveGroupId(source) : "legacy:unknown"
            : tile.GroupId.Trim();
        var placementId = string.IsNullOrWhiteSpace(tile.PlacementId)
            ? $"tile-{Guid.NewGuid():N}"
            : tile.PlacementId.Trim();

        return tile with
        {
            TypeId = typeId,
            GroupId = groupId,
            PlacementId = placementId
        };
    }

    static TileItem ApplyRepresentation(TileItem placed, AtlasTile representation, string targetGroupId) =>
        placed with
        {
            Image = representation.Image,
            SourceWidth = representation.SourceWidth,
            SourceHeight = representation.SourceHeight,
            CropX = representation.CropX,
            CropY = representation.CropY,
            CropWidth = representation.CropWidth,
            CropHeight = representation.CropHeight,
            AssetKind = representation.AssetKind,
            FrameCount = Math.Max(1, representation.FrameCount),
            FramesPerSecond = Math.Max(0, representation.FramesPerSecond),
            GroupId = targetGroupId
        };

    AssetGroupSwapResult ReplaceAssetGroupInternal(string sourceGroupId, string targetGroupId)
    {
        sourceGroupId = sourceGroupId?.Trim() ?? "";
        targetGroupId = targetGroupId?.Trim() ?? "";
        if (sourceGroupId.Length == 0 || targetGroupId.Length == 0 ||
            string.Equals(sourceGroupId, targetGroupId, StringComparison.OrdinalIgnoreCase))
            return new AssetGroupSwapResult(sourceGroupId, targetGroupId, 0, 0, 0);

        var targetByType = AtlasTiles
            .Where(asset => string.Equals(EffectiveGroupId(asset), targetGroupId, StringComparison.OrdinalIgnoreCase))
            .OrderBy(asset => asset.Id, StringComparer.Ordinal)
            .GroupBy(EffectiveTypeId, StringComparer.OrdinalIgnoreCase)
            .ToDictionary(group => group.Key, group => group.First(), StringComparer.OrdinalIgnoreCase);

        StoreCurrentSpatialPage();

        var matched = 0;
        var replaced = 0;
        var missing = 0;
        foreach (var address in _terrainByAddress.Keys.ToList())
        {
            var updated = new List<TileItem>(_terrainByAddress[address].Count);
            foreach (var rawTile in _terrainByAddress[address])
            {
                var tile = NormalizePlacedTileIdentity(rawTile);
                if (!string.Equals(EffectiveGroupId(tile), sourceGroupId, StringComparison.OrdinalIgnoreCase))
                {
                    updated.Add(tile);
                    continue;
                }

                matched++;
                if (!targetByType.TryGetValue(EffectiveTypeId(tile), out var replacement))
                {
                    missing++;
                    updated.Add(tile);
                    continue;
                }

                updated.Add(ApplyRepresentation(tile, replacement, targetGroupId));
                replaced++;
            }
            _terrainByAddress[address] = updated;
        }

        LoadCurrentSpatialPage();
        return new AssetGroupSwapResult(sourceGroupId, targetGroupId, matched, replaced, missing);
    }

    public AssetGroupSwapResult ReplaceAssetGroup(string sourceGroupId, string targetGroupId)
    {
        var result = ReplaceAssetGroupInternal(sourceGroupId, targetGroupId);
        if (result.Replaced > 0) AssetRepresentationRevision++;
        Notify();
        return result;
    }

    public AssetPackImportResult ImportAssetPack(AssetPackManifest pack, string replaceGroupId = "")
    {
        if (pack is null || string.IsNullOrWhiteSpace(pack.GroupId))
            return new AssetPackImportResult("", 0, 0, 0, 0);

        var groupId = pack.GroupId.Trim();
        var incoming = (pack.Tiles ?? [])
            .Where(asset => !string.IsNullOrWhiteSpace(asset.Id) && !string.IsNullOrWhiteSpace(asset.TypeId))
            .Select(asset => asset with { TypeId = asset.TypeId.Trim(), GroupId = groupId })
            .GroupBy(asset => asset.Id, StringComparer.Ordinal)
            .Select(group => group.Last())
            .ToList();

        foreach (var asset in incoming)
        {
            var index = AtlasTiles.FindIndex(existing => string.Equals(existing.Id, asset.Id, StringComparison.Ordinal));
            if (index >= 0) AtlasTiles[index] = asset;
            else AtlasTiles.Add(asset);
        }

        AssetGroupSwapResult swap = new(replaceGroupId?.Trim() ?? "", groupId, 0, 0, 0);
        if (!string.IsNullOrWhiteSpace(replaceGroupId))
            swap = ReplaceAssetGroupInternal(replaceGroupId, groupId);

        if (incoming.Count > 0 || swap.Replaced > 0) AssetRepresentationRevision++;
        Notify();
        return new AssetPackImportResult(groupId, incoming.Count, swap.Matched, swap.Replaced, swap.MissingTypeMatches);
    }
}

public sealed record AssetPackManifest(string GroupId, List<AtlasTile> Tiles, string Name = "");
public sealed record AssetGroupSwapResult(string SourceGroupId, string TargetGroupId, int Matched, int Replaced, int MissingTypeMatches);
public sealed record AssetPackImportResult(string GroupId, int Imported, int Matched, int Replaced, int MissingTypeMatches);
