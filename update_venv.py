#!/usr/bin/env python3
"""
Script to update the virtual environment and dependencies.
Uses uv to sync dependencies from pyproject.toml.
"""

import subprocess
import sys
from pathlib import Path


def check_uv_installed():
    """Check if uv is installed."""
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def update_venv():
    """Update the virtual environment and install/update dependencies."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.resolve()

    # Check if uv is installed
    if not check_uv_installed():
        print("Error: uv is not installed. Please install it first:")
        print("  curl -LsSf https://astral.sh/uv/install.sh | sh")
        print(
            '  Or on Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"'
        )
        sys.exit(1)

    # Change to script directory
    import os

    os.chdir(script_dir)

    # Sync dependencies (creates venv if needed and updates dependencies)
    print("Updating virtual environment and dependencies...")
    try:
        subprocess.run(["uv", "sync"], check=True)
        print("Virtual environment updated successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error updating environment: {e}")
        sys.exit(1)


if __name__ == "__main__":
    update_venv()
