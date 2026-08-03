# Concepts Mindmap Viewer

A private, local macOS viewer for [Concepts](https://concepts.app/) `.concept` documents. It renders the archived stroke canvas—not just the viewport thumbnail—and provides pan, zoom, rotation, search, and “Show in Finder.”

[![Latest release](https://img.shields.io/github/v/release/mtietz/concepts-mindmap-viewer?label=download)](https://github.com/mtietz/concepts-mindmap-viewer/releases/latest)
[![Tests](https://github.com/mtietz/concepts-mindmap-viewer/actions/workflows/test.yml/badge.svg)](https://github.com/mtietz/concepts-mindmap-viewer/actions/workflows/test.yml)

> [!NOTE]
> This is an independent, unofficial project. It is not affiliated with or endorsed by TopHatch or Concepts.

> [!TIP]
> **Keep your mindmaps synchronized:** On every device where you use Concepts, place the Concepts mindmap directory in a cloud-synced folder such as iCloud Drive. Then select that same cloud folder in Concepts Mindmap Viewer. Your cloud provider keeps the `.concept` files synchronized, while the viewer notices new and changed mindmaps automatically. Make sure cloud files are downloaded on the Mac before opening them.

## Features

- Runs as a regular macOS application—no Terminal or separate browser required
- Ships as a signed and Apple-notarized universal app for Apple Silicon and Intel Macs
- Uses a native folder picker and remembers your Concepts directory
- Renders strokes from a `.concept` archive as a full-canvas SVG
- Scans directories recursively and provides a searchable document list
- Detects new, changed, and removed mindmaps automatically
- Includes first-launch guidance and actionable empty states
- Supports pan, zoom, fit-to-window, and 90° rotation
- Reveals the source document in Finder
- Processes documents locally and never modifies or uploads them

## Install

1. Download **`Concepts-Mindmap-Viewer.dmg`** from the [latest release](https://github.com/mtietz/concepts-mindmap-viewer/releases/latest).
2. Open the DMG and drag **Concepts Mindmap Viewer** into **Applications**.
3. Open the app normally from Applications.
4. Choose the cloud folder containing your `.concept` documents.

The app requires macOS 14 or later. Use **Folder…** in the toolbar whenever you want to change the selected directory.

The standard Concepts mindmap directory in iCloud Drive is:

```text
~/Library/Mobile Documents/iCloud~com~tophatch~Concepts/Documents/Mindmaps
```

## Controls

| Action | Control |
| --- | --- |
| Choose Concepts directory | **Folder…** |
| Refresh immediately | **↻** |
| Show or hide sidebar | **☰** or **Command-B** |
| Zoom | Scroll, **+**, or **−** |
| Pan | Drag the canvas |
| Rotate | **↶** / **↷** or **[** / **]** |
| Reset rotation | Click the degree value |
| Fit to window | Double-click or click **Fit** |
| Reveal source file | Click **Finder** |

## Privacy and security

The viewer runs entirely on your Mac. Its embedded server binds only to `127.0.0.1`, so it is not exposed to your local network. Document paths and rendered content remain local. The app never modifies or uploads your mindmaps; synchronization is handled independently by your chosen cloud provider.

As with any local file utility, only open files you trust.

## Limitations

The `.concept` archive format is not a public API and may change between Concepts releases. The viewer currently focuses on archived strokes; other document elements may not render. It is designed for macOS and Finder integration.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and contribution guidelines.

## License

Licensed under the [MIT License](LICENSE).
