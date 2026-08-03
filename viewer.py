#!/usr/bin/env python3
"""Small, dependency-free browser viewer for Concepts .concept documents."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import plistlib
import struct
import sys
import threading
import urllib.parse
import webbrowser
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DEFAULT_DOCUMENT = (
    Path.home()
    / "Library/Mobile Documents/iCloud~com~tophatch~Concepts/Documents/Mindmaps"
)
STATIC_DIR = Path(__file__).resolve().parent / "static"
SVG_CACHE: dict[tuple[str, float], bytes] = {}


def render_document(document: Path) -> bytes:
    """Convert Concepts' archived strokes into a full-canvas SVG."""
    cache_key = (str(document), document.stat().st_mtime)
    if cache_key in SVG_CACHE:
        return SVG_CACHE[cache_key]

    with zipfile.ZipFile(document) as archive:
        archive_data = plistlib.loads(archive.read("Strokes.plist"))
    objects = archive_data["$objects"]

    def resolve(value):
        return objects[value.data] if isinstance(value, plistlib.UID) else value

    def class_name(value) -> str | None:
        if not isinstance(value, dict):
            return None
        descriptor = resolve(value.get("$class"))
        return descriptor.get("$classname") if isinstance(descriptor, dict) else None

    strokes = []
    bounds = [float("inf"), float("inf"), float("-inf"), float("-inf")]
    identity = (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)

    for stroke in objects:
        if class_name(stroke) != "Stroke":
            continue
        point_data = resolve(stroke.get("strokePointsNonOptionalAngles"))
        if not isinstance(point_data, bytes) or len(point_data) < 16:
            continue
        transform_data = resolve(stroke.get("diSavedTransform"))
        transform = struct.unpack("<16f", transform_data) if isinstance(transform_data, bytes) else identity
        points = []
        for offset in range(0, len(point_data) - 15, 16):
            px, py = struct.unpack_from("<2f", point_data, offset)
            x = transform[0] * px + transform[4] * py + transform[12]
            y = transform[1] * px + transform[5] * py + transform[13]
            points.append((x, y))
            bounds[0] = min(bounds[0], x)
            bounds[1] = min(bounds[1], y)
            bounds[2] = max(bounds[2], x)
            bounds[3] = max(bounds[3], y)

        brush = resolve(stroke.get("brushProperties"))
        color = resolve(brush.get("brushColor")) if isinstance(brush, dict) else {}
        red = round(float(color.get("UIRed", 1)) * 255)
        green = round(float(color.get("UIGreen", 1)) * 255)
        blue = round(float(color.get("UIBlue", 1)) * 255)
        brush_alpha = float(brush.get("brushAlpha", 1)) if isinstance(brush, dict) else 1
        color_alpha = float(color.get("UIAlpha", 1)) if isinstance(color, dict) else 1
        alpha = brush_alpha * color_alpha
        tool = int(brush.get("brushToolNew", 0)) if isinstance(brush, dict) else 0
        width = float(brush.get("brushWidth", 2))
        # Marker tool widths are stored relative to the zoom at which they were
        # drawn. Applying this scale restores the lighter, layered brush shape.
        if tool == 8:
            width *= float(stroke.get("scale", 1))
        strokes.append((points, f"rgb({red},{green},{blue})", alpha, max(width, 0.35), tool))

    if not strokes:
        raise ValueError("No renderable strokes found")

    margin = max(80.0, max(item[3] for item in strokes) * 2)
    left, top = bounds[0] - margin, bounds[1] - margin
    width, height = bounds[2] - bounds[0] + margin * 2, bounds[3] - bounds[1] + margin * 2
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="{left:.2f} {top:.2f} {width:.2f} {height:.2f}">',
        '<defs><pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">'
        '<circle cx="1" cy="1" r="1.25" fill="#353535"/></pattern>',
    ]

    # Concepts' marker is translucent and softly fades into and out of a stroke.
    # SVG's ordinary uniform polyline otherwise makes it look like a solid pen.
    for index, (points, color, alpha, _stroke_width, tool) in enumerate(strokes):
        if tool != 8:
            continue
        start, end = points[0], points[-1]
        marker_alpha = min(alpha, 0.62)
        parts.append(
            f'<linearGradient id="marker-{index}" gradientUnits="userSpaceOnUse" '
            f'x1="{start[0]:.1f}" y1="{start[1]:.1f}" x2="{end[0]:.1f}" y2="{end[1]:.1f}">'
            f'<stop offset="0" stop-color="{color}" stop-opacity="{marker_alpha * .16:.3f}"/>'
            f'<stop offset=".16" stop-color="{color}" stop-opacity="{marker_alpha:.3f}"/>'
            f'<stop offset=".82" stop-color="{color}" stop-opacity="{marker_alpha:.3f}"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="{marker_alpha * .12:.3f}"/>'
            '</linearGradient>'
        )
    parts.extend([
        '</defs>',
        f'<rect x="{left:.2f}" y="{top:.2f}" width="{width:.2f}" height="{height:.2f}" fill="#050505"/>',
        f'<rect x="{left:.2f}" y="{top:.2f}" width="{width:.2f}" height="{height:.2f}" fill="url(#grid)"/>',
        # Concepts stores this canvas with its horizontal axis reversed relative
        # to SVG. Mirror around the content center so handwriting reads normally.
        f'<g transform="translate({bounds[0] + bounds[2]:.2f} 0) scale(-1 1)" '
        'fill="none" stroke-linecap="round" stroke-linejoin="round">',
    ])
    for index, (points, color, alpha, stroke_width, tool) in enumerate(strokes):
        commands = [f"M{points[0][0]:.1f},{points[0][1]:.1f}"]
        commands.extend(f"L{x:.1f},{y:.1f}" for x, y in points[1:])
        # A one-point stroke needs a tiny segment so its round cap remains visible.
        if len(points) == 1:
            commands.append(f"l0.01,0")
        stroke_color = f"url(#marker-{index})" if tool == 8 else color
        stroke_opacity = 1 if tool == 8 else alpha
        line_cap = "butt" if tool == 8 else "round"
        parts.append(
            f'<path d="{" ".join(commands)}" stroke="{stroke_color}" stroke-opacity="{stroke_opacity:.3f}" '
            f'stroke-width="{stroke_width:.2f}" stroke-linecap="{line_cap}"/>'
        )
    parts.append("</g></svg>")
    result = "".join(parts).encode("utf-8")
    SVG_CACHE.clear()
    SVG_CACHE[cache_key] = result
    return result


