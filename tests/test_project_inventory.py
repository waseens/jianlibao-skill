import importlib.util
import os
from pathlib import Path
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / "project-career-kit" / "scripts" / "project_inventory.py"
MODULE_SPEC = importlib.util.spec_from_file_location("project_inventory_under_test", SCRIPT_PATH)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
INVENTORY_MODULE = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(INVENTORY_MODULE)
build_inventory = INVENTORY_MODULE.build_inventory


class ProjectInventoryTests(unittest.TestCase):
    def test_discovers_readme_entrypoint_and_route_candidates(self):
        fixture = REPOSITORY_ROOT / "tests" / "fixtures" / "backend-learning-project"
        result = build_inventory(fixture)
        paths = {record["path"] for record in result["files"]}
        categories = {record["category"] for record in result["candidate_files"]}
        self.assertTrue(result["readme_present"])
        self.assertTrue({"README.md", "app/main.py", "app/api/tasks.py"} <= paths)
        self.assertTrue({"manifest", "entrypoint", "route_handler", "service"} <= categories)

    def test_excludes_sensitive_and_generated_content(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / ".env").write_text("TOKEN=not-for-output", encoding="utf-8")
            (root / "node_modules").mkdir()
            (root / "node_modules" / "bundle.js").write_text("ignored", encoding="utf-8")
            (root / "dist").mkdir()
            (root / "dist" / "app.js").write_text("ignored", encoding="utf-8")
            (root / "app.py").write_text("print('kept')", encoding="utf-8")
            paths = {record["path"] for record in build_inventory(root)["files"]}
        self.assertEqual(paths, {"app.py"})

    def test_limit_warning_stops_collection_without_reading_contents(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "a.py").write_text("a", encoding="utf-8")
            (root / "b.py").write_text("bb", encoding="utf-8")
            result = build_inventory(root, max_bytes=1)
        self.assertEqual([record["path"] for record in result["files"]], ["a.py"])
        self.assertTrue(any("max_bytes" in warning for warning in result["warnings"]))

    def test_ignores_a_file_symlink_when_the_platform_allows_one(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "project"
            external = Path(temporary_directory) / "external.py"
            root.mkdir()
            external.write_text("print('outside')", encoding="utf-8")
            try:
                os.symlink(external, root / "linked.py")
            except OSError as error:
                self.skipTest("file symlink unavailable: %s" % error)
            self.assertEqual(build_inventory(root)["files"], [])
