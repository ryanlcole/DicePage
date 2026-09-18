from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def text(path):
    return (REPO / path).read_text(encoding="utf-8")


def test_authority_backend_parses_and_mints_one_profile_token():
    backend = text("infra/aws/rist-platform-authority/app.py")
    ast.parse(backend)
    assert 'path == "/authority/profile-complete"' in backend
    assert 'path == "/authority/world-tokens"' in backend
    assert 'GENESIS_WORLD_TOKEN_SK = "WORLD_TOKEN#GENESIS"' in backend
    assert 'ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)"' in backend
    assert '"status": "unspent"' in backend
    assert '"accountHalfCode": account_half' in backend
    assert '"accountHalfHash": hashlib.sha256(account_half.encode()).hexdigest()' in backend


def test_mmo_parcel_claim_is_exclusive_atomic_and_endemar_centered():
    backend = text("infra/aws/rist-platform-authority/app.py")
    assert "MMO_PARCEL_PIXELS = 2048" in backend
    assert "MMO_PARCEL_MAX_HEIGHT = 100" in backend
    assert "ENDEMAR_ORIGIN_COLUMN = 15" in backend
    assert "ENDEMAR_ORIGIN_ROW = 15" in backend
    assert "def mmo_parcel_claimable" in backend
    assert "frontier = occupied | {(ENDEMAR_ORIGIN_COLUMN, ENDEMAR_ORIGIN_ROW)}" in backend
    assert 'path == "/world/parcels/claim"' in backend
    assert "transact_write_items(" in backend
    assert '"worldHalfCode": world_half' in backend
    assert "binding_hash = hashlib.sha256(" in backend
    assert '"pixelWidth": MMO_PARCEL_PIXELS' in backend
    assert '"pixelHeight": MMO_PARCEL_PIXELS' in backend
    assert '"maxHeight": MMO_PARCEL_MAX_HEIGHT' in backend
    assert '"sourceLayerOffsets": list(range(MMO_PARCEL_MAX_HEIGHT))' in backend


def test_claimed_parcel_cannot_be_taken_or_grown_by_region_save():
    backend = text("infra/aws/rist-platform-authority/app.py")
    assert '"ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)"' in backend
    assert '"That Shaelvien parcel has already been claimed"' in backend
    assert 'region["minColumn"] = column' in backend
    assert 'region["maxColumn"] = column' in backend
    assert 'region["minRow"] = row' in backend
    assert 'region["maxRow"] = row' in backend
    assert 'region["parcelPixelWidth"] = MMO_PARCEL_PIXELS' in backend
    assert 'region["parcelPixelHeight"] = MMO_PARCEL_PIXELS' in backend
    assert 'region["maxHeight"] = MMO_PARCEL_MAX_HEIGHT' in backend


def test_parcel_permissions_delegate_without_transferring_ownership():
    backend = text("infra/aws/rist-platform-authority/app.py")
    session = text("apps/rist-world/WorldSession.MmoLand.cs")
    regions = text("apps/rist-world/WorldSession.Regions.cs")
    assert 'PARCEL_DELEGATION_PERMISSIONS = {"View", "Edit", "Manage", "None"}' in backend
    assert 'path == "/world/parcels/delegate"' in backend
    assert 'parcel_permission(world_id, parcel_id, user_id) == "Manage"' in backend
    assert "CanManageMmoParcel" in session
    assert "DelegateMmoParcelAsync" in session
    assert "string ParcelId = """ in regions
    assert "CanEditMmoParcel(parcel)" in regions


def test_worldbuilder_exposes_token_claim_map_and_enters_scoped_region():
    host = text("apps/rist-world/Components/WorldBuilderGeonaphHost.razor")
    router = text("apps/rist-world/Components/TaskWorkspaceRouter.razor")
    workspace = text("apps/rist-world/Components/RegionDefinerWorkspace.razor")
    relationships = text("apps/rist-world/WorldSession.WorldRelationships.cs")

    assert "SHAELVIEN · ORIGIN: ENDEMAR" in host
    assert "CLAIM WORLD" in host
    assert "SPEND TOKEN & CLAIM" in host
    assert "2048 by 2048 pixels, maximum height 100 layers" in host
    assert "RegionDefinerWorkspace" in host
    assert "Session.SetActiveRegion(parcel.RegionId)" in host
    assert "PERMISSIONS" in host
    assert "Mode == \"world\" && Session.CanRequestWorldClaim" not in router

    assert "parcelPixelWidth=Session.ActiveRegion?.ParcelPixelWidth??0" in workspace
    assert "parcelPixelHeight=Session.ActiveRegion?.ParcelPixelHeight??0" in workspace
    assert "maxHeight=Session.ActiveRegion?.MaxHeight??0" in workspace
    assert "await RefreshMmoLandAsync(loadParcels: false);" in relationships


def test_shaelvien_is_the_mmo_world_and_endemar_is_the_starting_point():
    identity = text("apps/rist-world/WorldSession.WorldIdentity.cs")
    assert 'public const string ShaelvienDisplayName = "Shaelvien";' in identity
    assert 'public const string EndemarStartingPointDisplayName = "Endemar";' in identity
    assert "public const string GeonaphDisplayName = ShaelvienDisplayName;" in identity
