#!/usr/bin/env python3
"""
Web GUI for the notecard extractor tool.
Provides a browser-based interface for uploading PDF files and storing them in the database.
"""

from flask import Flask, render_template, jsonify, request, Response
from pathlib import Path
from typing import Annotated, Optional
import typer
import hashlib
import io
from datetime import datetime
from pypdf import PdfReader
from PIL import Image
from sqlmodel import SQLModel, create_engine, Session
from notecard_extractor.database import Recipe, RecipeState
from notecard_extractor.image_processing import (
    autocrop_white_border,
    autocrop_grey_border,
)

# Get the directory where this module is located
BASE_DIR = Path(__file__).parent

flask_app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))
app = typer.Typer()

# Global database engine (will be initialized in run_server)
db_engine = None


def extract_and_process_image_from_pdf(pdf_data: bytes) -> tuple[bytes, str] | None:
    """
    Extract the first image from a PDF, process it (remove white and grey borders),
    and return the processed image data and its SHA256 hash.

    Returns:
        Tuple of (image_bytes, sha256_hash) or None if no image found
    """
    try:
        # Read PDF from bytes
        pdf_stream = io.BytesIO(pdf_data)
        reader = PdfReader(pdf_stream)

        # Iterate through pages to find the first image
        for page in reader.pages:
            for image_file_object in page.images:
                try:
                    # Get image data
                    image_data = image_file_object.data

                    # Open image with PIL
                    image = Image.open(io.BytesIO(image_data))

                    # Convert to RGB if needed
                    if image.mode in ("RGBA", "LA", "P"):
                        # Create white background for transparent images
                        rgb_img = Image.new("RGB", image.size, (255, 255, 255))
                        if image.mode == "P":
                            image = image.convert("RGBA")
                        rgb_img.paste(
                            image,
                            mask=image.split()[-1] if image.mode == "RGBA" else None,
                        )
                        image = rgb_img
                    elif image.mode != "RGB":
                        image = image.convert("RGB")

                    # Remove white border
                    image = autocrop_white_border(image, threshold=250)

                    # Remove grey border
                    image = autocrop_grey_border(image, border_color=None, tolerance=60)

                    # Convert processed image to bytes (PNG format)
                    image_bytes = io.BytesIO()
                    image.save(image_bytes, format="PNG")
                    image_bytes = image_bytes.getvalue()

                    # Calculate SHA256 hash of processed image
                    image_hash = hashlib.sha256(image_bytes).hexdigest()

                    return (image_bytes, image_hash)

                except Exception as e:
                    # Continue to next image if this one fails
                    continue

        # No image found
        return None

    except Exception as e:
        # PDF reading or processing failed
        return None


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

                    # Extract and process image from PDF
                    image_result = extract_and_process_image_from_pdf(pdf_data)

                    if image_result is None:
                        results.append(
                            {
                                "filename": file.filename,
                                "status": "error",
                                "error": "No image found in PDF or failed to extract/process image",
                            }
                        )
                        continue

                    cropped_image_data, cropped_image_hash = image_result

                    # Create new recipe entry
                    recipe = Recipe(
                        original_pdf_data=pdf_data,
                        original_pdf_sha256=pdf_hash,
                        pdf_filename=file.filename,
                        pdf_upload_timestamp=datetime.utcnow(),
                        cropped_image_data=cropped_image_data,
                        cropped_image_sha256=cropped_image_hash,
                    )

                    session.add(recipe)
                    session.commit()
                    session.refresh(recipe)

                    results.append(
                        {
                            "filename": file.filename,
                            "status": "success",
                            "message": "PDF and processed image stored successfully",
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


@flask_app.route("/api/recipes", methods=["GET"])
def get_recipes():
    """
    Get a list of all recipes from the database.
    Returns recipes ordered by upload timestamp (newest first).
    """
    if db_engine is None:
        return jsonify({"error": "Database not initialized"}), 500

    try:
        with Session(db_engine) as session:
            recipes = (
                session.query(Recipe).order_by(Recipe.pdf_upload_timestamp.desc()).all()
            )

            results = []
            for idx, recipe in enumerate(recipes, start=1):
                pdf_size = (
                    len(recipe.original_pdf_data) if recipe.original_pdf_data else 0
                )
                upload_time = (
                    recipe.pdf_upload_timestamp.isoformat()
                    if recipe.pdf_upload_timestamp
                    else None
                )

                results.append(
                    {
                        "id": recipe.id,
                        "count": idx,
                        "upload_timestamp": upload_time,
                        "pdf_filename": recipe.pdf_filename or "Unknown",
                        "pdf_size": pdf_size,
                    }
                )

            return jsonify({"recipes": results, "total": len(results)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flask_app.route("/api/recipe/<int:recipe_id>/image", methods=["GET"])
def get_recipe_image(recipe_id: int):
    """
    Get the processed image for a specific recipe.
    Returns the cropped image data as PNG.
    """
    if db_engine is None:
        return jsonify({"error": "Database not initialized"}), 500

    try:
        with Session(db_engine) as session:
            recipe = session.get(Recipe, recipe_id)

            if not recipe:
                return jsonify({"error": "Recipe not found"}), 404

            if not recipe.cropped_image_data:
                return jsonify({"error": "No processed image available"}), 404

            # Return image as PNG
            return Response(
                recipe.cropped_image_data,
                mimetype="image/png",
                headers={
                    "Content-Disposition": f"inline; filename=recipe_{recipe_id}.png"
                },
            )

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
