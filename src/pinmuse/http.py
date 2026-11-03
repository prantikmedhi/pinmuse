"""Tiny stdlib HTTP helpers (no requests/httpx dependency)."""

from __future__ import annotations

import json
import os
import random
import time
import uuid
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# Be a polite client: human-ish volume, never hammer a site.
_MIN_INTERVAL = float(os.environ.get("PINMUSE_MIN_INTERVAL", "0.8"))
_last_call: dict[str, float] = {}


class HTTPFailure(RuntimeError):
    def __init__(self, status: int, message: str, body: str = ""):
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.body = body


def _throttle(host: str) -> None:
    now = time.monotonic()
    wait = _last_call.get(host, 0) + _MIN_INTERVAL - now
    if wait > 0:
        time.sleep(wait + random.uniform(0, 0.25))
    _last_call[host] = time.monotonic()


def request(
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    json_body: Any = None,
    data: bytes | None = None,
    timeout: float = 60,
    throttle: bool = False,
    retries: int = 2,
) -> bytes:
    if params:
        url = url + ("&" if "?" in url else "?") + urlencode(params)
    hdrs = {"User-Agent": DEFAULT_UA}
    hdrs.update(headers or {})
    body = data
    if json_body is not None:
        body = json.dumps(json_body).encode()
        hdrs.setdefault("Content-Type", "application/json")
    host = url.split("/")[2] if "//" in url else url
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        if throttle:
            _throttle(host)
        try:
            with urlopen(Request(url, data=body, headers=hdrs, method=method), timeout=timeout) as r:
                return r.read()
        except HTTPError as e:
            text = e.read().decode("utf-8", "replace")[:2000]
            # retry only transient failures
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(2 ** (attempt + 1))
                last_err = HTTPFailure(e.code, e.reason, text)
                continue
            raise HTTPFailure(e.code, str(e.reason), text) from None
        except URLError as e:
            last_err = e
            if attempt < retries:
                time.sleep(2 ** (attempt + 1))
                continue
            raise
    raise last_err  # type: ignore[misc]


def get_json(url: str, **kw: Any) -> Any:
    return json.loads(request("GET", url, **kw))


def post_json(url: str, body: Any, **kw: Any) -> Any:
    return json.loads(request("POST", url, json_body=body, **kw))


def multipart(fields: dict[str, Any], files: list[tuple[str, str, bytes, str]]) -> tuple[bytes, str]:
    """Encode multipart/form-data. files = [(field, filename, bytes, mime)]."""
    boundary = "----pinmuse" + uuid.uuid4().hex
    out = bytearray()
    for k, v in fields.items():
        if v is None:
            continue
        out += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    for field, filename, content, mime in files:
        out += (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; "
            f"filename=\"{filename}\"\r\nContent-Type: {mime}\r\n\r\n"
        ).encode()
        out += content + b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={boundary}"
