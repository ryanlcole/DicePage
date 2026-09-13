#!/usr/bin/env bash
set -Eeuo pipefail

AWS_REGION="us-east-1"
EXPECTED_ACCOUNT="797661578124"
ASSET_STACK="rist-assets"
FRONTEND_STACK="rist-frontend"
GEONAPH_COMMIT="786565775353ee2aab10e9faf31150d3dd100bbd"
ZIP_PATH="/home/cloudshell-user/geonaph_world_assets_v1.zip"
EXPECTED_ZIP_SHA256="0f5eb161d822ccdbc5a3e3d6e84c02d3dcb444e0695a7cdbbed4fcfffc82754a"
PACKAGE_NAME="geonaph_world_assets_v1"
DEPLOY_WORK="$(mktemp -d /tmp/geonaph-deploy.XXXXXX)"
PACKAGE_ROOT="$DEPLOY_WORK/extracted/$PACKAGE_NAME"
RUNTIME_DIR="$DEPLOY_WORK/runtime"
SOURCE_DIR="$DEPLOY_WORK/source"
BUILD_DIR="$DEPLOY_WORK/build"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
export AWS_REGION AWS_DEFAULT_REGION

for cmd in aws python3 unzip curl git sha256sum; do
  command -v "$cmd" >/dev/null || { echo "Missing command: $cmd" >&2; exit 1; }
done

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
[[ "$ACCOUNT_ID" == "$EXPECTED_ACCOUNT" ]] || {
  echo "Wrong AWS account: expected $EXPECTED_ACCOUNT, got $ACCOUNT_ID" >&2
  exit 1
}

stack_output() {
  aws cloudformation describe-stacks --stack-name "$1" \
    --query "Stacks[0].Outputs[?OutputKey=='$2'].OutputValue | [0]" --output text
}
ASSET_BUCKET="$(stack_output "$ASSET_STACK" AssetBucketName)"
ASSET_DIST="$(stack_output "$ASSET_STACK" DistributionId)"
ASSET_BASE_URL="$(stack_output "$ASSET_STACK" AssetBaseUrl)"
FRONTEND_BUCKET="$(stack_output "$FRONTEND_STACK" FrontendBucketName)"
FRONTEND_DIST="$(stack_output "$FRONTEND_STACK" FrontendDistributionId)"
FRONTEND_BASE_URL="$(stack_output "$FRONTEND_STACK" FrontendBaseUrl)"
for name in ASSET_BUCKET ASSET_DIST ASSET_BASE_URL FRONTEND_BUCKET FRONTEND_DIST FRONTEND_BASE_URL; do
  value="${!name}"
  [[ -n "$value" && "$value" != "None" ]] || { echo "Could not resolve $name" >&2; exit 1; }
done

[[ -f "$ZIP_PATH" ]] || { echo "Missing $ZIP_PATH" >&2; exit 1; }
ACTUAL_SHA="$(sha256sum "$ZIP_PATH" | awk '{print $1}')"
[[ "$ACTUAL_SHA" == "$EXPECTED_ZIP_SHA256" ]] || {
  echo "ZIP checksum mismatch. Expected $EXPECTED_ZIP_SHA256; got $ACTUAL_SHA" >&2
  exit 1
}

mkdir -p "$RUNTIME_DIR" "$DEPLOY_WORK/extracted"
unzip -q "$ZIP_PATH" -d "$DEPLOY_WORK/extracted"
[[ -f "$PACKAGE_ROOT/deployment_manifest.json" ]] || { echo "Invalid package root" >&2; exit 1; }
export PACKAGE_ROOT RUNTIME_DIR ASSET_BASE_URL

python3 - <<'PY'
import hashlib, json, mimetypes, os
from pathlib import Path

root = Path(os.environ["PACKAGE_ROOT"])
runtime = Path(os.environ["RUNTIME_DIR"])
asset_base = os.environ["ASSET_BASE_URL"].rstrip("/") + "/"

def read(path): return json.loads(path.read_text(encoding="utf-8"))
def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest()
def key(local):
    if local.startswith("assets/world/"): return local.replace("assets/world/", "assets/library/world/", 1)
    if local.startswith("assets/sprites/"): return local
    if local.startswith("geonaph/maps/layers/"): return "assets/worlds/geonaph/v1/layers/" + Path(local).name
    if local.startswith("geonaph/maps/"): return "assets/worlds/geonaph/v1/maps/" + Path(local).name
    if local.startswith("geonaph/layers/"): return "assets/worlds/geonaph/v1/layers/" + Path(local).name
    if local.startswith("geonaph/tiers/"): return "assets/worlds/geonaph/v1/tiers/" + Path(local).name
    if local.startswith("geonaph/manifests/"): return "assets/worlds/geonaph/v1/manifests/" + Path(local).name
    if local.startswith("catalogs/"): return "assets/catalogs/geonaph/v1/" + Path(local).name
    return "assets/worlds/geonaph/v1/support/" + Path(local).name
