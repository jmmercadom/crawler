#!/usr/bin/env python3
"""
Run all project quality checks: tests, linting, formatting, and type checking.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional


def run_command(cmd: str, description: str, cwd: Optional[Path] = None) -> bool:
    """Run a command and return True if successful, False otherwise."""
    print(f"\n🔍 {description}...")
    print(f"Running: {cmd}")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd or Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"❌ {description} failed:")
            if result.stdout:
                print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            return False

        print(f"✅ {description} passed")
        return True
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False


def main() -> None:
    """Run all quality checks."""
    print("🚀 Running all project quality checks...")

    # Get the project root directory
    project_root = Path(__file__).parent.parent

    checks = [
        ("uv run pytest --cov", "Running tests with coverage"),
        ("uv run ruff check .", "Running linting"),
        ("uv run ruff format --check .", "Checking formatting"),
        ("uv run mypy .", "Running type checking"),
    ]

    all_passed = True
    for cmd, desc in checks:
        if not run_command(cmd, desc, cwd=project_root):
            all_passed = False
            # Continue running other checks to show all issues

    if all_passed:
        print("\n🎉 All checks passed! ✨")
        sys.exit(0)
    else:
        print("\n💥 Some checks failed! Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
