import json
import os
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

TABLE_NAME = os.environ["KNOWLEDGE_TABLE"]
MAX_QUERY_ITEMS = max(1, min(int(os.environ.get("MAX_QUERY_ITEMS", "25")), 100))

_table = boto3.resource("dynamodb").Table(TABLE_NAME)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


def _tool_name(event: dict) -> str:
    for key in ("name", "toolName", "operationId"):
        value = event.get(key)
        if isinstance(value, str) and value:
            return value.split("___")[-1]

    context = event.get("context") or {}
    for key in ("name", "toolName", "operationId"):
        value = context.get(key)
        if isinstance(value, str) and value:
            return value.split("___")[-1]

    return ""


def _arguments(event: dict) -> dict:
    for key in ("arguments", "input", "parameters"):
        value = event.get(key)
        if isinstance(value, dict):
            return value

    request_body = event.get("requestBody")
    if isinstance(request_body, dict):
        return request_body

    return {}


def _response(payload: dict) -> dict:
    return _json_safe(payload)


def health(_: dict) -> dict:
    return {
        "ok": True,
        "authority": "read-only",
        "provenance": "SHAELVIEN_EI",
        "table": TABLE_NAME,
        "writesAvailable": False,
    }


def get_record(args: dict) -> dict:
    pk = str(args.get("pk", "")).strip()
    sk = str(args.get("sk", "")).strip()
    if not pk or not sk:
        raise ValueError("pk and sk are required")

    result = _table.get_item(
        Key={"PK": pk, "SK": sk},
        ConsistentRead=False,
    )
    item = result.get("Item")
    return {
        "found": item is not None,
        "record": item,
        "sourceKey": {"PK": pk, "SK": sk},
        "authority": "read-only",
    }


def query_scope(args: dict) -> dict:
    pk = str(args.get("pk", "")).strip()
    prefix = str(args.get("skPrefix", "")).strip()
    requested = int(args.get("limit", MAX_QUERY_ITEMS))
    limit = max(1, min(requested, MAX_QUERY_ITEMS))

    if not pk:
        raise ValueError("pk is required")

    key_expr = Key("PK").eq(pk)
    if prefix:
        key_expr = key_expr & Key("SK").begins_with(prefix)

    result = _table.query(
        KeyConditionExpression=key_expr,
        Limit=limit,
        ConsistentRead=False,
    )

    return {
        "items": result.get("Items", []),
        "count": int(result.get("Count", 0)),
        "truncated": "LastEvaluatedKey" in result,
        "scope": {"PK": pk, "SKPrefix": prefix or None},
        "authority": "read-only",
    }


TOOLS = {
    "health": health,
    "get_record": get_record,
    "query_scope": query_scope,
}


def lambda_handler(event, context):
    try:
        event = event or {}
        name = _tool_name(event)
        args = _arguments(event)

        if name not in TOOLS:
            return _response(
                {
                    "ok": False,
                    "error": "unknown_tool",
                    "tool": name,
                    "allowedTools": sorted(TOOLS),
                    "authority": "read-only",
                }
            )

        result = TOOLS[name](args)
        return _response({"ok": True, "result": result})
    except (ValueError, TypeError) as exc:
        return _response({"ok": False, "error": "invalid_request", "message": str(exc)})
    except Exception as exc:
        print(json.dumps({"event": "readonly_tool_error", "type": type(exc).__name__}))
        return _response({"ok": False, "error": "internal_error"})