def find_documents(source: Path) -> list[Path]:
    source = source.expanduser().resolve()
    if source.is_file():
        return [source] if source.suffix.lower() == ".concept" else []
    if source.is_dir():
        return sorted(source.rglob("*.concept"), key=lambda p: p.name.casefold())
    return []


class DocumentCatalog:
    """Thread-safe collection of documents served by the viewer."""

    def __init__(self, source: Path):
        self._lock = threading.RLock()
        self._source = source.expanduser().resolve()
        self._documents: list[Path] = []
        self.set_source(source)

    def set_source(self, source: Path) -> list[Path]:
        resolved = source.expanduser().resolve()
        documents = find_documents(resolved)
        with self._lock:
            self._source = resolved
            self._documents = documents
            SVG_CACHE.clear()
        return list(documents)

    def refresh(self) -> list[Path]:
        """Rescan the current source without changing the selected directory."""
        with self._lock:
            source = self._source
        documents = find_documents(source)
        with self._lock:
            # Do not let a slower scan overwrite a directory selected meanwhile.
            if source == self._source:
                self._documents = documents
            return list(self._documents)

    def snapshot(self) -> tuple[Path, list[Path]]:
        with self._lock:
            return self._source, list(self._documents)

    def document(self, index: int) -> Path | None:
        if index < 0:
            return None
        with self._lock:
            try:
                return self._documents[index]
            except IndexError:
                return None


