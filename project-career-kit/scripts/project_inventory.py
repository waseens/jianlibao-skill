"""Create a bounded, metadata-only inventory of a backend project."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any


IGNORED_DIRECTORIES = {
    ".git", "node_modules", "vendor", "dist", "build", "target", "bin", "obj",
    "coverage", ".venv", "__pycache__",
}
SENSITIVE_EXTENSIONS = {".pem", ".key", ".p12", ".pfx", ".crt", ".cer"}
PRIVATE_KEY_NAMES = {
    "id_rsa", "id_dsa", "id_ecdsa", "id_ecdsa_sk", "id_ed25519", "id_ed25519_sk", "id_xmss",
}
SOURCE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".kt", ".go", ".rb", ".php",
    ".cs", ".rs", ".c", ".cc", ".cpp", ".h", ".hpp", ".swift", ".scala",
}
TEXT_EXTENSIONS = SOURCE_EXTENSIONS | {
    ".md", ".txt", ".rst", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".conf", ".xml", ".html", ".css", ".scss", ".sql", ".sh", ".ps1", ".bat",
}
MANIFEST_NAMES = {
    "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "pyproject.toml",
    "requirements.txt", "poetry.lock", "pipfile", "pipfile.lock", "go.mod", "go.sum",
    "cargo.toml", "cargo.lock", "pom.xml", "build.gradle", "build.gradle.kts", "gemfile",
    "composer.json", "composer.lock",
}
ENTRYPOINT_NAMES = {"main.py", "app.py", "server.py", "manage.py", "main.go", "program.cs", "index.js", "index.ts"}
DEPLOYMENT_NAMES = {"dockerfile", "docker-compose.yml", "docker-compose.yaml", "makefile", "procfile"}


def _is_sensitive(name: str, suffix: str) -> bool:
    lowered = name.lower()
    return (
        lowered in {".git", ".ssh"}
        or lowered in PRIVATE_KEY_NAMES
        or (lowered.startswith("ssh_host_") and lowered.endswith("_key"))
        or lowered.startswith(".env")
        or lowered.startswith("credentials")
        or lowered.startswith("secrets")
        or suffix.lower() in SENSITIVE_EXTENSIONS
    )


def _category(relative_path: str) -> str:
    path = Path(relative_path)
    name = path.name.lower()
    parts = {part.lower() for part in path.parts[:-1]}
    suffix = path.suffix.lower()
    if name in MANIFEST_NAMES:
        return "manifest"
    if name in DEPLOYMENT_NAMES or ".github" in parts or "deploy" in parts or "deployment" in parts:
        return "deployment_ci"
    if name in ENTRYPOINT_NAMES or name.startswith("main.") or name.startswith("server."):
        return "entrypoint"
    if {"routes", "route", "api", "handlers", "handler", "controllers", "controller"} & parts or "route" in name or "handler" in name:
        return "route_handler"
    if {"services", "service", "usecases", "usecase"} & parts or "service" in name:
        return "service"
    if {"models", "model", "migrations", "migration", "entities", "entity"} & parts or "model" in name or "migration" in name:
        return "model_migration"
    if "tests" in parts or "test" in parts or name.startswith("test_") or name.endswith("_test.py") or name.endswith(".test.js") or name.endswith(".spec.js"):
        return "test"
    if suffix in SOURCE_EXTENSIONS:
        return "source"
    return "other"


def _walk_error(warnings: list[str]):
    def record(error: OSError) -> None:
        warnings.append("Unable to read directory %s: %s" % (error.filename or "<unknown>", error.strerror or error))

    return record


def _path_sort_key(value: str) -> tuple[str, str]:
    return (value.lower(), value)


def _is_link_or_reparse_point(path: Path) -> bool:
    if os.path.islink(path):
        return True
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0) or 0
    except OSError:
        return False
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _is_readme(name: str) -> bool:
    path = Path(name)
    return path.stem.lower() == "readme" and path.suffix.lower() in {".md", ".markdown", ".txt"}


def _validate_project_root(root: Path) -> None:
    absolute_root = Path(os.path.abspath(root))
    for component in (absolute_root, *absolute_root.parents):
        name = component.name
        if not name:
            continue
        if (
            name.lower() in IGNORED_DIRECTORIES
            or _is_sensitive(name, component.suffix)
            or _is_link_or_reparse_point(component)
        ):
            raise ValueError("project root is excluded by the safety policy")


def build_inventory(root: Path, max_files: int = 2000, max_bytes: int = 1_000_000) -> dict[str, Any]:
    """Return metadata for safe-to-report project files without reading their contents."""
    root = Path(root)
    _validate_project_root(root)
    warnings: list[str] = []
    records: list[dict[str, Any]] = []
    total_bytes = 0
    readme_present = False
    limit_reached = False

    def stop_collection(limit_name: str) -> None:
        nonlocal limit_reached
        if not limit_reached:
            warnings.append("Inventory %s limit reached; remaining ordinary files were not included." % limit_name)
            limit_reached = True

    for directory, subdirectories, filenames in os.walk(root, topdown=True, onerror=_walk_error(warnings)):
        subdirectories[:] = sorted(
            (
                child
                for child in subdirectories
                if child.lower() not in IGNORED_DIRECTORIES
                and not _is_sensitive(child, Path(child).suffix)
                and not _is_link_or_reparse_point(Path(directory) / child)
            ),
            key=_path_sort_key,
        )
        for filename in sorted(filenames, key=_path_sort_key):
            file_path = Path(directory) / filename
            if _is_link_or_reparse_point(file_path):
                continue
            suffix = file_path.suffix.lower()
            if _is_sensitive(filename, suffix):
                continue
            if _is_readme(filename):
                readme_present = True
            if limit_reached:
                continue
            if len(records) >= max_files:
                stop_collection("max_files")
                continue
            try:
                size_bytes = file_path.stat().st_size
            except OSError as error:
                warnings.append("Unable to inspect file %s: %s" % (file_path, error.strerror or error))
                continue
            if total_bytes + size_bytes > max_bytes:
                stop_collection("max_bytes")
                continue
            try:
                relative_path = file_path.relative_to(root).as_posix()
            except ValueError:
                warnings.append("Unable to normalize file path %s." % file_path)
                continue
            records.append({
                "path": relative_path,
                "category": _category(relative_path),
                "size_bytes": size_bytes,
                "text_likely": suffix in TEXT_EXTENSIONS or filename.lower() in MANIFEST_NAMES,
            })
            total_bytes += size_bytes
            if total_bytes >= max_bytes:
                stop_collection("max_bytes")
            elif len(records) >= max_files:
                stop_collection("max_files")

    records.sort(key=lambda item: _path_sort_key(item["path"]))
    candidates = [item for item in records if item["category"] != "other"]
    return {
        "root": str(root),
        "readme_present": readme_present,
        "files": records,
        "candidate_files": candidates,
        "warnings": warnings,
    }


def _nonnegative(value: str) -> int:
    integer = int(value)
    if integer < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return integer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely inventory project metadata.")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--max-files", type=_nonnegative, default=2000)
    parser.add_argument("--max-bytes", type=_nonnegative, default=1_000_000)
    parser.add_argument("--json-out", type=Path)
    arguments = parser.parse_args(argv)
    try:
        _validate_project_root(arguments.project_root)
    except ValueError:
        print("project root is excluded by the safety policy.", file=sys.stderr)
        return 2
    if not arguments.project_root.is_dir():
        print("project root must be a readable directory: %s" % arguments.project_root, file=sys.stderr)
        return 2

    inventory = build_inventory(arguments.project_root, arguments.max_files, arguments.max_bytes)
    payload = json.dumps(inventory, ensure_ascii=False, separators=(",", ":"))
    if arguments.json_out:
        try:
            arguments.json_out.write_text(payload, encoding="utf-8")
        except OSError as error:
            print("unable to write JSON output: %s" % error, file=sys.stderr)
            return 2
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
