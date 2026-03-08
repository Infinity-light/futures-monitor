#!/usr/bin/env python3
"""Lightweight validation script for the single-service Futures Monitor stack."""

from __future__ import annotations

import importlib
import py_compile
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

KEY_FILES = [
    PROJECT_ROOT / "futures_monitor" / "main.py",
    PROJECT_ROOT / "futures_monitor" / "server" / "__main__.py",
    PROJECT_ROOT / "futures_monitor" / "server" / "app.py",
    PROJECT_ROOT / "futures_monitor" / "server" / "schemas.py",
    PROJECT_ROOT / "futures_monitor" / "server" / "api" / "config_api.py",
    PROJECT_ROOT / "futures_monitor" / "server" / "api" / "monitor_api.py",
    PROJECT_ROOT / "futures_monitor" / "server" / "services" / "monitor_service.py",
    PROJECT_ROOT / "futures_monitor" / "server" / "static_host.py",
    PROJECT_ROOT / "futures_monitor" / "Dockerfile",
    PROJECT_ROOT / "docker-compose.yml",
    PROJECT_ROOT / ".github" / "workflows" / "deploy.yml",
    PROJECT_ROOT / "tests" / "integration" / "test_app_bootstrap.py",
    PROJECT_ROOT / "tests" / "integration" / "test_single_service_routes.py",
    PROJECT_ROOT / "tests" / "unit" / "test_server_schemas.py",
    PROJECT_ROOT / "tests" / "unit" / "test_server_app_routes.py",
    PROJECT_ROOT / ".claude" / "validate.py",
]

PYTHON_DIRS = [
    PROJECT_ROOT / "futures_monitor",
    PROJECT_ROOT / "tests",
    PROJECT_ROOT / ".claude",
]

PYTHON_EXCLUDE_PARTS = {
    ".venv",
    "venv",
    "site-packages",
    "node_modules",
    "__pycache__",
}

OPTIONAL_IMPORTS = [
    "futures_monitor.server",
    "futures_monitor.server.__main__",
    "futures_monitor.server.app",
    "futures_monitor.server.schemas",
    "futures_monitor.server.api.monitor_api",
    "futures_monitor.server.api.config_api",
]


def _print_header(title: str) -> None:
    print(f"\n=== {title} ===")


def check_key_files_exist() -> int:
    _print_header("Check key files existence")
    missing = []
    for path in KEY_FILES:
        if path.exists():
            print(f"[OK] {path}")
        else:
            print(f"[FAIL] Missing: {path}")
            missing.append(path)
    return 0 if not missing else 1


def _is_excluded_python_path(file_path: Path) -> bool:
    return any(part in PYTHON_EXCLUDE_PARTS for part in file_path.parts)


def iter_python_files() -> list[Path]:
    files: list[Path] = []
    for directory in PYTHON_DIRS:
        if not directory.exists():
            continue
        for file_path in sorted(directory.rglob("*.py")):
            if _is_excluded_python_path(file_path):
                continue
            files.append(file_path)
    return files


def check_py_compile() -> int:
    _print_header("Compile all python files")
    failed = []
    files = iter_python_files()
    if not files:
        print("[FAIL] No Python files found in configured directories.")
        return 1

    for file_path in files:
        try:
            py_compile.compile(str(file_path), doraise=True)
            print(f"[OK] {file_path}")
        except py_compile.PyCompileError as exc:
            print(f"[FAIL] {file_path}: {exc}")
            failed.append(file_path)
        except Exception as exc:
            print(f"[FAIL] {file_path}: {exc}")
            failed.append(file_path)

    return 0 if not failed else 1


def check_optional_imports() -> int:
    _print_header("Optional server module imports")
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    failed = []
    for module_name in OPTIONAL_IMPORTS:
        try:
            importlib.import_module(module_name)
            print(f"[OK] import {module_name}")
        except Exception as exc:
            print(f"[FAIL] import {module_name}: {exc}")
            failed.append(module_name)
    return 0 if not failed else 1


def check_optional_web_build() -> int:
    _print_header("Optional web build")
    web_dir = PROJECT_ROOT / "futures_monitor" / "web"
    package_json = web_dir / "package.json"
    if not package_json.exists():
        print(f"[SKIP] package.json not found: {package_json}")
        return 0

    command = ["npm", "--prefix", str(web_dir), "run", "build"]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        print("[WARN] npm not found, skipping optional web build check.")
        return 0
    except Exception as exc:
        print(f"[WARN] optional web build check failed to execute: {exc}")
        return 1

    if completed.returncode == 0:
        print("[OK] npm web build passed")
        return 0

    print(f"[FAIL] npm web build failed with exit code {completed.returncode}")
    if completed.stdout:
        print("--- stdout ---")
        print(completed.stdout)
    if completed.stderr:
        print("--- stderr ---")
        print(completed.stderr)
    return 1


def main() -> int:
    print(f"Project root: {PROJECT_ROOT}")

    checks = [
        ("key_files", check_key_files_exist),
        ("py_compile", check_py_compile),
        ("optional_imports", check_optional_imports),
        ("optional_web_build", check_optional_web_build),
    ]

    failed_count = 0
    for _, check_func in checks:
        failed_count += check_func()

    _print_header("Summary")
    if failed_count == 0:
        print("Validation PASSED")
        return 0

    print(f"Validation FAILED ({failed_count} check group(s) failed)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
