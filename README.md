# Concepts Mindmap Viewer

A private, local macOS viewer for [Concepts](https://concepts.app/) `.concept` documents. It renders the archived stroke canvas—not just the viewport thumbnail—and provides pan, zoom, rotation, search, and “Show in Finder.”

> [!NOTE]
> This is an independent, unofficial project. It is not affiliated with or endorsed by TopHatch or Concepts.

## Features

- Runs as a regular macOS application—no Terminal or separate browser required
- Uses a native folder picker and remembers your Concepts directory
- Renders strokes from a `.concept` archive as a full-canvas SVG
- Scans directories recursively and provides a searchable document list
- Supports pan, zoom, fit-to-window, and 90° rotation
- Reveals the source document in Finder
- Processes documents locally and never modifies or uploads them
- Retains a dependency-free command-line mode for developers

## Install the macOS app

Signed and notarized universal builds for macOS 14 or later will be available from [GitHub Releases](https://github.com/mtietz/concepts-mindmap-viewer/releases). Download the DMG, drag **Concepts Mindmap Viewer** into Applications, and open it normally.

On first launch, choose the folder containing your `.concept` documents. Use **Folder…** in the toolbar whenever you want to change it. The selection is saved in:

```text
~/Library/Application Support/Concepts Mindmap Viewer/settings.json
```

The standard Concepts mindmap directory is:

```text
~/Library/Mobile Documents/iCloud~com~tophatch~Concepts/Documents/Mindmaps
```

Until the first signed release is published, developers can [build the app locally](#build-the-app).

## Controls

| Action | Control |
| --- | --- |
| Choose Concepts directory | **Folder…** |
| Show or hide sidebar | **☰** or **Command-B** |
| Zoom | Scroll, **+**, or **−** |
| Pan | Drag the canvas |
| Rotate | **↶** / **↷** or **[** / **]** |
| Reset rotation | Click the degree value |
| Fit to window | Double-click or click **Fit** |
| Reveal source file | Click **Finder** |

## Command-line mode

The original browser-based viewer remains available and uses only Python's standard library. It requires macOS and Python 3.10 or later.

```bash
git clone https://github.com/mtietz/concepts-mindmap-viewer.git
cd concepts-mindmap-viewer
python3 viewer.py
```

Open a specific document or recursively scan another directory:

```bash
python3 viewer.py "/path/to/drawing.concept"
python3 viewer.py "/path/to/concepts/directory"
```

Use another port or prevent the browser from opening automatically:

```bash
python3 viewer.py --port 9000 --no-open "/path/to/concepts/directory"
```

Press **Control-C** to stop the command-line viewer. You can also double-click **`Launch Viewer.command`** after cloning the repository.

## Build the app

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-build.txt
./scripts/build_macos.sh
open "dist/Concepts Mindmap Viewer.app"
```

The desktop shell uses [pywebview](https://pywebview.flowrl.com/) and macOS WKWebView. PyInstaller bundles Python and all runtime dependencies into the app.

Maintainers can find code-signing, notarization, and release instructions in [docs/releasing.md](docs/releasing.md).

## Privacy and security

The embedded server binds to an automatically selected port on `127.0.0.1`, so it is available only from your computer rather than your local network. Document paths and rendered content remain local. As with any local file utility, only open files you trust.

## Limitations

The `.concept` archive format is not a public API and may change between Concepts releases. The viewer currently focuses on archived strokes; other document elements may not render. It is designed for macOS and Finder integration.

## Development

Run the checks with:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile viewer.py desktop.py
```

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Licensed under the [MIT License](LICENSE).
