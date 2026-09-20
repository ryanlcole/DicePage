from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ROOT / "Components"


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise SystemExit(f"launch contract failed: {label}")


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise SystemExit(f"launch contract failed: {label}")


def main() -> None:
    authenticated = (COMPONENTS / "AuthenticatedWorld.razor").read_text(encoding="utf-8")
    shell = (COMPONENTS / "PublicAlphaShell.razor").read_text(encoding="utf-8")
    gate = (COMPONENTS / "WorldGate.razor").read_text(encoding="utf-8")
    router = (COMPONENTS / "TaskWorkspaceRouter.razor").read_text(encoding="utf-8")
    perceiver = (COMPONENTS / "PerceiverWorkspace.razor").read_text(encoding="utf-8")
    perceiver_player = (ROOT / "wwwroot" / "perceiver-player.js").read_text(encoding="utf-8")
    host = (COMPONENTS / "WorldBuilderGeonaphHost.razor").read_text(encoding="utf-8")
    ticker = (COMPONENTS / "SiteTicker.razor").read_text(encoding="utf-8")
    index = (ROOT / "wwwroot" / "index.html").read_text(encoding="utf-8")
    game_start = (ROOT / "wwwroot" / "game-start-screen.js").read_text(encoding="utf-8")
    public_entry = (ROOT.parents[1] / "site" / "relic-home" / "Play" / "index.html").read_text(encoding="utf-8")
    marketing_home = (ROOT.parents[1] / "site" / "relic-home" / "index.html").read_text(encoding="utf-8")
    device = (ROOT / "wwwroot" / "device-settings.js").read_text(encoding="utf-8")
    rist = (ROOT / "wwwroot" / "rist.js").read_text(encoding="utf-8")
    compat = (ROOT / "wwwroot" / "auth-session-compat.js").read_text(encoding="utf-8")
    discord = (ROOT / "DiscordAuthClient.cs").read_text(encoding="utf-8")
    world_authority = (ROOT / "WorldSession.WorldAuthority.cs").read_text(encoding="utf-8")
    platform_authority = (ROOT.parents[1] / "infra" / "aws" / "rist-platform-authority" / "app.py").read_text(encoding="utf-8")
    auth_template = (ROOT.parents[1] / "infra" / "aws" / "rist-discord-storage.yml").read_text(encoding="utf-8")
    auth_workflow = (ROOT.parents[1] / ".github" / "workflows" / "deploy-rist-discord-auth.yml").read_text(encoding="utf-8")

    # Provider session -> Press Start -> environment choice. The user chooses
    # Shaelvien or one of their sandboxes; MMO-world navigation happens only after
    # entering the Shaelvien environment.
    require(authenticated, "@if(!_launchStarted)", "authenticated shell must show Press Start")
    require(authenticated, "PRESS START", "authenticated shell must expose the start user gesture")
    require(authenticated, "ristPrivacy.set", "Press Start must present storage/privacy choice")
    require(authenticated, 'Http.GetStringAsync("terms.html")', "terms gate must load the canonical Terms of Service inline")
    require(authenticated, 'Http.GetStringAsync("privacy.html")', "terms gate must load the canonical Privacy Policy inline")
    require(authenticated, "ExistingAdultConsentGrandfatherCutoffUtc", "existing adult accounts created during the broken consent rollout must be grandfathered")
    require(authenticated, "account.AgeAtSignup is >=18", "consent grandfathering must be adult-only")
    require(authenticated, "account.CreatedAtUtc < ExistingAdultConsentGrandfatherCutoffUtc", "consent grandfathering must be limited to accounts created before the cutoff")
    require(authenticated, "!IsGrandfatheredAdultConsentAttempt(Auth.Account)", "new accounts must still receive the terms gate")
    require(authenticated, '@onscroll="OnPolicyScrollAsync"', "terms gate must observe policy scrolling")
    require(authenticated, '@onchange="OnTermsChangedAsync"', "agreement checkbox must re-check policy completion when mobile scroll events are missed")
    forbid(authenticated, 'disabled="@(!_policiesRead)"', "agreement checkbox must remain tappable for mobile end-of-scroll recovery")
    require(authenticated, 'class="rist-policy-complete"', "policy end must expose an explicit mobile-safe completion control")
    require(authenticated, '@onclick="ConfirmPoliciesReadAsync"', "policy completion control must unlock consent without relying on scroll metrics")
    require(authenticated, "I REACHED THE END — UNLOCK AGREEMENT", "policy completion control must clearly describe its action")
    require(authenticated, "_policiesRead=true;", "explicit policy completion must satisfy the read gate")
    require(authenticated, 'disabled="@(!_policiesRead || !_termsChecked || _savingTerms)"', "agreement submission must remain locked until scroll completion and consent")
    require(authenticated, "Please read both policies through to the end before agreeing.", "server-side consent handler must enforce policy scroll completion")
    require(authenticated, "I have read and agree to the Terms of Service and Privacy Policy.", "terms gate must name the policies being accepted")
    require(rist, "window.ristLegalConsent", "base runtime must provide legal consent scroll authority")
    require(rist, "el.scrollHeight-el.clientHeight-el.scrollTop", "legal consent authority must detect the true end of the scroll region")
    require(rist, ".rist-policy-end", "legal consent authority must recognize the visible policy-end sentinel")
    require(rist, "Math.max(48", "legal consent authority must tolerate mobile scroll rounding and momentum")
    require(authenticated, "ristLaunch.pressStart", "Press Start must use the canonical launch authority")
    forbid(authenticated, "HARD REFRESH", "authenticated Press Start must stay focused on launch and permissions")
    require(authenticated, "else if(!_launchWorldChosen)", "environment choice must follow Press Start")
    require(authenticated, "Choose Your Environment", "launch must offer Shaelvien or RIST")
    require(authenticated, "<strong>SHAELVIEN</strong>", "launch must expose Shaelvien as the MMO environment")
    require(authenticated, "<strong>RIST</strong>", "launch must expose RIST as the sandbox environment")
    require(authenticated, 'class="rist-environment-option rist-sandbox"', "RIST environment control must use a collision-safe sandbox class")
    require(authenticated, ".rist-environment-option.shaelvien,.rist-environment-option.rist-sandbox", "Shaelvien and RIST environment controls must share the same visual treatment")
    forbid(authenticated, 'class="rist-environment-option rist"', "environment controls must not reuse the generic RIST class")
    require(authenticated, "await LoadLaunchWorldsAsync();", "Press Start must load Shaelvien availability before environment choice")
    require(authenticated, "EnterShaelvienAsync", "launch must provide a Shaelvien environment choice")
    require(authenticated, "OpenRistSandboxChooser", "RIST choice must open the sandbox chooser instead of listing sandboxes on the environment screen")
    require(authenticated, 'OnContinue="CompleteLaunchSandboxSelectionAsync"', "successful RIST sandbox selection must complete environment launch")
    require(authenticated, 'OnClose="CloseLaunchSandboxChooser"', "sandbox chooser cancel must return to Shaelvien-or-RIST choice")
    require(authenticated, "directory.Worlds.Where(WorldSession.IsMmoWorldReference)", "Shaelvien launch state must identify MMO worlds separately")
    forbid(authenticated, "_launchSandboxWorlds", "top-level environment screen must not duplicate sandbox-world navigation")
    require(authenticated, '<PublicAlphaShell @ref="_alphaShell" />', "landing shell must render after an environment is selected")
    require(authenticated, "_launchWorldChosen=true;", "successful environment selection must unlock landing")
    require(rist, "pressStart:async", "base runtime must own Press Start activation")
    require(rist, "ristDeviceCapabilities", "Press Start must use the device capability authority")
    require(device, "initializeAtStart", "device settings must initialize saved/default experience preferences")
    require(device, "requestAtStart", "device capability setup must originate from Press Start")
    require(device, "getUserMedia", "Press Start capability setup must request microphone access")
    require(device, "unlockAudio", "Press Start must unlock browser audio from the user gesture")
    require(device, "ristMotionPermission", "Press Start capability setup must request motion for Parallax")
    require(device, "AUDIO_KEY", "audio preference must have one canonical key")
    require(device, "VIDEO_KEY", "video preference must have one canonical key")

    # WorldGate paints before directory/network/storage work.
    require(gate, "protected override void OnParametersSet()", "world chooser must initialize synchronously")
    require(gate, "_loading=true;", "world chooser must expose a visible loading state")
    require(gate, "_loadRequested=true;", "world chooser must defer directory work until after first render")
    require(gate, "protected override async Task OnAfterRenderAsync", "world chooser must load after first paint")
    require(gate, "await RefreshWorldsAsync();", "world chooser must load its directory after first paint")
    require(gate, "OnContinue.HasDelegate", "sandbox chooser must distinguish successful selection from cancel/back")
    require(gate, "CompleteSelectionAsync()", "sandbox chooser must report successful load/create/import separately")
    forbid(gate, "protected override async Task OnParametersSetAsync()", "world chooser must not block first paint")

    # Landing keeps environment choice and nested MMO navigation separate.
    # Top level is Shaelvien or a sandbox; MMO property worlds only appear after
    # entering Shaelvien. Creation/import stays isolated in sandbox management.
    require(shell, "_workspaceOpen=false;", "landing must start at hub")
    require(shell, "_worldGateOpen=false;", "landing must not open a second initial world gate")
    require(shell, 'await PersistWorkspaceAsync("hub");', "landing must persist hub as launch workspace")
    forbid(shell, "RestorableWorkspaces.Contains(storedWorkspace)", "old workspace restoration must not bypass world-first launch")
    forbid(shell, "ApplyWorkspace(storedWorkspace)", "old workspace restoration must not bypass landing")
    require(shell, "@inject DiscordAuthClient Auth", "landing must own authenticated account actions")
    require(shell, "<strong>SWITCH USER</strong>" if "<strong>SWITCH USER</strong>" in shell else "SWITCH USER", "landing must expose Switch User")
    require(shell, "<strong>SIGN OUT</strong>" if "<strong>SIGN OUT</strong>" in shell else "SIGN OUT", "landing must expose Sign Out")
    require(shell, "async Task SwitchUserAsync()", "Switch User must have an explicit handler")
    require(shell, "async Task SignOutAsync()", "Sign Out must have an explicit handler")
    require(shell, 'Navigation.NavigateTo("/Play/index.html",forceLoad:true);', "Switch User must return to account selection")
    require(shell, 'Navigation.NavigateTo("/",forceLoad:true);', "Sign Out must return to the public home")
    require(shell, "await Auth.LogoutAsync();", "landing account actions must clear the provider session")
    require(shell, 'label for="landing-mmo-world-select">MMO WORLD</label>', "Shaelvien landing must navigate only MMO worlds")
    require(shell, 'label for="landing-sandbox-world-select">SANDBOX WORLD</label>', "RIST landing must navigate only sandbox worlds")
    require(shell, "launcher-mmo-selectbar", "Shaelvien must expose nested MMO-world navigation")
    require(shell, "SHAELVIEN · ENDEMAR", "MMO selector must include the Shaelvien/Endemar root")
    require(shell, "AccessibleMmoWorlds", "MMO selector must use accessible Shaelvien property worlds")
    require(shell, "Session.MmoParcels", "MMO worlds must come from Shaelvien parcel authority, not the sandbox world directory")
    require(shell, "Session.CanAccessMmoParcel", "MMO navigation must respect parcel access authority")
    require(shell, "_sandboxWorlds.AddRange(directory.Worlds", "sandbox worlds must come from the account world directory")
    require(shell, ".Where(WorldSession.IsSandboxWorldReference)", "sandbox navigation must exclude MMO worlds")
    forbid(shell, "CREATE / IMPORT…", "landing selectors must navigate only; create/import belongs in sandbox management")
    require(shell, "SANDBOX WORLDS", "landing must expose sandbox management separately")
    require(gate, "CHOOSE A SANDBOX WORLD", "world gate must be the sandbox chooser")
    require(gate, "directory.Worlds.Where(WorldSession.IsSandboxWorldReference)", "sandbox chooser must exclude MMO worlds")
    forbid(gate, "SHAELVIEN MMO · PROPERTY SPACE", "sandbox chooser must not present MMO property-space controls")

    # Experience activation belongs to Press Start; landing stays clean.
    require(index, '<script src="device-settings.js"></script>', "device settings authority must load before Blazor")
    forbid(game_start, "parallax-toggle", "pre-auth login must not expose a Parallax toggle")
    forbid(public_entry, "parallax-toggle", "public sign-in entry must not expose a Parallax toggle")
    forbid(public_entry, "PARALLAX_PREF", "public sign-in entry must not run Parallax before authentication")
    forbid(public_entry, "requestMotionPermission", "public sign-in entry must not request motion before authentication")
    forbid(shell, 'class="launcher-device-setup"', "landing must not ask for Parallax/motion setup again")
    require(shell, "ToggleAudioAsync", "audio preference must remain editable from Start menu")
    require(shell, "ToggleVideoAsync", "video preference must remain editable from Start menu")
    require(shell, "HardRefreshAsync", "authenticated Start menu must expose hard refresh recovery")
    require(shell, "ToggleParallaxAsync", "Parallax control must remain available after authentication in Settings")
    require(shell, "PARALLAX @(_parallaxEnabled?", "authenticated Settings must render the Parallax state")
    require(rist, "navigator.serviceWorker.getRegistrations", "hard refresh must unregister app service workers")
    require(rist, "caches.keys()", "hard refresh must clear app Cache Storage")
    require(rist, "cache:'reload'", "hard refresh must revalidate stable app resources")

    # The archived static Perceiver prototype stays unpublished. The authenticated
    # application may expose the live Perceiver workspace, which must consume the
    # canonical world/database tier source rather than the archived static route.
    forbid(marketing_home, "/perceiver/", "public home must not link the archived Perceiver prototype")
    require(shell, "OpenPerceiver", "authenticated launcher must expose the live Perceiver workspace")
    require(shell, "<strong>PERCEIVER</strong>", "authenticated launcher must render a Perceiver card")
    require(router, '<PerceiverWorkspace OnStartMenu="OnStartMenu" OnHome="OnHome" />', "Perceiver must route through the authenticated workspace router")
    require(perceiver, "Session.LoadWorldBuilderSourceAsync()", "Perceiver must source canonical world tiers from the database")
    require(perceiver, 'TryGetProperty("tierImages"', "Perceiver must consume database tier image references")
    require(perceiver_player, "STEP_SEQUENCE", "Perceiver must own a deterministic tier playback sequence")
    require(perceiver_player, "Tier 1 + Tier 2 + Tier 3", "Perceiver proof must include the all-tier state")
    require(perceiver_player, "deviceorientation", "Perceiver must react to device tilt when permission is available")

    # One universal World Builder. Geonaph differs only by seed data.
    require(router, '<WorldBuilderGeonaphHost OnStartMenu="OnStartMenu" OnHome="OnHome" />', "all worlds must use the universal builder host and return Home without reloading Press Start")
    forbid(router, '<WorldBuilderStudio OnStartMenu="OnStartMenu" />', "normal worlds must not route to a second builder")
    require(host, 'var seed=Session.IsGeonaphWorld?"geonaph":"empty";', "Geonaph may differ only by seed data")
    require(host, "worldId={worldId}", "builder must receive selected world identity")

    # Ticker is world-scoped and absent before world choice.
    require(ticker, "@if(Session.HasActiveWorld)", "ticker must stay hidden until a world is active")
    require(ticker, 'rist.worldbuilder.ticker.buttons.v1.{Session.WorldId}', "ticker settings must be world-scoped")

    # Authentication session lifetime belongs to provider/server.
    require(rist, "installSessionExpiry", "browser must honor provider-issued session expiry")
    require(rist, "rist.session.expiresAt", "browser must store provider expiry")
    require(rist, "rist.session.provider", "browser must store provider identity")
    forbid(rist, "idleMs", "core auth must not impose its own idle duration")
    forbid(rist, "installIdleExpiry", "core auth must not install a competing idle timer")
    forbid(compat, "lastActivity", "compat auth must not implement activity expiry")
    forbid(compat, "installIdleExpiry", "compat auth must not install a competing idle timer")
    require(compat, "installSessionExpiry", "compat auth must delegate to provider expiry")
    require(auth_template, '"provider": "discord"', "Discord sessions must identify their provider")
    require(auth_template, '"sessionExpiresAt": session_item["expiresAt"]', "Discord handoff must expose authoritative expiry")
    require(auth_template, "Default: https://relicgamemaster.com/Play/index.html", "auth template must default to the canonical Play entry")
    require(auth_workflow, "PRODUCTION_ENTRY_URL: https://relicgamemaster.com/Play/index.html", "production Discord auth must return through the canonical Play entry")
    forbid(auth_workflow, "PRODUCTION_GAME_URL: https://relicgamemaster.com/Game/index.html", "Discord auth must not bypass the Play entry")
    require(world_authority, "GetProfileAsync()", "world authority must read trusted platform-owner status")
    require(world_authority, "profile?.PlatformOwner == true", "platform owner must receive trusted worldbuilder authority")
    require(world_authority, "_trustedPlatformOwner || IsTrustedWorldBuilderRole", "worldbuilder authority must accept platform owner or GM/owner membership")
    require(platform_authority, '"effectiveAuthority": "platformOwner"', "authority API must expose platform owner as effective world owner")
    require(authenticated, "await Session.RefreshTrustedWorldAuthorityAsync();\n  _launchWorldChosen=true;", "initial launcher must wait for trusted authority resolution")
    require(discord, 'string AuthProvider = "discord"', "account client must model provider identity")
    require(discord, "long SessionExpiresAt = 0", "account client must model provider expiry")

    print("Authenticated launch contract verified: provider session -> Press Start -> Shaelvien-or-sandbox choice -> nested MMO navigation inside Shaelvien.")


if __name__ == "__main__":
    main()
