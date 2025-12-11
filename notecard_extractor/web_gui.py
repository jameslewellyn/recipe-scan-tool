#!/usr/bin/env python3
"""
Web GUI for the notecard extractor tool.
Provides a browser-based interface for uploading PDF files and storing them in the database.
"""

from flask import Flask, render_template, jsonify, request
from pathlib import Path
from typing import Annotated, Optional
import typer
import hashlib
from datetime import datetime
from sqlmodel import SQLModel, create_engine, Session
from notecard_extractor.database import Recipe, RecipeState

# Get the directory where this module is located
BASE_DIR = Path(__file__).parent

flask_app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))
app = typer.Typer()

# Global database engine (will be initialized in run_server)
db_engine = None


@flask_app.route("/")
def index():
    """Serve the main HTML page."""
    return render_template("index.html")


@flask_app.route("/api/upload-pdfs", methods=["POST"])
def upload_pdfs():
    """
    Receive PDF files from client and store them in the database.
    Expects multipart/form-data with 'files' field containing PDF files.
    """
    if db_engine is None:
        return jsonify({"error": "Database not initialized"}), 500

    try:
        if "files" not in request.files:
            return jsonify({"error": "No files provided"}), 400

        files = request.files.getlist("files")
        if not files or all(f.filename == "" for f in files):
            return jsonify({"error": "No files selected"}), 400

        results = []
        with Session(db_engine) as session:
            for file in files:
                if file.filename == "":
                    continue

                # Check if file is a PDF
                if not file.filename.lower().endswith(".pdf"):
                    results.append(
                        {
                            "filename": file.filename,
                            "status": "skipped",
                            "error": "Not a PDF file",
                        }
                    )
                    continue

                try:
                    # Read PDF data
                    pdf_data = file.read()
                    file.seek(0)  # Reset file pointer

                    # Calculate SHA256 hash
                    pdf_hash = hashlib.sha256(pdf_data).hexdigest()

                    # Check if PDF with this hash already exists
                    existing = (
                        session.query(Recipe)
                        .filter(Recipe.original_pdf_sha256 == pdf_hash)
                        .first()
                    )

                    if existing:
                        results.append(
                            {
                                "filename": file.filename,
                                "status": "duplicate",
                                "message": f"PDF already exists (ID: {existing.id})",
                                "recipe_id": existing.id,
                            }
                        )
                        continue

                    # Create new recipe entry
                    recipe = Recipe(
                        original_pdf_data=pdf_data,
                        original_pdf_sha256=pdf_hash,
                        pdf_filename=file.filename,
                        pdf_upload_timestamp=datetime.utcnow(),
                    )

                    session.add(recipe)
                    session.commit()
                    session.refresh(recipe)

                    results.append(
                        {
                            "filename": file.filename,
                            "status": "success",
                            "message": "PDF stored successfully",
                            "recipe_id": recipe.id,
                        }
                    )

                except Exception as e:
                    session.rollback()
                    results.append(
                        {
                            "filename": file.filename,
                            "status": "error",
                            "error": str(e),
                        }
                    )

        return jsonify({"results": results, "total": len(results)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Get path to user's home directory
HOME_DIR = Path.home()

# Get path to database file in user's home directory
DEFAULT_DATABASE_PATH = HOME_DIR / "notecard_extractor.db"


@app.command()
def run_server(
    host: Annotated[
        str | None, typer.Argument(help="Host to bind the server to")
    ] = "127.0.0.1",
    port: Annotated[int, typer.Argument(help="Port to bind the server to")] = 5000,
    debug: Annotated[
        bool, typer.Option("--debug", "-d", help="Enable debug mode")
    ] = False,
    database: Annotated[
        Path | None,
        typer.Option("--database", "-db", help="Path to SQLite database file"),
    ] = DEFAULT_DATABASE_PATH,
):
    """Run the Flask development server."""
    global db_engine

    # Initialize database if path provided
    # Create parent directory if it doesn't exist
    database.parent.mkdir(parents=True, exist_ok=True)

    # Create database URL
    db_url = f"sqlite:///{database}"
    db_engine = create_engine(db_url, echo=debug)

    # Create all tables (Recipe model is imported above, so it's registered)
    SQLModel.metadata.create_all(db_engine)

    typer.echo(f"Database initialized at: {database}")

    typer.echo(f"Starting web server at http://{host}:{port}")
    typer.echo("Press Ctrl+C to stop the server")
    flask_app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    app()
