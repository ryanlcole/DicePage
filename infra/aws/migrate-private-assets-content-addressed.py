#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

STACK_NAME = "rist-discord-storage"
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg")


def now_epoch() -> int:
    return int(time.time())


def sha256_stream(body) -> str:
    digest = hashlib.sha256()
    while True:
        block = body.read(1024 * 1024)
        if not block:
            return digest.hexdigest()
        digest.update(block)


def content_key(sha256: str) -> str:
    return f"content/sha256/{sha256[:2]}/{sha256}"


def content_pk(sha256: str) -> str:
    return "content#" + sha256


def ref_pk(user_id: str, relative_key: str) -> str:
    digest = hashlib.sha256(f"{user_id}:{relative_key}".encode()).hexdigest()
    return "contentref#" + digest


def split_user_key(key: str) -> tuple[str, str] | None:
    parts = key.split("/", 2)
    if len(parts) != 3 or parts[0] != "users":
        return None
    return parts[1], parts[2]


def is_user_image(relative_key: str) -> bool:
    low = relative_key.lower()
    return (
        (low.startswith("uploads/") or low.startswith("assets/"))
        and low.endswith(IMAGE_SUFFIXES)
    )


def infer_content_type(key: str, current: str | None) -> str:
    if current and current.startswith("image/"):
        return current
    guessed = mimetypes.guess_type(key)[0]
    return guessed if guessed and guessed.startswith("image/") else "application/octet-stream"


def head_or_none(s3, bucket: str, key: str):
    try:
        return s3.head_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        code = str((exc.response.get("Error") or {}).get("Code") or "")
        if code in {"404", "NoSuchKey", "NotFound"}:
            return None
        raise


def ensure_content_row(table, sha256: str, object_key: str, content_type: str, size_bytes: int, now: int) -> None:
    try:
        table.put_item(
            Item={
                "pk": content_pk(sha256),
                "sha256": sha256,
                "objectKey": object_key,
                "contentType": content_type,
                "sizeBytes": Decimal(size_bytes),
                "refCount": Decimal(0),
                "createdAt": Decimal(now),
                "updatedAt": Decimal(now),
            },
            ConditionExpression="attribute_not_exists(pk)",
        )
    except ClientError as exc:
        if (exc.response.get("Error") or {}).get("Code") != "ConditionalCheckFailedException":
            raise


def ensure_reference(table, user_id: str, relative_key: str, sha256: str, source_version_id: str, now: int) -> bool:
    key = ref_pk(user_id, relative_key)
    existing = table.get_item(Key={"pk": key}).get("Item")
    if existing:
        table.update_item(
            Key={"pk": key},
            UpdateExpression="SET sha256 = :sha, sourceVersionId = :version, updatedAt = :now",
            ExpressionAttributeValues={
                ":sha": sha256,
                ":version": source_version_id or "",
                ":now": Decimal(now),
            },
        )
        return False

    table.put_item(
        Item={
            "pk": key,
            "userId": user_id,
            "relativeKey": relative_key,
            "sha256": sha256,
            "sourceVersionId": source_version_id or "",
            "createdAt": Decimal(now),
            "updatedAt": Decimal(now),
        }
    )
    table.update_item(
        Key={"pk": content_pk(sha256)},
        UpdateExpression="SET updatedAt = :now ADD refCount :one",
        ExpressionAttributeValues={":now": Decimal(now), ":one": Decimal(1)},
    )
    return True


def canonical_hash(s3, bucket: str, key: str) -> str:
    obj = s3.get_object(Bucket=bucket, Key=key)
    return sha256_stream(obj["Body"])


def resolve_resources(cfn):
    bucket = cfn.describe_stack_resource(
        StackName=STACK_NAME,
        LogicalResourceId="PrivateStorageBucket",
    )["StackResourceDetail"]["PhysicalResourceId"]
    table = cfn.describe_stack_resource(
        StackName=STACK_NAME,
        LogicalResourceId="IdentityTable",
    )["StackResourceDetail"]["PhysicalResourceId"]
    return bucket, table


