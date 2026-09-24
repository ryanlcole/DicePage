using System.Text.Json;
using RistWorld;

static void Check(bool condition, string message) { if (!condition) throw new Exception(message); }
var session = new WorldSession();
using var document = JsonDocument.Parse("{\"worldId\":\"private-test\",\"userLayers\":[{\"id\":\"image-1\"}]}");
Check(PrivateWorldSourcePolicy.MatchesOwner("private-test", "account-1", "private-test", "account-1"), "valid private owner rejected");
Check(!PrivateWorldSourcePolicy.MatchesOwner("private-test", "account-1", "private-test", "other"), "foreign account accepted");
Check(!PrivateWorldSourcePolicy.MatchesOwner("private-test", "account-1", "other", "account-1"), "foreign world accepted");
Check(!PrivateWorldSourcePolicy.MatchesOwner(WorldSession.GeonaphWorldId, "account-1", WorldSession.GeonaphWorldId, "account-1"), "private descriptor elevated Shaelvien authority");
session.Auth.Descriptor = new("private-test", "account-1");
await session.SaveWorldBuilderSourceAsync(document.RootElement);
Check(session.Auth.UploadKey == "worlds/private-test/worldbuilder-source.json", "private write escaped world namespace");
Check(session.Authority.Writes == 0, "private save changed shared database");
var restored = await session.LoadWorldBuilderSourceAsync();
Check(restored?.State?.GetProperty("userLayers")[0].GetProperty("id").GetString() == "image-1", "private state did not round trip");
Check(session.Authority.Reads == 0, "private read used shared database");
session.Auth.Descriptor = new("private-test", "other");
session.PrivateOwner = true;
try { await session.SaveWorldBuilderSourceAsync(document.RootElement); throw new Exception("stale private grant accepted"); }
catch (UnauthorizedAccessException) { }
session.PrivateOwner = false;
session.WorldId = WorldSession.GeonaphWorldId;
session.Auth.Descriptor = new(WorldSession.GeonaphWorldId, "account-1");
await session.LoadWorldBuilderSourceAsync();
Check(session.Authority.Reads == 1, "Shaelvien source did not use shared authority");
session.WorldId = "private-test";
session.Auth.Descriptor = new("private-test", "account-1");
session.Auth.OnDescriptorRead = () => session.WorldId = "different-world";
try { await session.SaveWorldBuilderSourceAsync(document.RootElement); throw new Exception("world-switch race accepted"); }
catch (UnauthorizedAccessException) { }
Check(session.Authority.Writes == 0, "race wrote to shared world");
using var parentDocument = JsonDocument.Parse("""
{
    "worldId":"private-test",
    "tierImages":["full-private-world.png"],
    "sourceTileIndex":[
        {"cellIndex":31,"tierIndex":0,"layerOffset":0,"image":"claimed.webp"},
        {"cellIndex":32,"tierIndex":0,"layerOffset":0,"image":"unclaimed.webp"}
    ],
    "userLayers":[
        {"id":"world-road","tier":0,"layer":0,"x":0.05,"y":0.05,"kind":"image","originalSrc":"road.webp"},
        {"id":"private-city","regionId":"private-region","tier":0,"worldLayer":0,"layer":0,"regionLayer":1,"z100":1,"x":0.05,"y":0.05,"kind":"image","originalSrc":"city.webp"},
        {"id":"foreign-city","regionId":"another-region","tier":0,"worldLayer":0,"layer":0,"regionLayer":1,"z100":1,"x":0.05,"y":0.05}
    ]
}
""");
var projected = RegionSourceProjector.Project(
    "private-test", "private-region", "world:private-test", 0,
    [31], "square", [0], parentDocument.RootElement);
Check(projected.GetProperty("projection").GetString() == "region-world-z-v2", "private region projection version is wrong");
Check(projected.GetProperty("sourceTileIndex").GetArrayLength() == 1, "private projection leaked unclaimed tile");
Check(projected.GetProperty("sourceTileIndex")[0].GetProperty("image").GetString() == "claimed.webp", "wrong private cell selected");
Check(!projected.TryGetProperty("tierImages", out _), "private projection leaked full world bitmap");
Check(projected.GetProperty("sourceUserLayers").GetArrayLength() == 1, "private projection lost locked WorldBuilder layer");
Check(projected.GetProperty("userLayers").GetArrayLength() == 1, "private projection leaked another region's overlay");
Check(projected.GetProperty("userLayers")[0].GetProperty("z100").GetInt32() == 1, "private region exact Z is wrong");
Check(projected.GetProperty("userLayers")[0].GetProperty("parallaxMode").GetString() == "anchored",
    "private region overlay received independent parallax");
