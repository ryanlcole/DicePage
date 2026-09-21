#!/usr/bin/env python3
"""Zero-cloud-inference-cost smoke test for the Shaelvien EI model layer.

Runs against an OpenAI-compatible server such as LM Studio on localhost.
It exposes exactly one harmless local tool so we can verify that the selected
model can follow the Shaelvien authority prompt and perform a tool call before
we connect it to AgentCore Gateway.

No AWS credentials are read and no RIST state can be mutated by this script.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

from agent import SYSTEM_PROMPT

BASE_URL = os.environ.get("EI_OPENAI_BASE_URL", "http://127.0.0.1:1234/v1").rstrip("/")
API_KEY = os.environ.get("EI_API_KEY", "")
REQUESTED_MODEL = os.environ.get("EI_MODEL", "").strip()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "health",
            "description": "Return the authority state of this local Shaelvien EI smoke test. This tool never mutates state.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    }
]


def _request(method: str, path: str, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = "Bearer " + API_KEY
    request = urllib.request.Request(BASE_URL + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise SystemExit(
            "Cannot reach the local EI server at "
            + BASE_URL
            + ". Start LM Studio Developer > Server and keep it bound to localhost. "
            + str(exc)
        ) from exc


def _model_id() -> str:
    if REQUESTED_MODEL:
        return REQUESTED_MODEL
    models = _request("GET", "/models").get("data") or []
    if not models:
        raise SystemExit("LM Studio is reachable but no model is loaded.")
    return str(models[0]["id"])


def _chat(model: str, messages: list[dict]) -> dict:
    payload = {
        "model": model,
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
        "temperature": 0.1,
        "max_tokens": 500,
    }
    data = _request("POST", "/chat/completions", payload)
    choices = data.get("choices") or []
    if not choices:
        raise SystemExit("Model server returned no choices: " + json.dumps(data)[:1200])
    return choices[0]["message"]


def main() -> int:
    model = _model_id()
    print("Shaelvien EI local model:", model)
    print("Endpoint:", BASE_URL)
    print("Cloud inference cost: $0 for this local test")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Call the health tool first. Then tell me whether you have authority "
                "to mutate RIST world state and identify your provenance."
            ),
        },
    ]

    assistant = _chat(model, messages)
    tool_calls = assistant.get("tool_calls") or []
    if not tool_calls:
        print(json.dumps(assistant, indent=2))
        print("\nFAIL: model did not call the required health tool.")
        return 2

    messages.append(assistant)
    for call in tool_calls:
        fn = (call.get("function") or {}).get("name")
        if fn != "health":
            print("FAIL: model attempted an unavailable tool:", fn)
            return 3
        result = {
            "ok": True,
            "authority": "read-only",
            "provenance": "SHAELVIEN_EI",
            "stateMutated": False,
            "writesAvailable": False,
        }
        messages.append(
            {
                "role": "tool",
                "tool_call_id": call.get("id"),
                "name": "health",
                "content": json.dumps(result),
            }
        )

    final = _chat(model, messages)
    text = final.get("content") or ""
    print("\n--- EI response ---")
    print(text.strip())
    print("\nPASS: tool boundary exercised without AWS or RIST writes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
