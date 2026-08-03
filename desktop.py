#!/usr/bin/env python3
"""Native macOS shell for Concepts Mindmap Viewer."""

from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

from viewer import DEFAULT_DOCUMENT, DocumentCatalog, make_handler

APP_NAME = "Concepts Mindmap Viewer"
CONFIG_DIR = Path.home() / "Library" / "Application Support" / APP_NAME
CONFIG_FILE = CONFIG_DIR / "settings.json"


def load_source() -> Path | None:
    """Load the user's saved Concepts directory, if it is valid."""
    try:
        value = json.loads(CONFIG_FILE.read_text(encoding="utf-8")).get("source")
        return Path(value).expanduser().resolve() if isinstance(value, str) and value else None
    except (OSError, ValueError, TypeError):
        return None


def save_source(source: Path) -> None:
    """Persist the selected directory atomically."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    temporary = CONFIG_FILE.with_suffix(".tmp")
    temporary.write_text(
        json.dumps({"source": str(source)}, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(CONFIG_FILE)


class DesktopApi:
    """Methods exposed to JavaScript by pywebview."""

    def __init__(self, catalog: DocumentCatalog, webview_module: Any):
        self.catalog = catalog
        self.webview = webview_module
        self.window: Any = None

    def choose_folder(self) -> dict[str, object] | None:
        source, _documents = self.catalog.snapshot()
        initial_directory = source if source.is_dir() else source.parent
        result = self.window.create_file_dialog(
            self.webview.FileDialog.FOLDER,
            directory=str(initial_directory),
        )
        if not result:
            return None

        selected = Path(result[0]).expanduser().resolve()
        documents = self.catalog.set_source(selected)
        save_source(selected)
        return {"source": str(selected), "count": len(documents)}


def main() -> int:
    try:
        import webview
    except ImportError:
        raise SystemExit(
            "The desktop dependency is missing. Install it with "
            "'python3 -m pip install -r requirements-desktop.txt'."
        )

    configured_source = load_source()
    catalog = DocumentCatalog(configured_source or DEFAULT_DOCUMENT)
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(catalog))
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    url = f"http://127.0.0.1:{server.server_port}"

    api = DesktopApi(catalog, webview)
    window = webview.create_window(
        APP_NAME,
        url,
        js_api=api,
        width=1280,
        height=820,
        min_size=(800, 560),
    )
    api.window = window

    try:
        webview.start()
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
