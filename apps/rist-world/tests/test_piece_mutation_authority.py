from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ROOT / "Components"


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_piece_identity_is_persistent_and_versioned():
    models = read("WorldSession.Models.cs")
    assert 'string PieceId=""' in models
    assert 'string OwnerUserId=""' in models
    assert 'long AuthorityVersion=0' in models


def test_authenticated_piece_mutation_is_server_first_and_fail_closed():
    authority = read("WorldSession.PieceAuthority.cs")
    assert '"piece.move"' in authority
    assert '"piece.remove"' in authority
    assert "await authority.MutateAsync(" in authority
    assert 'return new(false, "You do not have authority to move that piece.")' in authority
    assert "Pieces[index] = piece with" in authority
    assert "AuthorityVersion = updated.Version" in authority
    assert authority.index("if (updated is null)") < authority.index("Pieces[index] = piece with")


def test_accessibility_and_pointer_paths_share_authorized_mutation():
    accessibility = read("WorldSession.Accessibility.cs")
    shell = (COMPONENTS / "AccessibilityShell.razor").read_text(encoding="utf-8")
    world_map = (COMPONENTS / "WorldMap.razor.cs").read_text(encoding="utf-8")

    assert "await MovePieceAuthorizedAsync(piece, x, y)" in accessibility
    assert "MoveAccessiblePiece(" not in accessibility
    assert "await Session.MoveAccessiblePieceAsync(" in shell
    assert "await Session.MovePieceAuthorizedAsync(" in world_map
    assert "await Session.RemovePieceAuthorizedAsync(" in world_map
    assert "Session.MovePiece(" not in world_map
    assert "Session.RemovePiece(" not in world_map


def test_authority_client_carries_server_owner_back_to_session():
    client = read("AwsAuthorityClient.cs")
    assert 'string OwnerUserId = ""' in client


def main():
    tests = [
        test_piece_identity_is_persistent_and_versioned,
        test_authenticated_piece_mutation_is_server_first_and_fail_closed,
        test_accessibility_and_pointer_paths_share_authorized_mutation,
        test_authority_client_carries_server_owner_back_to_session,
    ]
    for test in tests:
        test()
    print(f"piece-mutation-authority: ok ({len(tests)} checks)")


if __name__ == "__main__":
    main()
