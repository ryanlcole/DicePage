using Microsoft.AspNetCore.Components.Web;
using Microsoft.AspNetCore.Components.WebAssembly.Hosting;
using RistWorld;

var builder = WebAssemblyHostBuilder.CreateDefault(args);
builder.RootComponents.Add<App>("#app");
builder.RootComponents.Add<HeadOutlet>("head::after");
builder.Services.AddScoped(_ => new HttpClient { BaseAddress = new Uri(builder.HostEnvironment.BaseAddress) });
builder.Services.AddScoped<DiscordAuthClient>();
builder.Services.AddScoped<AssetRatingClient>();
builder.Services.AddScoped<AwsAuthorityClient>();
builder.Services.AddScoped<PrivateCardLibrary>();

// External AI remains owner-locked. These registrations build the defensive runtime without
// exposing a login or granting browser state authority over presence/security decisions.
builder.Services.AddScoped<ExternalAiAccessPolicy>();
builder.Services.AddScoped<AiVillainConversionPolicy>();
builder.Services.AddScoped<AiInjectionFictionPolicy>();
builder.Services.AddScoped<AiFloodDamagePolicy>();
builder.Services.AddScoped<IExternalAgentIdentityProvider, LockedExternalAgentIdentityProvider>();
builder.Services.AddScoped<IAiZonePresenceAuthority, LockedAiZonePresenceAuthority>();
builder.Services.AddScoped<ExternalAiLifeTokenLedger>();
builder.Services.AddScoped<ExternalAiWorldLedger>();
builder.Services.AddScoped<ExternalAiDefensivePipeline>();
builder.Services.AddScoped<ExternalAiActionGate>();
builder.Services.AddScoped<ExternalNpcSubmissionStore>();

builder.Services.AddScoped<WorldSession>();
await builder.Build().RunAsync();
