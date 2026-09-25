using RistWorld;

static void Check(bool condition, string message)
{
    if (!condition) throw new InvalidOperationException(message);
}

Check(WorldSession.InstanceElevationParallaxBand(0) == 0, "zero elevation band failed");
Check(WorldSession.InstanceElevationParallaxBand(9) == 0, "+9 must stay in band zero");
Check(WorldSession.InstanceElevationParallaxBand(10) == 1, "+10 must enter band one");
Check(WorldSession.InstanceElevationParallaxBand(19) == 1, "+19 must stay in band one");
Check(WorldSession.InstanceElevationParallaxBand(-9) == 0, "-9 must stay in band zero");
Check(WorldSession.InstanceElevationParallaxBand(-10) == -1, "-10 must enter band minus one");
Check(WorldSession.InstanceElevationParallaxBand(-19) == -1, "-19 must stay in band minus one");

var now = DateTimeOffset.UtcNow;
var instance = new WorldInstance(
    "instance-test",
    "world-test",
    "region-test",
    "local-test",
    "Test Instance",
    "marker-test",
    "Door Marker",
    "asset-door",
    "Door",
    4,
    4,
    "square",
    "owner",
    "local:local-test",
    WorldSession.RecursiveScopeFormat,
    45,
    now,
    now);

var state = WorldSession.DefaultInstanceMapState(instance);
var raised = new WorldInstanceCellState(
    1, 1,
    ElevationSteps: 3,
    TerrainType: "stone",
    MovementCost: 1.5,
    BlocksMovement: false,
    BlocksSight: false,
    Tags: "stairs",
    Notes: "raised landing");
var east = new WorldInstanceCellState(2, 1, ElevationSteps: 1);
state = state with { Cells = [raised, east] };

var topAtThree = WorldSession.InstanceSurfaceId(instance.InstanceId, 1, 1, "top", 3);
var topAtNine = WorldSession.InstanceSurfaceId(instance.InstanceId, 1, 1, "top", 9);
Check(topAtThree == topAtNine, "top surface identity changed with elevation");

var surfaces = WorldSession.InstanceSurfacesForCell(state, 1, 1);
Check(surfaces.Any(x => x.IsTop && x.SurfaceId == topAtThree), "stable top surface missing");
Check(surfaces.Any(x => x.Face == "east" && x.ElevationStep == 2), "east exposed step two missing");
Check(surfaces.Any(x => x.Face == "east" && x.ElevationStep == 3), "east exposed step three missing");
Check(!surfaces.Any(x => x.Face == "east" && x.ElevationStep == 1), "buried east step was exposed");

var loweredState = state with
{
    Cells = [new WorldInstanceCellState(1, 1, ElevationSteps: -10)]
};
var loweredSurfaces = WorldSession.InstanceSurfacesForCell(loweredState, 1, 1);
Check(loweredSurfaces.Count == 1 && loweredSurfaces[0].IsTop, "lower cell invented owned vertical surfaces");
Check(WorldSession.InstanceElevationParallaxBand(-10) == -1, "negative parallax band did not persist");

var placementId = "placement-test";
var placement = new WorldInstanceAssetPlacement(
    placementId,
    "asset-source",
    "Table",
    "image",
    1,
    1,
    topAtThree,
    Tier: 2,
    Layer: 10,
    Opacity: .75,
    Visible: true,
    Locked: false,
    LinkedGroupId: "group-a",
    PermissionResourceId: WorldSession.RecursivePermissionResourceId(placementId));
state = state with { Assets = [placement] };

var normalized = WorldSession.NormalizeInstanceMapState(instance, state);
var normalizedPlacement = normalized.Assets.Single();
Check(normalizedPlacement.Tier == 2, "Instance Tier changed during normalization");
Check(normalizedPlacement.Layer == 10, "visual Layer was capped or changed during normalization");
Check(Math.Abs(normalizedPlacement.Opacity - .75) < 0.000001, "placement opacity changed during normalization");
Check(normalized.Cells.Single(x => x.Column == 1 && x.Row == 1).TerrainType == "stone", "cell terrain rule did not persist");
Check(normalized.Cells.Single(x => x.Column == 1 && x.Row == 1).Tags == "stairs", "cell tags did not persist");

Console.WriteLine("Instance geometry runtime: all checks passed.");