Check(projected.GetProperty("requiresRasterIndex").GetBoolean() == false, "indexed private claim incorrectly rejected");

using var editedLayers = JsonDocument.Parse("""
[{"id":"private-city","x":0.05,"y":0.05,"tier":0,"worldLayer":4,"layer":4,"regionLayer":7,"z100":407,"regionId":"private-region"}]
""");
var merged = RegionSourceProjector.MergeRegionLayers(
    "private-test", "private-region", "world:private-test", 0,
    [31], "square", parentDocument.RootElement, editedLayers.RootElement);
var mergedRegion = merged.GetProperty("userLayers").EnumerateArray()
    .Single(x => x.TryGetProperty("regionId", out var id) && id.GetString() == "private-region");
Check(mergedRegion.GetProperty("z100").GetInt32() == 407, "private region hundredth Z did not persist");
Check(mergedRegion.GetProperty("worldLayer").GetInt32() == 4, "private region World Z did not persist");
Check(mergedRegion.GetProperty("regionLayer").GetInt32() == 7, "private region fractional layer did not persist");
Check(mergedRegion.GetProperty("parallaxMode").GetString() == "anchored", "private region overlay drifted into parallax");

using var leakedLayers = JsonDocument.Parse("""
[{"id":"foreign-placement","x":0.95,"y":0.95,"tier":0,"worldLayer":0,"layer":0,"regionLayer":1,"z100":1}]
""");
try
{
    RegionSourceProjector.MergeRegionLayers(
        "private-test","private-region","world:private-test",0,
        [31],"square",parentDocument.RootElement,leakedLayers.RootElement);
    throw new Exception("private object escaped claimed source-cell boundary");
}
catch (UnauthorizedAccessException) { }
Console.WriteLine("Private source, selected-coordinate projection and exact region Z isolation checks passed.");

namespace RistWorld
{
    public sealed record WorldRelationshipDescriptor(string WorldId, string OwnerAccountId);
    public sealed record TestRegion(string RegionId);
    public sealed partial class WorldSession
    {
        public const string GeonaphWorldId = "shaelvien-geonaph-alpha-001";
        public bool IsLoggedIn { get; set; } = true;
        public bool HasActiveWorld => WorldId.Length > 0;
        public string WorldId { get; set; } = "private-test";
        public string WorldOwnerAccountId { get; set; } = "account-1";
        public bool HasTrustedWorldBuilderAuthority { get; set; } = true;
        private bool _trustedPrivateWorldOwner;
        public bool PrivateOwner { set => _trustedPrivateWorldOwner = value; }
        private readonly FakeAuth auth = new();
        public FakeAuth Auth => auth;
        public AwsAuthorityClient Authority { get; } = new();
        private readonly List<TestRegion> _regions = [];
        private bool CanEditRegion(TestRegion region) => false;
        private Task<AwsAuthorityClient?> GetClaimAuthorityClientAsync() => Task.FromResult<AwsAuthorityClient?>(Authority);
        private static readonly JsonSerializerOptions MapWriteOptions = new();
    }
    public sealed class FakeAuth
    {
        public string SessionToken { get; set; } = "test-session";
        public WorldRelationshipDescriptor? Descriptor { get; set; }
        public Action? OnDescriptorRead { get; set; }
        public string? UploadKey { get; private set; }
        private string? saved;
        public Task<T?> DownloadJsonAsync<T>(string key)
        {
            if (typeof(T) == typeof(WorldRelationshipDescriptor))
            {
                OnDescriptorRead?.Invoke();
                return Task.FromResult((T?)(object?)Descriptor);
            }
            return Task.FromResult(saved is null ? default : JsonSerializer.Deserialize<T>(saved));
        }
        public Task UploadTextAsync(string key, string text, string contentType)
        { UploadKey = key; saved = text; return Task.CompletedTask; }
    }
    public sealed class AwsAuthorityClient
    {
        public sealed record WorldSource(string WorldId, JsonElement? State, string UpdatedAtUtc = "");
        public int Reads { get; private set; }
        public int Writes { get; private set; }
        public Task<WorldSource?> GetWorldSourceAsync(string worldId) { Reads++; return Task.FromResult<WorldSource?>(null); }
        public Task<WorldSource?> SaveWorldSourceAsync(string worldId, JsonElement state) { Writes++; return Task.FromResult<WorldSource?>(null); }
        public Task<WorldSource?> SaveWorldRegionMapAsync(string worldId, string regionId, JsonElement layers) => throw new NotSupportedException();
    }
}
