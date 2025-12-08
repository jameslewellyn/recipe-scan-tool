#!/usr/bin/env python3
"""
Web GUI for the notecard extractor tool.
Provides a browser-based interface for selecting folders and viewing files.
"""

from flask import Flask, render_template, jsonify, request
from pathlib import Path
import os

# Get the directory where this module is located
BASE_DIR = Path(__file__).parent

app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))


@app.route("/")
def index():
    """Serve the main HTML page."""
    return render_template("index.html")


@app.route("/api/files", methods=["POST"])
def get_files():
    """
    Receive folder path from client and return list of files.
    Expects JSON: {"folder_path": "/path/to/folder"}
    """
    try:
        data = request.get_json()
        if not data or "folder_path" not in data:
            return jsonify({"error": "Missing folder_path in request"}), 400

        folder_path = Path(data["folder_path"])

        # Validate that the path exists and is a directory
        if not folder_path.exists():
            return jsonify({"error": f"Path does not exist: {folder_path}"}), 400

        if not folder_path.is_dir():
            return jsonify({"error": f"Path is not a directory: {folder_path}"}), 400

        # Get list of files in the directory
        files = []
        try:
            for item in sorted(folder_path.iterdir()):
                if item.is_file():
                    files.append(
                        {
                            "name": item.name,
                            "path": str(item),
                            "size": item.stat().st_size,
                            "extension": item.suffix.lower(),
                        }
                    )
        except PermissionError:
            return jsonify({"error": f"Permission denied: {folder_path}"}), 403

        return jsonify({"files": files, "folder": str(folder_path)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def run_server(host="127.0.0.1", port=5000, debug=False):
    """Run the Flask development server."""
    print(f"Starting web server at http://{host}:{port}")
    print("Press Ctrl+C to stop the server")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    import sys

    # Parse command line arguments
    host = "127.0.0.1"
    port = 5000
    debug = False

    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    if len(sys.argv) > 3 and sys.argv[3].lower() == "debug":
        debug = True

    run_server(host=host, port=port, debug=debug)

