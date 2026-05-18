import os
from typing import Optional
from urllib.parse import urlparse

from pydantic import HttpUrl, TypeAdapter

_http_url_adapter = TypeAdapter(HttpUrl)


def get_allowed_media_url_prefixes() -> list[str]:
    prefixes: list[str] = []
    r2_public = os.getenv("R2_PUBLIC_URL", "").strip().rstrip("/")
    if r2_public:
        prefixes.append(r2_public)

    extra = os.getenv("ALLOWED_MEDIA_URL_PREFIXES", "").strip()
    if extra:
        prefixes.extend(p.strip().rstrip("/") for p in extra.split(",") if p.strip())

    return prefixes


def validate_media_url(value: Optional[str], field_name: str) -> Optional[str]:
    if value is None or value == "":
        return None

    parsed = _http_url_adapter.validate_python(value)
    url_str = str(parsed)

    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"{field_name} must use http or https")

    allowed_prefixes = get_allowed_media_url_prefixes()
    if allowed_prefixes:
        if not any(url_str.startswith(prefix) for prefix in allowed_prefixes):
            raise ValueError(
                f"{field_name} must start with an allowed media host: "
                + ", ".join(allowed_prefixes)
            )
    else:
        host = urlparse(url_str).hostname or ""
        if not host:
            raise ValueError(f"{field_name} must be a valid URL")

    return url_str
