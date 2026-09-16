import hashlib
import io
import json
import os
import re
import urllib.parse
from datetime import datetime, timezone

import boto3
from PIL import Image, ImageSequence

s3 = boto3.client("s3")
BUCKET = os.environ["STORAGE_BUCKET"]
MAX_CANONICAL_PIXELS = int(os.environ.get("MAX_CANONICAL_PIXELS", "100000000"))
MANIFEST_MEDIA_TYPE = "application/vnd.shaelvien.shaep+json"
READY = "ready"
HOT = "hot"
PRESERVED_SOURCE = "preserved-source"
SUPPORTED_IMAGE_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
    "image/tiff",
}
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".tif", ".tiff"}

Image.MAX_IMAGE_PIXELS = MAX_CANONICAL_PIXELS


def _utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _relative_user_prefix(manifest_key):
    marker = "/uploads/shaep/"
    index = manifest_key.find(marker)
    if index < 0:
        raise ValueError("SHAEP manifest is outside a user uploads/shaep namespace")
    prefix = manifest_key[: index + 1]
    if not prefix.startswith("users/"):
        raise ValueError("SHAEP manifest is outside a user namespace")
    return prefix


def _safe_relative_key(value):
    key = str(value or "").replace("\\", "/").strip("/")
    if not key or ".." in key.split("/"):
        raise ValueError("Invalid SHAEP payload key")
    return key


def _full_user_key(user_prefix, relative_key):
    relative_key = _safe_relative_key(relative_key)
    full = relative_key if relative_key.startswith(user_prefix) else user_prefix + relative_key
    if not full.startswith(user_prefix):
        raise ValueError("SHAEP payload escaped its user namespace")
    return full


def _manifest_from_s3(key):
    obj = s3.get_object(Bucket=BUCKET, Key=key)
    raw = obj["Body"].read()
    manifest = json.loads(raw)
    if manifest.get("Format") != "SHAEP" or manifest.get("Version") != 1:
        raise ValueError("Unsupported SHAEP manifest")
    shaep_id = str(manifest.get("ShaepId") or "")
    if not re.fullmatch(r"shaep-[0-9a-f]{32}", shaep_id):
        raise ValueError("Invalid SHAEP identity")
    return manifest


def _put_manifest(key, manifest):
    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=json.dumps(manifest, separators=(",", ":")).encode("utf-8"),
        ContentType=MANIFEST_MEDIA_TYPE,
        CacheControl="no-store",
        Metadata={
            "shaep-id": manifest["ShaepId"],
            "storage-state": str(manifest.get("StorageState") or HOT),
            "ingest-status": str(manifest.get("IngestStatus") or "unknown"),
        },
    )


def _image_media_type(source, source_key):
    media_type = str(source.get("MediaType") or "").lower().strip()
    if media_type in SUPPORTED_IMAGE_TYPES:
        return media_type
    extension = os.path.splitext(source_key)[1].lower()
    if extension in SUPPORTED_IMAGE_EXTENSIONS:
        return "image/tiff" if extension in {".tif", ".tiff"} else "image/unknown"
    return ""


def _safe_frame(frame):
    copied = frame.copy()
    # 000055.python.app.line104.comment TIFF can preserve these common raster modes losslessly. Convert uncommon
    # 000056.python.app.line105.comment decoder modes to RGBA rather than risking a lossy RGB flattening.
    if copied.mode not in {"1", "L", "LA", "P", "RGB", "RGBA", "CMYK", "I", "F", "I;16", "I;16B", "I;16L"}:
        copied = copied.convert("RGBA")
    return copied


def _canonicalize_image(source_bytes):
    with Image.open(io.BytesIO(source_bytes)) as image:
        width, height = image.size
        if width < 1 or height < 1 or width * height > MAX_CANONICAL_PIXELS:
            raise ValueError("Image exceeds SHAEP canonical pixel safety limit")

        frame_count = max(1, int(getattr(image, "n_frames", 1) or 1))
        durations = []
        frames = []
        for frame in ImageSequence.Iterator(image):
            if frame.width * frame.height > MAX_CANONICAL_PIXELS:
                raise ValueError("Image frame exceeds SHAEP canonical pixel safety limit")
            durations.append(max(0.0, float(frame.info.get("duration") or image.info.get("duration") or 0.0)))
            frames.append(_safe_frame(frame))

        if not frames:
            frames = [_safe_frame(image)]
            durations = [0.0]
            frame_count = 1

        if len(frames) > 1:
            # 000057.python.app.line132.comment Multi-frame TIFF is the preservation master. Normalizing frame mode
            # 000058.python.app.line133.comment avoids Pillow silently dropping pages when source frames differ.
            common_mode = "RGBA" if any("A" in f.mode or f.mode == "P" for f in frames) else "RGB"
            frames = [f if f.mode == common_mode else f.convert(common_mode) for f in frames]

        output = io.BytesIO()
        save_args = {
            "format": "TIFF",
            "compression": "tiff_deflate",
        }
        icc = image.info.get("icc_profile")
        if icc:
            save_args["icc_profile"] = icc
        try:
            exif = image.getexif().tobytes()
            if exif:
                save_args["exif"] = exif
        except Exception:
            pass

        if len(frames) > 1:
            frames[0].save(output, save_all=True, append_images=frames[1:], **save_args)
        else:
            frames[0].save(output, **save_args)

        canonical = output.getvalue()
        total_duration_ms = sum(durations)
        fps = 0.0
        if len(frames) > 1 and total_duration_ms > 0:
            fps = len(frames) * 1000.0 / total_duration_ms
        temporal = None
        if len(frames) > 1:
            temporal = {
                "FrameCount": len(frames),
                "FramesPerSecond": round(fps, 6),
                "DurationSeconds": round(total_duration_ms / 1000.0, 6),
                "Loop": int(image.info.get("loop", 0) or 0) == 0,
            }
        return canonical, width, height, len(frames), temporal


