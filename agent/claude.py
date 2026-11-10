"""Minimaler Client für die Claude Messages API – nur Python-Standardbibliothek.

Bewusst ohne das offizielle `anthropic`-SDK: dessen Abhängigkeiten (pydantic-core, jiter)
müssen unter Termux/Android erst mit Rust kompiliert werden, was die Installation
sehr langsam und fehleranfällig macht.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

API_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/") + "/v1/messages"
API_VERSION = "2026-10-21"


class APIError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.message = message


def create_message(body: dict[str, Any], betas: list[str] | None = None, max_retries: int = 4) -> dict[str, Any]:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise APIError(401, "ANTHROPIC_API_KEY ist nicht gesetzt.")
    headers = {
        "x-api-key": api_key,
        "anthropic-version": API_VERSION,
        "content-type": "application/json",
    }
    if betas:
        headers["anthropic-beta"] = ",".join(betas)
    data = json.dumps(body).encode("utf-8")

    for attempt in range(max_retries + 1):
        request = urllib.request.Request(API_URL, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            raw = err.read().decode("utf-8", "replace")
            try:
                message = json.loads(raw)["error"]["message"]
            except (ValueError, KeyError, TypeError):
                message = raw[:500]
            retryable = err.code in (408, 409, 429) or err.code >= 500
            if not retryable or attempt == max_retries:
                raise APIError(err.code, message) from None
            delay = float(err.headers.get("retry-after") or 2 ** (attempt + 1))
        except (urllib.error.URLError, TimeoutError, ConnectionError) as err:
            if attempt == max_retries:
                raise APIError(0, f"Keine Verbindung: {err}") from None
            delay = 2 ** (attempt + 1)
        time.sleep(min(delay, 60))
    raise AssertionError("unreachable")
