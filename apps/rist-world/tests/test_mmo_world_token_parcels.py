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
    assert 'SHAELVIEN_TOKEN_CLASS = "shaelvien.property-space"' in backend
    assert '"accountHalfCode": account_half' in backend
    assert '"accountHalfHash": hashlib.sha256(account_half.encode()).hexdigest()' in backend
    assert "Legacy unspent tokens created before split-code binding" in backend
    assert "attribute_not_exists(accountHalfCode)" in backend
    assert "users.update_item(" in backend


def test_mmo_parcel_claim_is_exclusive_atomic_and_endemar_centered():
    backend = text("infra/aws/rist-platform-authority/app.py")
    assert "SHAELVIEN_PROPERTY_SPACE_PIXELS = 2048" in backend
    assert "MMO_PARCEL_PIXELS = SHAELVIEN_PROPERTY_SPACE_PIXELS" in backend
    assert "SHAELVIEN_PROPERTY_SPACE_LAYERS = 100" in backend
    assert "MMO_PARCEL_MAX_HEIGHT = SHAELVIEN_PROPERTY_SPACE_LAYERS" in backend
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
    assert "Claim is idempotent for the account that already owns this exact" in backend
    assert "return response(200, public_parcel(existing_parcel))" in backend
    assert "latest_token = world_token_for_parcel(user_id, parcel_id)" in backend
    assert "def normalize_unspent_world_token(user_id, token):" in backend
    assert "normalize_unspent_world_token(user_id, item)" in backend
    assert '"ConditionExpression": "#status = :unspent"' in backend
    assert '"#status = :unspent AND tokenId = :tokenId"' not in backend
    assert '"#status = :unspent AND holderUserId = :userId"' not in backend
    assert "def ensure_parcel_region(world_id, parcel, now_value=None):" in backend
    claim_block = backend[backend.index('path == "/world/parcels/claim"'):backend.index('path == "/world/parcels/delegate"')]
    assert "ensure_parcel_region(world_id, parcel_item, now)" in claim_block
    assert "ensure_parcel_region(world_id, existing_parcel, now)" in claim_block
    assert "region_item" not in claim_block.split("claim_transaction = [", 1)[1].split("claim_committed = False", 1)[0]
    transaction_block = claim_block.split("claim_transaction = [", 1)[1].split("claim_committed = False", 1)[0]
    assert '"Update": {' not in transaction_block
    assert "spent_token = {" in claim_block
    assert '"Item": _ddb_map(dynamo_safe(spent_token))' in transaction_block
    assert transaction_block.count('"Put": {') == 2


def test_claimed_parcel_cannot_be_taken_or_grown_by_region_save():
    backend = text("infra/aws/rist-platform-authority/app.py")
    assert '"ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)"' in backend
    assert '"That Shaelvien property space has already been claimed"' in backend
    assert 'region["minColumn"] = column' in backend
    assert 'region["maxColumn"] = column' in backend
    assert 'region["minRow"] = row' in backend
    assert 'region["maxRow"] = row' in backend
    assert 'region["parcelPixelWidth"] = MMO_PARCEL_PIXELS' in backend
    assert 'region["parcelPixelHeight"] = MMO_PARCEL_PIXELS' in backend
    assert 'region["maxHeight"] = MMO_PARCEL_MAX_HEIGHT' in backend
    assert "Token + parcel are the atomic ownership identity." in backend
    assert "Region state is a representation of" in backend


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
    assert "CLAIM PROPERTY SPACE" in host
    assert "SPEND SHAELVIEN TOKEN & CLAIM" in host
    assert "2048 by 2048 pixels, maximum height 100 layers" in host
    assert "Shaelvien property space" in host
    assert "RegionDefinerWorkspace" in host
    assert "Session.SetActiveRegion(parcel.RegionId)" in host
    client = text("apps/rist-world/AwsAuthorityClient.cs")
    session = text("apps/rist-world/WorldSession.MmoLand.cs")
    assert "AuthorityError" in client
    assert "payload.Error.Trim()" in client
    assert "catch (HttpRequestException ex)" in session
    assert "await RefreshMmoLandAsync();" in session
    assert "var tokenId = UnspentMmoWorldToken?.TokenId ?? \"\";" in session
    assert "ClaimMmoParcelAsync(WorldId, cellIndex, displayName, tokenId)" in session
    assert "attempt < 2" in session
    assert 'ex.Message.Contains("binding was refreshed", StringComparison.OrdinalIgnoreCase)' in session
    assert "HasUnspentMmoWorldToken" in session
    assert "_mmoParcels.Add(claimed);" in session
    assert 'Status = "spent"' in session
    assert "PurchasedWorldId = WorldId" in session
    assert "ParcelId = claimed.ParcelId" in session
    assert "await InvokeAsync(StateHasChanged);" in host
    assert "_claimOpen=false;" in host
    assert "PERMISSIONS" in host
    assert "Mode == \"world\" && Session.CanRequestWorldClaim" not in router

    assert "parcelPixelWidth=Session.ActiveRegion?.ParcelPixelWidth??0" in workspace
    assert "parcelPixelHeight=Session.ActiveRegion?.ParcelPixelHeight??0" in workspace
    assert "maxHeight=Session.ActiveRegion?.MaxHeight??0" in workspace
    assert "await RefreshMmoLandAsync(loadParcels: false);" in relationships


def test_worldbuilder_and_regiondefiner_fill_parent_workspace_not_raw_device_viewport():
    shell_css = text("apps/rist-world/Components/PublicAlphaShell.razor.css")
    host = text("apps/rist-world/Components/WorldBuilderGeonaphHost.razor")
    region = text("apps/rist-world/Components/RegionDefinerWorkspace.razor")
    router = text("apps/rist-world/Components/TaskWorkspaceRouter.razor")

    assert ".alpha-world-stage{box-sizing:border-box;position:relative;width:100%;height:100%;" in shell_css
    assert "position:absolute;inset:0" in host
    assert "width:100%;height:100%" in host
    assert "width:100dvw;height:100dvh" not in host
    assert "position:absolute;" in region
    assert "width:100%;" in region and "height:100%;" in region
    assert "width:100dvw;" not in region and "height:100dvh;" not in region
    assert ".task-workspace-router{box-sizing:border-box;position:relative;width:100%;height:100%;" in router


def test_world_gate_mobile_layout_keeps_token_and_private_world_sections_separate():
    gate = text("apps/rist-world/Components/WorldGate.razor")
    assert "display:flex;flex-direction:column;overflow:auto" in gate
    assert "grid-template-rows:auto minmax(0,1fr)" not in gate
    assert "SHAELVIEN MMO · PROPERTY SPACE" in gate
    assert "world-gate-create{display:grid;gap:10px;margin:10px 16px 6px" in gate


def test_shaelvien_is_the_mmo_world_and_endemar_is_the_starting_point():
    identity = text("apps/rist-world/WorldSession.WorldIdentity.cs")
    assert 'public const string ShaelvienDisplayName = "Shaelvien";' in identity
    assert 'public const string EndemarStartingPointDisplayName = "Endemar";' in identity
    assert "public const string GeonaphDisplayName = ShaelvienDisplayName;" in identity