def make_handler(catalog: DocumentCatalog):
    class ViewerHandler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:
            print(f"[viewer] {fmt % args}")

        def send_bytes(self, body: bytes, content_type: str, status: int = 200) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def send_json(self, value, status: int = 200) -> None:
            self.send_bytes(
                json.dumps(value, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8",
                status,
            )

        def document(self, query: dict[str, list[str]]) -> Path | None:
            try:
                return catalog.document(int(query.get("id", [""])[0]))
            except ValueError:
                return None

        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            query = urllib.parse.parse_qs(parsed.query)

            if parsed.path == "/api/documents":
                if query.get("refresh") == ["1"]:
                    catalog.refresh()
                items = []
                source, documents = catalog.snapshot()
                base = source if source.is_dir() else source.parent
                for index, path in enumerate(documents):
                    try:
                        stat = path.stat()
                    except OSError:
                        continue
                    try:
                        relative = str(path.relative_to(base))
                    except ValueError:
                        relative = str(path)
                    items.append(
                        {
                            "id": index,
                            "name": path.stem,
                            "relativePath": relative,
                            "path": str(path),
                            "size": stat.st_size,
                            "modified": stat.st_mtime,
                        }
                    )
                return self.send_json({"documents": items, "source": str(source)})

            if parsed.path == "/api/render":
                document = self.document(query)
                if document is None:
                    return self.send_json({"error": "Unknown document"}, 404)
                try:
                    return self.send_bytes(render_document(document), "image/svg+xml; charset=utf-8")
                except (zipfile.BadZipFile, KeyError, OSError, ValueError, struct.error) as exc:
                    return self.send_json({"error": f"Cannot render document: {exc}"}, 422)

            if parsed.path == "/api/image":
                document = self.document(query)
                if document is None:
                    return self.send_json({"error": "Unknown document"}, 404)
                try:
                    with zipfile.ZipFile(document) as archive:
                        image = archive.read("Thumb.jpg")
                    return self.send_bytes(image, "image/jpeg")
                except (zipfile.BadZipFile, KeyError, OSError) as exc:
                    return self.send_json({"error": f"Cannot read preview: {exc}"}, 422)

            if parsed.path == "/api/reveal":
                document = self.document(query)
                if document is None:
                    return self.send_json({"error": "Unknown document"}, 404)
                try:
                    os.spawnlp(os.P_NOWAIT, "open", "open", "-R", str(document))
                    return self.send_json({"ok": True})
                except OSError as exc:
                    return self.send_json({"error": str(exc)}, 500)

            requested = "index.html" if parsed.path == "/" else parsed.path.lstrip("/")
            candidate = (STATIC_DIR / requested).resolve()
            try:
                candidate.relative_to(STATIC_DIR.resolve())
            except ValueError:
                return self.send_json({"error": "Not found"}, 404)
            if not candidate.is_file():
                return self.send_json({"error": "Not found"}, 404)
            content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
            if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}:
                content_type += "; charset=utf-8"
            return self.send_bytes(candidate.read_bytes(), content_type)

    return ViewerHandler


def main() -> int:
    parser = argparse.ArgumentParser(description="Display Concepts mind-map previews in a browser.")
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        default=DEFAULT_DOCUMENT,
        help="A .concept file or a directory to scan recursively",
    )
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-open", action="store_true", help="Do not open the browser")
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    catalog = DocumentCatalog(source)
    _source, documents = catalog.snapshot()
    if not documents:
        print(f"No .concept documents found at: {source}", file=sys.stderr)
        return 1

    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(catalog))
    url = f"http://127.0.0.1:{args.port}"
    print(f"Concepts Mindmap Viewer: {url}")
    print(f"Found {len(documents)} document(s). Press Control-C to stop.")
    if not args.no_open:
        threading.Timer(0.35, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
