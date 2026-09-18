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

    # Initial authenticated launch has one authority: AuthenticatedWorld.
    require(authenticated, "@if(!_launchWorldChosen)", "authenticated shell must gate landing on world choice")
    require(
        authenticated,
        '<WorldGate Open="true" RequireSelection="true" OnClose="CompleteWorldChoiceAsync" />',
        "authenticated shell must own the mandatory initial world gate",
    )
    require(authenticated, "<PublicAlphaShell @ref=\"_alphaShell\" />", "landing shell must render only after world choice")
    require(authenticated, "_launchWorldChosen=true;", "successful world selection must unlock landing immediately")

    # WorldGate must paint before any directory/network/storage wait.
    require(gate, "protected override void OnParametersSet()", "world chooser must initialize synchronously")
    require(gate, "_loading=true;", "world chooser must expose a visible loading state")
    require(gate, "_loadRequested=true;", "world chooser must defer directory work until after first render")
    require(gate, "protected override async Task OnAfterRenderAsync", "world chooser must load after first paint")
    require(gate, "await RefreshWorldsAsync();", "world chooser must load its directory after first paint")
    forbid(gate, "protected override async Task OnParametersSetAsync()", "world chooser must never block first paint on async parameters")

    # Landing always starts at the hub for the already-selected world.
    require(shell, "_workspaceOpen=false;", "landing must not restore an old workspace before showing the hub")
    require(shell, "_worldGateOpen=false;", "landing must not open a second initial world gate")
    require(shell, 'await PersistWorkspaceAsync("hub");', "landing must persist hub as the launch workspace")
    forbid(shell, "RestorableWorkspaces.Contains(storedWorkspace)", "old workspace restoration must not bypass world-first launch")
    forbid(shell, "ApplyWorkspace(storedWorkspace)", "old workspace restoration must not bypass landing")

    # World Builder is universal. Geonaph differs only by seed data.
    require(router, '<WorldBuilderGeonaphHost OnStartMenu="OnStartMenu" />', "all worlds must use the universal prototype builder host")
    forbid(router, '<WorldBuilderStudio OnStartMenu="OnStartMenu" />', "normal worlds must not route to a second builder")
    require(host, 'var seed=Session.IsGeonaphWorld?"geonaph":"empty";', "Geonaph may differ only by seed data")
    require(host, "worldId={worldId}", "builder must receive selected world identity")

    # Ticker is world-scoped and absent before world choice.
    require(ticker, "@if(Session.HasActiveWorld)", "ticker must stay hidden until a world is active")
    require(ticker, 'rist.worldbuilder.ticker.buttons.v1.{Session.WorldId}', "ticker settings must be world-scoped")

    print("Authenticated launch contract verified: auth -> world choice -> landing -> selected-world workspace.")


if __name__ == "__main__":
    main()
