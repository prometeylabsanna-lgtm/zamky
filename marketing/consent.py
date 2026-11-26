"""Перша сторона CMP: згода лише після явного кліку Accept/Reject."""

COOKIE_NAME = "zamky_consent"
VALUE_ALL = "all"
VALUE_NECESSARY = "necessary"
ALLOWED = frozenset({VALUE_ALL, VALUE_NECESSARY})


def read_consent(request) -> str:
    if request is None:
        return ""
    raw = (request.COOKIES.get(COOKIE_NAME) or "").strip()
    return raw if raw in ALLOWED else ""


def allows_pixels(request) -> bool:
    return read_consent(request) == VALUE_ALL
