"""Private same-task bridge. The MCP database mount remains physically read-only."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from continuity_writer import ContinuityEvent


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def submit(item: ContinuityEvent):
    token = os.getenv("RELIC_APPEND_TOKEN", "")
    if not token:
        raise ValueError("continuity writer is not configured")
    # Fixed same-task address prevents caller-selected URLs and credential forwarding.
    request = Request("http://127.0.0.1:8080/v1/continuity-events",
                      data=item.model_dump_json().encode(), method="POST",
                      headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=40) as response:
            result = json.loads(response.read(8192))
    except HTTPError as exc:
        raise ValueError(f"continuity append rejected (HTTP {exc.code}); no success receipt received") from None
    except (URLError, TimeoutError, OSError, ValueError):
        raise ValueError("continuity receipt unavailable; retry the exact record with the same idempotency key") from None
    if (not isinstance(result, dict) or result.get("stored") is not True
            or not result.get("event_id") or result.get("canon_promoted") is not False
            or result.get("project") != item.project):
        raise ValueError("invalid persistence receipt; persistence is unconfirmed")
    return result