def mime(path):
    if path.suffix.lower() == ".apng": return "image/apng"
    if path.suffix.lower() == ".json": return "application/json"
    if path.suffix.lower() in {".txt", ".md"}: return "text/plain; charset=utf-8"
    if path.suffix.lower() == ".html": return "text/html; charset=utf-8"
    return mimetypes.guess_type(path.name)[0] or "application/octet-stream"
def normalize_z(value):
    if isinstance(value, list):
        for item in value: normalize_z(item)
    elif isinstance(value, dict):
        for item in list(value.values()): normalize_z(item)
        if isinstance(value.get("tier"), int) and isinstance(value.get("layer"), int):
            value["z"] = value["tier"] * 10 + value["layer"]
        if isinstance(value.get("defaultTierIndex"), int) and isinstance(value.get("defaultLayerOffset"), int):
            value["defaultZ"] = value["defaultTierIndex"] * 10 + value["defaultLayerOffset"]
        if "tierStride" in value: value["tierStride"] = 10
        if isinstance(value.get("tier"), int) and isinstance(value.get("zRange"), dict):
            value["zRange"] = {"min": value["tier"] * 10, "max": value["tier"] * 10 + 9}

for path in root.rglob("*.json"):
    data = read(path); normalize_z(data); write(path, data)

deployment_path = root / "deployment_manifest.json"
deployment = read(deployment_path)
for asset in deployment["assets"]:
    packaged = Path(asset["localZipPath"])
    local = root.joinpath(*packaged.parts[1:])
    if not local.is_file() or digest(local) != asset["sha256"]:
        raise SystemExit(f"Asset checksum failure: {local}")
    asset["z"] = int(asset["tier"]) * 10 + int(asset["layer"])
    if asset["classification"] == "sprite":
        packaged_sheet = Path(asset["spriteSheetLocalZipPath"])
        sheet = root.joinpath(*packaged_sheet.parts[1:])
        if not sheet.is_file() or digest(sheet) != asset["spriteSheetSha256"]:
            raise SystemExit(f"Sprite-sheet checksum failure: {sheet}")

def absolute_image(local):
    return local if local.startswith(("https://", "http://")) else asset_base + key(local)
def author(source):
    p = source.get("provenance") or {}
    return source.get("author") or p.get("author") or p.get("preservedAuthor") or "OpenAI Codex for Shaelvien/RIST"
def atlas(source):
    footprint = source.get("defaultFootprint", 1)
    if isinstance(footprint, dict): footprint = max(footprint.get("width", 1), footprint.get("height", 1))
    layer = source.get("layer", "WORLD")
    return {
        "id": source["id"], "name": source["name"], "image": absolute_image(source["image"]),
        "layer": layer if isinstance(layer, str) else "WORLD",
        "directory": source.get("directory", "Terrain"), "folder": source.get("folder", "Special"),
        "author": author(source), "sourceWidth": int(source.get("sourceWidth") or 0),
        "sourceHeight": int(source.get("sourceHeight") or 0), "cropX": int(source.get("cropX") or 0),
        "cropY": int(source.get("cropY") or 0), "cropWidth": int(source.get("cropWidth") or 0),
        "cropHeight": int(source.get("cropHeight") or 0), "assetKind": source.get("assetKind", "tile"),
        "authoredDepth": bool(source.get("authoredDepth", True)),
        "defaultTierIndex": int(source.get("defaultTierIndex", source.get("tier", 0))),
        "defaultLayerOffset": int(source.get("defaultLayerOffset", 0)),
        "defaultFootprint": int(footprint), "frameCount": int(source.get("frameCount", 1)),
        "framesPerSecond": float(source.get("framesPerSecond", 0)),
    }

