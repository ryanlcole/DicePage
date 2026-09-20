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
Console.WriteLine("Private source ownership, isolation, persistence, and world-switch checks passed.");

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
