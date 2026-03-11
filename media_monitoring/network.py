from __future__ import annotations

import os
from collections.abc import Callable
from urllib.parse import quote
from urllib.request import ProxyHandler, Request, build_opener


DEFAULT_PROXY_HOST = "pr.oxylabs.io"
DEFAULT_PROXY_PORT = "7777"


def _truthy(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _proxy_url() -> str | None:
    username = os.getenv("OXYLABS_USERNAME")
    password = os.getenv("OXYLABS_PASSWORD")
    if not username or not password:
        return None

    host = os.getenv("OXYLABS_PROXY_HOST", DEFAULT_PROXY_HOST)
    port = os.getenv("OXYLABS_PROXY_PORT", DEFAULT_PROXY_PORT)

    user_enc = quote(username, safe="")
    pass_enc = quote(password, safe="")
    return f"http://{user_enc}:{pass_enc}@{host}:{port}"


def _open(req: Request, timeout: int, use_proxy: bool) -> bytes:
    if use_proxy:
        proxy = _proxy_url()
        if not proxy:
            raise RuntimeError("Proxy requested but OXYLABS credentials are not configured")
        opener = build_opener(ProxyHandler({"http": proxy, "https": proxy}))
        with opener.open(req, timeout=timeout) as response:
            return response.read()

    with build_opener().open(req, timeout=timeout) as response:
        return response.read()


def fetch_bytes(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: int = 20,
    validator: Callable[[bytes], bool] | None = None,
) -> bytes:
    """Fetch a URL with proxy-first behavior (if configured), then direct fallback.

    Behavior can be changed with USE_PROXY_DEFAULT env var:
    - true (default): proxy -> direct
    - false: direct -> proxy
    """
    req = Request(url, headers=headers or {})
    proxy_first = _truthy(os.getenv("USE_PROXY_DEFAULT"), default=True)
    has_proxy = _proxy_url() is not None

    attempts: list[bool] = []
    if has_proxy:
        attempts = [True, False] if proxy_first else [False, True]
    else:
        attempts = [False]

    last_error: Exception | None = None
    for use_proxy in attempts:
        try:
            payload = _open(req, timeout=timeout, use_proxy=use_proxy)
            if validator is not None and not validator(payload):
                last_error = RuntimeError("Fetched payload failed validation")
                continue
            return payload
        except Exception as exc:  # noqa: BLE001
            last_error = exc

    if last_error:
        raise last_error
    raise RuntimeError("No network attempt was executed")


def fetch_text(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: int = 20,
    encoding: str = "utf-8",
    validator: Callable[[bytes], bool] | None = None,
) -> str:
    return fetch_bytes(url=url, headers=headers, timeout=timeout, validator=validator).decode(
        encoding, errors="replace"
    )