library = read(root / "catalogs/library_catalog.json")
sprites = read(root / "catalogs/sprite_catalog.json")
layers = read(root / "geonaph_layer_manifest.json")
sprite_manifest = read(root / "geonaph_sprite_manifest.json")
new_library, new_sprites = [atlas(x) for x in library], [atlas(x) for x in sprites]
assert len(new_library) == 80 and len(new_sprites) == 17
assert all(x["assetKind"] == "sprite" and x["frameCount"] > 1 and x["framesPerSecond"] > 0 for x in new_sprites)
write(runtime / "geonaph_library_entries.json", new_library)
write(runtime / "geonaph_sprite_entries.json", new_sprites)

placements = []
for source in layers["layerAssets"]:
    asset = atlas(source); asset.update(assetKind="tile", frameCount=1, framesPerSecond=0)
    placements.append({"placementId": source["id"] + "-placement", "asset": asset, "x": 0, "y": 0, "footprint": 30})
sprites_by_id = {x["id"]: x for x in sprites}
for placement in sprite_manifest["mapPlacements"]:
    source = sprites_by_id[placement["assetId"]]
    footprint = placement.get("footprint", source.get("footprint", {"width": 1, "height": 1}))
    if isinstance(footprint, dict): footprint = max(footprint.get("width", 1), footprint.get("height", 1))
    placements.append({"placementId": placement["placementId"], "asset": atlas(source),
                       "x": placement["x"], "y": placement["y"], "footprint": int(footprint)})
assert len(placements) == 41
write(runtime / "runtime_catalog.json", {
    "schemaVersion": 1, "worldId": "geonaph-world-v1", "name": "Geonaph",
    "gridWidth": 30, "gridHeight": 30, "layersPerTier": 10,
    "registeredOrigin": layers["registeredOrigin"], "placements": placements,
})

deployment["runtimeLayersPerTier"] = 10
deployment["status"] = "normalized-for-rist-runtime-awaiting-upload"
deployment["files"] = [
    {
        "localZipPath": f"{root.name}/{path.relative_to(root).as_posix()}",
        "intendedS3Path": key(path.relative_to(root).as_posix()),
        "contentType": mime(path),
        "byteSize": path.stat().st_size,
        "sha256": digest(path),
    }
    for path in sorted(root.rglob("*"))
    if path.is_file() and path != deployment_path
] + [{
    "localZipPath": f"{root.name}/deployment_manifest.json",
    "intendedS3Path": "assets/worlds/geonaph/v1/deployment_manifest.json",
    "contentType": "application/json",
    "byteSize": None,
    "sha256": None,
    "selfReferentialManifest": True,
}]
write(deployment_path, deployment)
with (runtime / "asset_upload_plan.tsv").open("w", encoding="utf-8") as target:
    for path in sorted(root.rglob("*")):
        if path.is_file():
            local = path.relative_to(root).as_posix()
            target.write("\t".join((local, key(local), mime(path), digest(path), str(path.stat().st_size))) + "\n")
assert sum(1 for path in root.rglob("*") if path.is_file()) == 100
print("Package validation and runtime normalization passed")
PY