def _normalize_manifest(manifest_key):
    manifest = _manifest_from_s3(manifest_key)
    ingest_status = str(manifest.get("IngestStatus") or "")
    if ingest_status in {READY, PRESERVED_SOURCE}:
        return {"status": "already-" + ingest_status, "shaepId": manifest["ShaepId"]}

    user_prefix = _relative_user_prefix(manifest_key)
    source = dict(manifest.get("Source") or {})
    source_relative = _safe_relative_key(source.get("ObjectKey"))
    source_key = _full_user_key(user_prefix, source_relative)
    source_obj = s3.get_object(Bucket=BUCKET, Key=source_key)
    source_bytes = source_obj["Body"].read()
    source_hash = _sha256(source_bytes)

    source["Sha256"] = source_hash
    source["Bytes"] = len(source_bytes)
    source.setdefault("OriginalFileName", os.path.basename(source_relative))
    if not source.get("MediaType"):
        source["MediaType"] = source_obj.get("ContentType") or "application/octet-stream"

    media_type = _image_media_type(source, source_relative)
    if not media_type:
        # 000059.python.app.line195.comment Non-image codecs intentionally remain their original canonical payload
        # 000060.python.app.line196.comment until a media-specific preservation worker (for example MediaConvert)
        # 000061.python.app.line197.comment is attached. Hashing still makes the hot source archive-verifiable.
        manifest["Source"] = source
        manifest["Canonical"] = dict(source)
        manifest["StorageState"] = HOT
        manifest["IngestStatus"] = PRESERVED_SOURCE
        manifest["UpdatedAtUtc"] = _utc_now()
        _put_manifest(manifest_key, manifest)
        return {"status": PRESERVED_SOURCE, "shaepId": manifest["ShaepId"]}

    canonical_bytes, width, height, frame_count, temporal = _canonicalize_image(source_bytes)
    source["PixelWidth"] = width
    source["PixelHeight"] = height

    shaep_id = manifest["ShaepId"]
    canonical_relative = f"uploads/shaep/{shaep_id}/canonical/master.tiff"
    canonical_key = _full_user_key(user_prefix, canonical_relative)
    canonical_hash = _sha256(canonical_bytes)

    s3.put_object(
        Bucket=BUCKET,
        Key=canonical_key,
        Body=canonical_bytes,
        ContentType="image/tiff",
        CacheControl="private,max-age=31536000,immutable",
        Metadata={
            "shaep-id": shaep_id,
            "sha256": canonical_hash,
            "source-sha256": source_hash,
            "preservation-role": "canonical",
            "storage-state": HOT,
        },
    )

    manifest["Source"] = source
    manifest["Canonical"] = {
        "ObjectKey": canonical_relative,
        "MediaType": "image/tiff",
        "Sha256": canonical_hash,
        "Bytes": len(canonical_bytes),
        "PixelWidth": width,
        "PixelHeight": height,
        "OriginalFileName": source.get("OriginalFileName") or os.path.basename(source_relative),
    }
    if temporal is not None:
        manifest["Temporal"] = temporal
    elif frame_count <= 1:
        manifest["Temporal"] = None
    manifest["StorageState"] = HOT
    manifest["IngestStatus"] = READY
    manifest["UpdatedAtUtc"] = _utc_now()
    _put_manifest(manifest_key, manifest)
    return {"status": READY, "shaepId": shaep_id, "canonicalKey": canonical_relative}


def handler(event, context):
    results = []
    for record in event.get("Records") or []:
        if record.get("eventSource") != "aws:s3":
            continue
        bucket = record.get("s3", {}).get("bucket", {}).get("name")
        if bucket != BUCKET:
            continue
        key = urllib.parse.unquote_plus(record.get("s3", {}).get("object", {}).get("key") or "")
        if not key.endswith(".shaep"):
            continue
        results.append(_normalize_manifest(key))
    return {"processed": len(results), "results": results}
