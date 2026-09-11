# Node-local mirror of the desktop container's X11 clipboard. Read by the
# background X11 monitor to detect clipboard changes and written by the
# clipboard endpoints / ws clipboard bridge. Never assumed shared between
# processes (in k8s this stays with the node-bound gateway service).
_x11_clipboard = ""


def get_x11_clipboard() -> str:
    return _x11_clipboard


def set_x11_clipboard(text: str) -> None:
    global _x11_clipboard
    _x11_clipboard = text or ""
