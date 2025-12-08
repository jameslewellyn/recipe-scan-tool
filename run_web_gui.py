#!/usr/bin/env python3
"""
Script to run web-gui with automatic venv setup and dependency installation.
This script ensures the virtual environment exists and dependencies are installed before running.
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


def setup_and_run():
    """Set up venv, install dependencies, and run web-gui."""
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

    # Sync dependencies (creates venv if needed and installs dependencies)
    print("Setting up virtual environment and installing dependencies...")
    try:
        subprocess.run(["uv", "sync"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error setting up environment: {e}")
        sys.exit(1)

    # Run the web-gui command with all passed arguments
    print("Starting web server...")
    print("Open your browser to http://127.0.0.1:5000")
    print("Press Ctrl+C to stop the server")
    try:
        # Pass all command-line arguments to web-gui
        subprocess.run(["uv", "run", "web-gui"] + sys.argv[1:], check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\nServer stopped.")
        sys.exit(0)


if __name__ == "__main__":
    setup_and_run()
