#!/usr/bin/env python3
"""
Web GUI for the notecard extractor tool.
Provides a browser-based interface for selecting folders and viewing files.
"""

from flask import Flask, render_template, jsonify, request
from pathlib import Path
from typing import Annotated, Optional
import typer

# Get the directory where this module is located
BASE_DIR = Path(__file__).parent

flask_app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))
app = typer.Typer()


@flask_app.route("/")
def index():
    """Serve the main HTML page."""
    return render_template("index.html")


@flask_app.route("/api/files", methods=["POST"])
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


@app.command()
def run_server(
    host: Annotated[
        str, typer.Option("--host", "-h", help="Host to bind the server to")
    ] = "127.0.0.1",
    port: Annotated[
        int, typer.Option("--port", "-p", help="Port to bind the server to")
    ] = 5000,
    debug: Annotated[
        bool, typer.Option("--debug", "-d", help="Enable debug mode")
    ] = False,
    database: Annotated[
        Optional[Path],
        typer.Option("--database", "-db", help="Path to SQLite database file"),
    ] = None,
):
    """Run the Flask development server."""
    typer.echo(f"Starting web server at http://{host}:{port}")
    typer.echo("Press Ctrl+C to stop the server")
    flask_app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    app()
