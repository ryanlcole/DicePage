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
    host = (COMPONENTS / "WorldBuilderGeonaphHost.razor").read_text(encoding="utf-8")
    ticker = (COMPONENTS / "SiteTicker.razor").read_text(encoding="utf-8")
    rist = (ROOT / "wwwroot" / "rist.js").read_text(encoding="utf-8")
    compat = (ROOT / "wwwroot" / "auth-session-compat.js").read_text(encoding="utf-8")
    discord = (ROOT / "DiscordAuthClient.cs").read_text(encoding="utf-8")
    auth_template = (ROOT.parents[1] / "infra" / "aws" / "rist-discord-storage.yml").read_text(encoding="utf-8")

    # Verified provider session -> mandatory world choice -> landing.
    require(authenticated, "@if(!_launchWorldChosen)", "authenticated shell must gate landing on world choice")
    require(
        authenticated,
        '<WorldGate Open="true" RequireSelection="true" OnClose="CompleteWorldChoiceAsync" />',
        "authenticated shell must own the mandatory initial world gate",
    )
    require(authenticated, '<PublicAlphaShell @ref="_alphaShell" />', "landing shell must render only after world choice")
    require(authenticated, "_launchWorldChosen=true;", "successful world selection must unlock landing")
    forbid(authenticated, "_launchStarted", "verified provider sessions must not add a second launch gate")
    forbid(authenticated, "PRESS START", "verified provider sessions must go directly to world choice")
    forbid(authenticated, "ristPrivacy.set", "privacy preference must not block authenticated launch")
    forbid(authenticated, "ristMotionPermission.request", "motion permission must not block authenticated launch")

    # WorldGate must paint before directory/network/storage work.
    require(gate, "protected override void OnParametersSet()", "world chooser must initialize synchronously")
    require(gate, "_loading=true;", "world chooser must expose a visible loading state")
    require(gate, "_loadRequested=true;", "world chooser must defer directory work until after first render")
    require(gate, "protected override async Task OnAfterRenderAsync", "world chooser must load after first paint")
    require(gate, "await RefreshWorldsAsync();", "world chooser must load its directory after first paint")
    forbid(gate, "protected override async Task OnParametersSetAsync()", "world chooser must not block first paint")

    # Landing starts at the hub for the already-selected world.
    require(shell, "_workspaceOpen=false;", "landing must start at hub")
    require(shell, "_worldGateOpen=false;", "landing must not open a second initial world gate")
    require(shell, 'await PersistWorkspaceAsync("hub");', "landing must persist hub as launch workspace")
    forbid(shell, "RestorableWorkspaces.Contains(storedWorkspace)", "old workspace restoration must not bypass world-first launch")
    forbid(shell, "ApplyWorkspace(storedWorkspace)", "old workspace restoration must not bypass landing")

    # One universal World Builder. Geonaph differs only by seed data.
    require(router, '<WorldBuilderGeonaphHost OnStartMenu="OnStartMenu" />', "all worlds must use the universal builder host")
    forbid(router, '<WorldBuilderStudio OnStartMenu="OnStartMenu" />', "normal worlds must not route to a second builder")
    require(host, 'var seed=Session.IsGeonaphWorld?"geonaph":"empty";', "Geonaph may differ only by seed data")
    require(host, "worldId={worldId}", "builder must receive selected world identity")

    # Ticker is world-scoped and absent before world choice.
    require(ticker, "@if(Session.HasActiveWorld)", "ticker must stay hidden until a world is active")
    require(ticker, 'rist.worldbuilder.ticker.buttons.v1.{Session.WorldId}', "ticker settings must be world-scoped")

    # Authentication session lifetime belongs to the provider/server.
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
    require(discord, 'string AuthProvider = "discord"', "account client must model provider identity")
    require(discord, "long SessionExpiresAt = 0", "account client must model provider expiry")

    print("Authenticated launch contract verified: provider session -> world choice -> landing -> selected-world workspace.")


if __name__ == "__main__":
    main()