echo "Asset bucket: $ASSET_BUCKET"
echo "Frontend bucket: $FRONTEND_BUCKET"
UPLOAD_COUNT=0
while IFS=$'\t' read -r local object mime sha bytes; do
  [[ "$mime" == image/* ]] && cache="public,max-age=31536000,immutable" || cache="no-cache,no-store,must-revalidate"
  aws s3 cp "$PACKAGE_ROOT/$local" "s3://$ASSET_BUCKET/$object" \
    --content-type "$mime" --cache-control "$cache" --metadata "sha256=$sha" --only-show-errors
  UPLOAD_COUNT=$((UPLOAD_COUNT + 1))
done < "$RUNTIME_DIR/asset_upload_plan.tsv"
[[ "$UPLOAD_COUNT" -eq 100 ]]

BACKUP_PREFIX="deployment-backups/geonaph/$STAMP"
aws s3 cp "s3://$FRONTEND_BUCKET/Game/assets/drive-tiles/catalog.json" "$RUNTIME_DIR/current_library.json" --only-show-errors \
  || printf '[]\n' > "$RUNTIME_DIR/current_library.json"
aws s3 cp "s3://$FRONTEND_BUCKET/Game/assets/sprites/catalog.json" "$RUNTIME_DIR/current_sprites.json" --only-show-errors \
  || printf '[]\n' > "$RUNTIME_DIR/current_sprites.json"
aws s3 cp "$RUNTIME_DIR/current_library.json" "s3://$FRONTEND_BUCKET/$BACKUP_PREFIX/library_catalog.json" --only-show-errors
aws s3 cp "$RUNTIME_DIR/current_sprites.json" "s3://$FRONTEND_BUCKET/$BACKUP_PREFIX/sprite_catalog.json" --only-show-errors
aws s3 sync "s3://$FRONTEND_BUCKET/Game/assets/sprites/pangea/" \
  "s3://$FRONTEND_BUCKET/$BACKUP_PREFIX/obsolete-pangea/" --only-show-errors || true

python3 - <<'PY'
import json, os
from pathlib import Path
runtime = Path(os.environ["RUNTIME_DIR"])
def load(name):
    try:
        value = json.loads((runtime / name).read_text()); return value if isinstance(value, list) else []
    except Exception: return []
def write(name, value):
    (runtime / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
def geonaph(x): return str(x.get("id", "")).lower().startswith("geonaph-")
def pangea(x): return "pangea" in json.dumps(x).lower()
def animated(x):
    return str(x.get("assetKind", "")).lower() == "sprite" and int(x.get("frameCount", 1)) > 1 and float(x.get("framesPerSecond", 0)) > 0
def dedupe(items): return list({x["id"]: x for x in items}.values())
library = dedupe([x for x in load("current_library.json") if not geonaph(x) and not pangea(x)] + load("geonaph_library_entries.json"))
sprites = dedupe([x for x in load("current_sprites.json") if not geonaph(x) and not pangea(x) and animated(x)] + load("geonaph_sprite_entries.json"))
assert len([x for x in library if geonaph(x)]) == 80
assert len([x for x in sprites if geonaph(x)]) == 17 and all(animated(x) for x in sprites)
write("merged_library_catalog.json", library); write("merged_sprite_catalog.json", sprites)
PY

git clone --filter=blob:none --no-checkout https://github.com/ryanlcole/DicePage.git "$SOURCE_DIR"
git -C "$SOURCE_DIR" checkout --detach "$GEONAPH_COMMIT"
[[ "$(git -C "$SOURCE_DIR" rev-parse HEAD)" == "$GEONAPH_COMMIT" ]]
python3 - "$SOURCE_DIR/apps/rist-world/tests/test_worldbuilder_physical_table.py" <<'PY'
import runpy, sys
tests = runpy.run_path(sys.argv[1])
for name, fn in sorted(tests.items()):
    if name.startswith("test_") and callable(fn): fn(); print("PASS", name)
PY

DOTNET_DIR="$DEPLOY_WORK/dotnet"
curl -fsSL --retry 5 https://dot.net/v1/dotnet-install.sh -o "$DEPLOY_WORK/dotnet-install.sh"
bash "$DEPLOY_WORK/dotnet-install.sh" --channel 10.0 --quality GA --install-dir "$DOTNET_DIR"
export PATH="$DOTNET_DIR:$PATH"
PYDEPS="$DEPLOY_WORK/python-deps"
python3 -m pip install --disable-pip-version-check --quiet --target "$PYDEPS" Pillow==11.3.0
PYTHONPATH="$PYDEPS${PYTHONPATH:+:$PYTHONPATH}" python3 "$SOURCE_DIR/apps/rist-world/prepare_public_data.py"
dotnet publish "$SOURCE_DIR/apps/rist-world/RistWorld.csproj" -c Release -o "$BUILD_DIR/rist" --nologo

aws s3 sync "$BUILD_DIR/rist/wwwroot/" "s3://$FRONTEND_BUCKET/Game/" \
  --exclude 'index.html' --exclude 'Launcher/*' --exclude 'assets/shaelvien/*' \
  --exclude 'authority-config.json' --exclude 'translation-config.json' \
  --cache-control 'public,max-age=86400' --only-show-errors
aws s3 cp "$BUILD_DIR/rist/wwwroot/_framework/blazor.boot.json" \
  "s3://$FRONTEND_BUCKET/Game/_framework/blazor.boot.json" \
  --content-type application/json --cache-control 'no-cache,no-store,must-revalidate' --only-show-errors
aws s3 cp "$BUILD_DIR/rist/wwwroot/index.html" "s3://$FRONTEND_BUCKET/Game/index.html" \
  --content-type 'text/html; charset=utf-8' --cache-control 'no-cache,no-store,must-revalidate' --only-show-errors

publish_json() {
  aws s3 cp "$1" "s3://$FRONTEND_BUCKET/$2" \
    --content-type application/json --cache-control 'no-cache,no-store,must-revalidate' --only-show-errors
}
publish_json "$RUNTIME_DIR/merged_library_catalog.json" "Game/assets/drive-tiles/catalog.json"
publish_json "$RUNTIME_DIR/merged_sprite_catalog.json" "Game/assets/sprites/catalog.json"
publish_json "$RUNTIME_DIR/runtime_catalog.json" "Game/assets/worlds/geonaph/v1/runtime_catalog.json"
publish_json "$PACKAGE_ROOT/catalogs/geonaph_map_catalog.json" "Game/assets/worlds/geonaph/v1/geonaph_map_catalog.json"
publish_json "$PACKAGE_ROOT/geonaph_layer_manifest.json" "Game/assets/worlds/geonaph/v1/geonaph_layer_manifest.json"
publish_json "$PACKAGE_ROOT/geonaph_sprite_manifest.json" "Game/assets/worlds/geonaph/v1/geonaph_sprite_manifest.json"
publish_json "$PACKAGE_ROOT/deployment_manifest.json" "Game/assets/worlds/geonaph/v1/deployment_manifest.json"
aws s3 rm "s3://$FRONTEND_BUCKET/Game/assets/sprites/pangea/" --recursive --only-show-errors

VERIFIED=0
while IFS=$'\t' read -r local object mime sha bytes; do
  remote_sha="$(aws s3api head-object --bucket "$ASSET_BUCKET" --key "$object" --query Metadata.sha256 --output text)"
  remote_bytes="$(aws s3api head-object --bucket "$ASSET_BUCKET" --key "$object" --query ContentLength --output text)"
  [[ "$remote_sha" == "$sha" && "$remote_bytes" == "$bytes" ]] || { echo "Verification failed: $object" >&2; exit 1; }
  VERIFIED=$((VERIFIED + 1))
done < "$RUNTIME_DIR/asset_upload_plan.tsv"
[[ "$VERIFIED" -eq 100 ]]

ASSET_INV="$(aws cloudfront create-invalidation --distribution-id "$ASSET_DIST" \
  --paths '/assets/library/world/terrain/*' '/assets/sprites/world/terrain/*' '/assets/worlds/geonaph/v1/*' '/assets/catalogs/geonaph/v1/*' \
  --query Invalidation.Id --output text)"
FRONTEND_INV="$(aws cloudfront create-invalidation --distribution-id "$FRONTEND_DIST" \
  --paths '/Game/*' --query Invalidation.Id --output text)"
aws cloudfront wait invalidation-completed --distribution-id "$ASSET_DIST" --id "$ASSET_INV"
aws cloudfront wait invalidation-completed --distribution-id "$FRONTEND_DIST" --id "$FRONTEND_INV"

curl -fsSL --retry 8 "${FRONTEND_BASE_URL}Game/assets/drive-tiles/catalog.json" -o "$RUNTIME_DIR/live_library.json"
curl -fsSL --retry 8 "${FRONTEND_BASE_URL}Game/assets/sprites/catalog.json" -o "$RUNTIME_DIR/live_sprites.json"
curl -fsSL --retry 8 "${FRONTEND_BASE_URL}Game/assets/worlds/geonaph/v1/runtime_catalog.json" -o "$RUNTIME_DIR/live_runtime.json"
curl -fsSL --retry 8 "${ASSET_BASE_URL}assets/sprites/world/terrain/ocean/geonaph_ocean_surface_motion_animated_v1.apng" -o "$RUNTIME_DIR/live_ocean.apng"
python3 - <<PY
import json
from pathlib import Path
r = Path("$RUNTIME_DIR")
library, sprites, world = [json.loads((r / name).read_text()) for name in ("live_library.json", "live_sprites.json", "live_runtime.json")]
assert len([x for x in library if str(x.get("id", "")).startswith("geonaph-")]) == 80
genuine = [x for x in sprites if str(x.get("id", "")).startswith("geonaph-")]
assert len(genuine) == 17 and all(x["assetKind"] == "sprite" and x["frameCount"] > 1 and x["framesPerSecond"] > 0 for x in genuine)
assert world["worldId"] == "geonaph-world-v1" and world["gridWidth"] == world["gridHeight"] == 30
assert world["layersPerTier"] == 10 and len(world["placements"]) == 41
assert (r / "live_ocean.apng").stat().st_size > 0
print("LIVE VERIFICATION PASSED")
print("80 Geonaph normal-Library entries")
print("17 genuine Geonaph sprites")
print("41 registered World Builder placements")
print("100 package objects verified")
print("Runtime source commit: $GEONAPH_COMMIT")
print("Backup: s3://$FRONTEND_BUCKET/$BACKUP_PREFIX/")
PY
