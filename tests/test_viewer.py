import plistlib
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path

import desktop
import viewer


class FindDocumentsTests(unittest.TestCase):
    def test_finds_concept_files_recursively_and_sorts_by_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "nested").mkdir()
            (root / "zebra.concept").touch()
            (root / "nested" / "Alpha.concept").touch()
            (root / "notes.txt").touch()

            self.assertEqual(
                [path.name for path in viewer.find_documents(root)],
                ["Alpha.concept", "zebra.concept"],
            )

    def test_accepts_a_single_concept_file(self):
        with tempfile.TemporaryDirectory() as directory:
            document = Path(directory) / "drawing.concept"
            document.touch()
            self.assertEqual(viewer.find_documents(document), [document.resolve()])

    def test_rejects_a_non_concept_file(self):
        with tempfile.TemporaryDirectory() as directory:
            document = Path(directory) / "drawing.zip"
            document.touch()
            self.assertEqual(viewer.find_documents(document), [])


class DocumentCatalogTests(unittest.TestCase):
    def test_can_switch_directories_at_runtime(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_document = Path(first) / "first.concept"
            second_document = Path(second) / "second.concept"
            first_document.touch()
            second_document.touch()
            catalog = viewer.DocumentCatalog(Path(first))

            self.assertEqual(catalog.document(0), first_document.resolve())
            self.assertIsNone(catalog.document(-1))
            catalog.set_source(Path(second))
            source, documents = catalog.snapshot()

            self.assertEqual(source, Path(second).resolve())
            self.assertEqual(documents, [second_document.resolve()])


class DesktopSettingsTests(unittest.TestCase):
    def test_saves_and_loads_selected_source(self):
        with tempfile.TemporaryDirectory() as directory:
            config_dir = Path(directory) / "Application Support"
            config_file = config_dir / "settings.json"
            source = Path(directory) / "Mindmaps"
            source.mkdir()
            original_dir, original_file = desktop.CONFIG_DIR, desktop.CONFIG_FILE
            try:
                desktop.CONFIG_DIR = config_dir
                desktop.CONFIG_FILE = config_file
                desktop.save_source(source)
                self.assertEqual(desktop.load_source(), source.resolve())
            finally:
                desktop.CONFIG_DIR = original_dir
                desktop.CONFIG_FILE = original_file

    def test_invalid_settings_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "settings.json"
            config_file.write_text("not json", encoding="utf-8")
            original_file = desktop.CONFIG_FILE
            try:
                desktop.CONFIG_FILE = config_file
                self.assertIsNone(desktop.load_source())
            finally:
                desktop.CONFIG_FILE = original_file

    def test_folder_picker_updates_catalog_and_settings(self):
        class FakeFileDialog:
            FOLDER = "folder"

        class FakeWebview:
            FileDialog = FakeFileDialog

        class FakeWindow:
            def __init__(self, selected):
                self.selected = selected

            def create_file_dialog(self, dialog_type, directory):
                self.dialog_type = dialog_type
                self.directory = directory
                return (str(self.selected),)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selected = root / "Selected"
            selected.mkdir()
            (selected / "drawing.concept").touch()
            config_dir = root / "settings"
            original_dir, original_file = desktop.CONFIG_DIR, desktop.CONFIG_FILE
            try:
                desktop.CONFIG_DIR = config_dir
                desktop.CONFIG_FILE = config_dir / "settings.json"
                catalog = viewer.DocumentCatalog(root)
                api = desktop.DesktopApi(catalog, FakeWebview)
                api.window = FakeWindow(selected)

                result = api.choose_folder()

                resolved = selected.resolve()
                self.assertEqual(result, {"source": str(resolved), "count": 1})
                self.assertEqual(desktop.load_source(), resolved)
                self.assertEqual(catalog.document(0), resolved / "drawing.concept")
            finally:
                desktop.CONFIG_DIR = original_dir
                desktop.CONFIG_FILE = original_file


class RenderDocumentTests(unittest.TestCase):
    def setUp(self):
        viewer.SVG_CACHE.clear()

    @staticmethod
    def make_document(path: Path, *, include_stroke: bool = True) -> None:
        objects = ["$null", {"$classname": "Stroke"}]
        if include_stroke:
            points = struct.pack("<4f", 10, 20, 0, 0) + struct.pack("<4f", 30, 40, 0, 0)
            objects.append(
                {
                    "$class": plistlib.UID(1),
                    "strokePointsNonOptionalAngles": points,
                    "brushProperties": {
                        "brushColor": {
                            "UIRed": 1.0,
                            "UIGreen": 0.5,
                            "UIBlue": 0.0,
                            "UIAlpha": 1.0,
                        },
                        "brushAlpha": 0.75,
                        "brushToolNew": 0,
                        "brushWidth": 3.0,
                    },
                }
            )
        archive = plistlib.dumps({"$objects": objects}, fmt=plistlib.FMT_BINARY)
        with zipfile.ZipFile(path, "w") as concept:
            concept.writestr("Strokes.plist", archive)

    def test_renders_archived_strokes_as_svg(self):
        with tempfile.TemporaryDirectory() as directory:
            document = Path(directory) / "drawing.concept"
            self.make_document(document)

            svg = viewer.render_document(document).decode("utf-8")

            self.assertTrue(svg.startswith('<svg xmlns="http://www.w3.org/2000/svg"'))
            self.assertIn('stroke="rgb(255,128,0)"', svg)
            self.assertIn('stroke-opacity="0.750"', svg)
            self.assertIn("M10.0,20.0 L30.0,40.0", svg)

    def test_rejects_an_archive_without_strokes(self):
        with tempfile.TemporaryDirectory() as directory:
            document = Path(directory) / "empty.concept"
            self.make_document(document, include_stroke=False)

            with self.assertRaisesRegex(ValueError, "No renderable strokes found"):
                viewer.render_document(document)


if __name__ == "__main__":
    unittest.main()