def list_user_images(s3, bucket: str):
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix="users/"):
        for item in page.get("Contents", []):
            split = split_user_key(item["Key"])
            if not split:
                continue
            user_id, relative_key = split
            if is_user_image(relative_key):
                yield item, user_id, relative_key


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate RIST private images to shared content-addressed storage.")
    parser.add_argument("--apply", action="store_true", help="Apply the migration. Default is read-only audit.")
    parser.add_argument(
        "--purge-source-version",
        action="store_true",
        help="After canonical copy + alias verification, delete the original full-byte S3 version.",
    )
    args = parser.parse_args()

    session = boto3.session.Session()
    s3 = session.client("s3")
    cfn = session.client("cloudformation")
    dynamodb = session.resource("dynamodb")

    bucket, table_name = resolve_resources(cfn)
    table = dynamodb.Table(table_name)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    rows = []
    groups: dict[str, list[dict]] = defaultdict(list)
    verified_canonical: set[str] = set()

    for item, user_id, relative_key in list_user_images(s3, bucket):
        full_key = item["Key"]
        head = s3.head_object(Bucket=bucket, Key=full_key)
        metadata = head.get("Metadata") or {}
        existing_sha = (metadata.get("rist-content-sha256") or "").lower()
        source_version = str(head.get("VersionId") or "")
        content_type = infer_content_type(full_key, head.get("ContentType"))

        if existing_sha:
            sha = existing_sha
            size_bytes = int(metadata.get("rist-content-bytes") or 0)
            canonical = content_key(sha)
            state = "already-reference"
        else:
            obj = s3.get_object(Bucket=bucket, Key=full_key)
            sha = sha256_stream(obj["Body"])
            size_bytes = int(head.get("ContentLength") or item.get("Size") or 0)
            canonical = content_key(sha)
            state = "legacy-full-copy"

        row = {
            "userId": user_id,
            "relativeKey": relative_key,
            "sourceKey": full_key,
            "sourceVersionId": source_version,
            "sha256": sha,
            "sizeBytes": size_bytes,
            "contentType": content_type,
            "canonicalKey": canonical,
            "stateBefore": state,
        }
        rows.append(row)
        groups[sha].append(row)

        if not args.apply:
            continue

        canonical_head = head_or_none(s3, bucket, canonical)
        if canonical_head is None:
            if existing_sha:
                raise RuntimeError(f"Alias target is missing for {full_key}: {canonical}")
            copy_source = {"Bucket": bucket, "Key": full_key}
            if source_version and source_version != "null":
                copy_source["VersionId"] = source_version
            s3.copy_object(
                Bucket=bucket,
                Key=canonical,
                CopySource=copy_source,
                ContentType=content_type,
                MetadataDirective="REPLACE",
                Metadata={"rist-sha256": sha},
            )
            canonical_head = s3.head_object(Bucket=bucket, Key=canonical)

        if sha not in verified_canonical:
            actual = canonical_hash(s3, bucket, canonical)
            if actual != sha:
                raise RuntimeError(f"Canonical hash mismatch for {canonical}")
            verified_canonical.add(sha)

        now = now_epoch()
        ensure_content_row(table, sha, canonical, content_type, size_bytes, now)
        ensure_reference(table, user_id, relative_key, sha, source_version, now)

        if not existing_sha:
            marker = {
                "type": "shaelvien-content-reference",
                "sha256": sha,
                "contentType": content_type,
                "sizeBytes": size_bytes,
            }
            s3.put_object(
                Bucket=bucket,
                Key=full_key,
                Body=json.dumps(marker, separators=(",", ":")).encode(),
                ContentType="application/vnd.shaelvien.content-ref+json",
                Metadata={
                    "rist-content-sha256": sha,
                    "rist-content-type": content_type,
                    "rist-content-bytes": str(size_bytes),
                },
            )

            verify = s3.head_object(Bucket=bucket, Key=full_key)
            if (verify.get("Metadata") or {}).get("rist-content-sha256") != sha:
                raise RuntimeError(f"Alias verification failed for {full_key}")

            if args.purge_source_version and source_version and source_version != "null":
                s3.delete_object(Bucket=bucket, Key=full_key, VersionId=source_version)
                row["sourceVersionPurged"] = True
            else:
                row["sourceVersionPurged"] = False

        row["stateAfter"] = "content-reference"

    total_current_bytes = sum(r["sizeBytes"] for r in rows)
    unique_bytes = sum(max(r["sizeBytes"] for r in group) for group in groups.values())
    duplicate_bytes = max(0, total_current_bytes - unique_bytes)
    duplicate_groups = sum(1 for group in groups.values() if len(group) > 1)

    report = {
        "migration": "shaelvien-private-assets-content-addressed-v1",
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "applied": args.apply,
        "purgeSourceVersion": args.purge_source_version,
        "bucket": bucket,
        "identityTable": table_name,
        "assetReferences": len(rows),
        "uniqueContentHashes": len(groups),
        "duplicateGroups": duplicate_groups,
        "currentLogicalBytes": total_current_bytes,
        "uniqueLogicalBytes": unique_bytes,
        "deduplicableLogicalBytes": duplicate_bytes,
        "rows": rows,
    }

    report_path = f"/tmp/shaelvien-private-asset-migration-{stamp}.json"
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    if args.apply:
        report_key = f"migration-reports/atomic-assets/{stamp}.json"
        s3.upload_file(
            report_path,
            bucket,
            report_key,
            ExtraArgs={"ContentType": "application/json"},
        )
        report["reportObjectKey"] = report_key

    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=2))
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
