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
from notecard_extractor.database import Recipe, RecipeState, RecipeImage, DishImage
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


def extract_and_process_image_from_pdf(
    pdf_data: bytes,
) -> list[tuple[int, bytes, str, bytes, str, bytes, str]]:
    """
    Extract images from each page of a PDF, process them (remove white and grey borders),
    and create thumbnail and medium versions.

    Returns:
        List of tuples, each containing (page_num, full_image_bytes, full_image_hash,
        medium_image_bytes, medium_image_hash, thumbnail_bytes, thumbnail_hash).
        Returns empty list if no images found.
    """
    results = []
    try:
        # Read PDF from bytes
        pdf_stream = io.BytesIO(pdf_data)
        reader = PdfReader(pdf_stream)

        # Iterate through pages to extract one image per page
        for page_num, page in enumerate(reader.pages):
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

                    # Create medium version (max 800px on longest side)
                    medium_size = (800, 800)
                    medium_image = image.copy()
                    medium_image.thumbnail(medium_size, Image.Resampling.LANCZOS)
                    medium_bytes = io.BytesIO()
                    medium_image.save(medium_bytes, format="PNG")
                    medium_bytes = medium_bytes.getvalue()
                    medium_hash = hashlib.sha256(medium_bytes).hexdigest()

                    # Create thumbnail version (max 200px on longest side)
                    thumbnail_size = (200, 200)
                    thumbnail_image = image.copy()
                    thumbnail_image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                    thumbnail_bytes = io.BytesIO()
                    thumbnail_image.save(thumbnail_bytes, format="PNG")
                    thumbnail_bytes = thumbnail_bytes.getvalue()
                    thumbnail_hash = hashlib.sha256(thumbnail_bytes).hexdigest()

                    results.append(
                        (
                            page_num,
                            image_bytes,
                            image_hash,
                            medium_bytes,
                            medium_hash,
                            thumbnail_bytes,
                            thumbnail_hash,
                        )
                    )

                    # Only extract the first image from each page
                    break

                except Exception as e:
                    # Continue to next image if this one fails
                    continue

        return results

    except Exception as e:
        # PDF reading or processing failed
        return []


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

                    # Extract and process images from PDF (one per page)
                    image_results = extract_and_process_image_from_pdf(pdf_data)

                    if not image_results:
                        results.append(
                            {
                                "filename": file.filename,
                                "status": "error",
                                "error": "No image found in PDF or failed to extract/process image",
                            }
                        )
                        continue

                    # Create a single recipe entry (without image data)
                    recipe = Recipe(
                        original_pdf_data=pdf_data,
                        original_pdf_sha256=pdf_hash,
                        pdf_filename=file.filename,
                        pdf_upload_timestamp=datetime.utcnow(),
                    )

                    session.add(recipe)
                    session.commit()
                    session.refresh(recipe)

                    # Create RecipeImage entries for each page
                    for (
                        page_num,
                        cropped_image_data,
                        cropped_image_hash,
                        medium_image_data,
                        medium_image_hash,
                        thumbnail_data,
                        thumbnail_hash,
                    ) in image_results:
                        recipe_image = RecipeImage(
                            recipe_id=recipe.id,
                            pdf_page_number=page_num,
                            rotation=0,
                            cropped_image_data=cropped_image_data,
                            cropped_image_sha256=cropped_image_hash,
                            medium_image_data=medium_image_data,
                            medium_image_sha256=medium_image_hash,
                            thumbnail_data=thumbnail_data,
                            thumbnail_sha256=thumbnail_hash,
                        )

                        session.add(recipe_image)

                    session.commit()

                    results.append(
                        {
                            "filename": file.filename,
                            "status": "success",
                            "message": f"PDF with {len(image_results)} page(s) stored successfully",
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

                # Get rotation from page 1 image (pdf_page_number = 0)
                recipe_image = (
                    session.query(RecipeImage)
                    .filter(RecipeImage.recipe_id == recipe.id)
                    .filter(RecipeImage.pdf_page_number == 0)
                    .first()
                )
                rotation = recipe_image.rotation if recipe_image else 0

                results.append(
                    {
                        "id": recipe.id,
                        "count": idx,
                        "upload_timestamp": upload_time,
                        "pdf_filename": recipe.pdf_filename or "Unknown",
                        "pdf_size": pdf_size,
                        "rotation": rotation,
                        "state": recipe.state.value if recipe.state else "not_started",
                    }
                )

            return jsonify({"recipes": results, "total": len(results)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flask_app.route("/api/recipe/<int:recipe_id>", methods=["GET"])
def get_recipe(recipe_id: int):
    """
    Get full details for a specific recipe.
    """
    if db_engine is None:
        return jsonify({"error": "Database not initialized"}), 500

    try:
        with Session(db_engine) as session:
            recipe = session.get(Recipe, recipe_id)

            if not recipe:
                return jsonify({"error": "Recipe not found"}), 404

            # Get all RecipeImage entries for this recipe
            recipe_images = (
                session.query(RecipeImage)
                .filter(RecipeImage.recipe_id == recipe_id)
                .order_by(RecipeImage.pdf_page_number)
                .all()
            )

            # Get page 1 image (pdf_page_number = 0) for main image data
            recipe_image_page1 = (
                session.query(RecipeImage)
                .filter(RecipeImage.recipe_id == recipe_id)
                .filter(RecipeImage.pdf_page_number == 0)
                .first()
            )

            # Get all DishImage entries for this recipe
            dish_images = (
                session.query(DishImage)
                .filter(DishImage.recipe_id == recipe_id)
                .order_by(DishImage.image_number)
                .all()
            )

            # Build list of all pages
            pages = []
            for img in recipe_images:
                pages.append(
                    {
                        "pdf_page_number": img.pdf_page_number,
                        "rotation": img.rotation,
                        "cropped_image_sha256": img.cropped_image_sha256,
                        "cropped_image_size": len(img.cropped_image_data)
                        if img.cropped_image_data
                        else 0,
                        "medium_image_sha256": img.medium_image_sha256,
                        "medium_image_size": len(img.medium_image_data)
                        if img.medium_image_data
                        else 0,
                        "thumbnail_sha256": img.thumbnail_sha256,
                        "thumbnail_size": len(img.thumbnail_data)
                        if img.thumbnail_data
                        else 0,
                    }
                )

            # Build list of all dish images
            dish_images_list = []
            for img in dish_images:
                dish_images_list.append(
                    {
                        "image_number": img.image_number,
                        "rotation": img.rotation,
                        "image_sha256": img.image_sha256,
                        "image_size": len(img.image_data) if img.image_data else 0,
                        "medium_image_sha256": img.medium_image_sha256,
                        "medium_image_size": len(img.medium_image_data)
                        if img.medium_image_data
                        else 0,
                        "thumbnail_sha256": img.thumbnail_sha256,
                        "thumbnail_size": len(img.thumbnail_data)
                        if img.thumbnail_data
                        else 0,
                    }
                )

            # Build response with all fields
            result = {
                "id": recipe.id,
                "pdf_filename": recipe.pdf_filename,
                "pdf_upload_timestamp": (
                    recipe.pdf_upload_timestamp.isoformat()
                    if recipe.pdf_upload_timestamp
                    else None
                ),
                "original_pdf_sha256": recipe.original_pdf_sha256,
                "original_pdf_size": len(recipe.original_pdf_data)
                if recipe.original_pdf_data
                else 0,
                "cropped_image_sha256": recipe_image_page1.cropped_image_sha256
                if recipe_image_page1
                else None,
                "cropped_image_size": len(recipe_image_page1.cropped_image_data)
                if recipe_image_page1 and recipe_image_page1.cropped_image_data
                else 0,
                "medium_image_sha256": recipe_image_page1.medium_image_sha256
                if recipe_image_page1
                else None,
                "medium_image_size": len(recipe_image_page1.medium_image_data)
                if recipe_image_page1 and recipe_image_page1.medium_image_data
                else 0,
                "thumbnail_sha256": recipe_image_page1.thumbnail_sha256
                if recipe_image_page1
                else None,
                "thumbnail_size": len(recipe_image_page1.thumbnail_data)
                if recipe_image_page1 and recipe_image_page1.thumbnail_data
                else 0,
                "rotation": recipe_image_page1.rotation if recipe_image_page1 else 0,
                "state": recipe.state.value if recipe.state else "not_started",
                "title": recipe.title,
                "description": recipe.description,
                "year": recipe.year,
                "author": recipe.author,
                "ingredients": recipe.ingredients,
                "recipe": recipe.recipe,
                "cook_time": recipe.cook_time,
                "notes": recipe.notes,
                "pages": pages,
                "total_pages": len(pages),
                "dish_images": dish_images_list,
                "total_dish_images": len(dish_images_list),
            }

            return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flask_app.route("/api/recipe/<int:recipe_id>/image", methods=["GET"])
def get_recipe_image(recipe_id: int):
    """
    Get the processed image for a specific recipe (page 1).
    Returns the cropped image data as PNG.
    """
    if db_engine is None:
        return jsonify({"error": "Database not initialized"}), 500

    try:
        with Session(db_engine) as session:
            recipe = session.get(Recipe, recipe_id)

            if not recipe:
                return jsonify({"error": "Recipe not found"}), 404

            # Get page 1 image (pdf_page_number = 0)
            recipe_image = (
                session.query(RecipeImage)
                .filter(RecipeImage.recipe_id == recipe_id)
                .filter(RecipeImage.pdf_page_number == 0)
                .first()
            )

            if not recipe_image or not recipe_image.cropped_image_data:
                return jsonify(
                    {"error": "No processed image available for page 1"}
                ), 404

            # Return image as PNG
            return Response(
                recipe_image.cropped_image_data,
                mimetype="image/png",
                headers={
                    "Content-Disposition": f"inline; filename=recipe_{recipe_id}.png"
                },
            )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flask_app.route("/api/recipe/<int:recipe_id>/thumbnail", methods=["GET"])
def get_recipe_thumbnail(recipe_id: int):
    """
    Get the thumbnail image for a specific recipe (page 1).
    Returns the thumbnail data as PNG.
    """
    if db_engine is None:
        return jsonify({"error": "Database not initialized"}), 500

    try:
        with Session(db_engine) as session:
            recipe = session.get(Recipe, recipe_id)

            if not recipe:
                return jsonify({"error": "Recipe not found"}), 404

            # Get page 1 image (pdf_page_number = 0)
            recipe_image = (
                session.query(RecipeImage)
                .filter(RecipeImage.recipe_id == recipe_id)
                .filter(RecipeImage.pdf_page_number == 0)
                .first()
            )

            if not recipe_image or not recipe_image.thumbnail_data:
                return jsonify({"error": "No thumbnail available for page 1"}), 404

            # Return thumbnail as PNG
            return Response(
                recipe_image.thumbnail_data,
                mimetype="image/png",
                headers={
                    "Content-Disposition": f"inline; filename=recipe_{recipe_id}_thumb.png"
                },
            )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flask_app.route("/api/recipe/<int:recipe_id>/medium", methods=["GET"])
def get_recipe_medium(recipe_id: int):
    """
    Get the medium-sized image for a specific recipe (page 1).
    Returns the medium image data as PNG.
    """
    if db_engine is None:
        return jsonify({"error": "Database not initialized"}), 500

    try:
        with Session(db_engine) as session:
            recipe = session.get(Recipe, recipe_id)

            if not recipe:
                return jsonify({"error": "Recipe not found"}), 404

            # Get page 1 image (pdf_page_number = 0)
            recipe_image = (
                session.query(RecipeImage)
                .filter(RecipeImage.recipe_id == recipe_id)
                .filter(RecipeImage.pdf_page_number == 0)
                .first()
            )

            if not recipe_image or not recipe_image.medium_image_data:
                return jsonify({"error": "No medium image available for page 1"}), 404

            # Return medium image as PNG
            return Response(
                recipe_image.medium_image_data,
                mimetype="image/png",
                headers={
                    "Content-Disposition": f"inline; filename=recipe_{recipe_id}_medium.png"
                },
            )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flask_app.route(
    "/api/recipe/<int:recipe_id>/page/<int:page_number>/thumbnail", methods=["GET"]
)
def get_recipe_page_thumbnail(recipe_id: int, page_number: int):
    """
    Get the thumbnail image for a specific recipe page.
    Returns the thumbnail data as PNG.
    """
    if db_engine is None:
        return jsonify({"error": "Database not initialized"}), 500

    try:
        with Session(db_engine) as session:
            recipe = session.get(Recipe, recipe_id)

            if not recipe:
                return jsonify({"error": "Recipe not found"}), 404

            # Get the specific page image (page_number is 0-indexed in URL, but stored as 0-indexed)
            recipe_image = (
                session.query(RecipeImage)
                .filter(RecipeImage.recipe_id == recipe_id)
                .filter(RecipeImage.pdf_page_number == page_number)
                .first()
            )

            if not recipe_image or not recipe_image.thumbnail_data:
                return jsonify(
                    {"error": f"No thumbnail available for page {page_number + 1}"}
                ), 404

            # Return thumbnail as PNG
            return Response(
                recipe_image.thumbnail_data,
                mimetype="image/png",
                headers={
                    "Content-Disposition": f"inline; filename=recipe_{recipe_id}_page{page_number}_thumb.png"
                },
            )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flask_app.route(
    "/api/recipe/<int:recipe_id>/page/<int:page_number>/image", methods=["GET"]
)
def get_recipe_page_image(recipe_id: int, page_number: int):
    """
    Get the full cropped image for a specific recipe page.
    Returns the cropped image data as PNG.
    """
    if db_engine is None:
        return jsonify({"error": "Database not initialized"}), 500

    try:
        with Session(db_engine) as session:
            recipe = session.get(Recipe, recipe_id)

            if not recipe:
                return jsonify({"error": "Recipe not found"}), 404

            # Get the specific page image (page_number is 0-indexed)
            recipe_image = (
                session.query(RecipeImage)
                .filter(RecipeImage.recipe_id == recipe_id)
                .filter(RecipeImage.pdf_page_number == page_number)
                .first()
            )

            if not recipe_image or not recipe_image.cropped_image_data:
                return jsonify(
                    {"error": f"No image available for page {page_number + 1}"}
                ), 404

            # Return image as PNG
            return Response(
                recipe_image.cropped_image_data,
                mimetype="image/png",
                headers={
                    "Content-Disposition": f"inline; filename=recipe_{recipe_id}_page{page_number}.png"
                },
            )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flask_app.route(
    "/api/recipe/<int:recipe_id>/dish/<int:image_number>/thumbnail", methods=["GET"]
)
def get_dish_image_thumbnail(recipe_id: int, image_number: int):
    """
    Get the thumbnail image for a specific dish image.
    Returns the thumbnail data as PNG.
    """
    if db_engine is None:
        return jsonify({"error": "Database not initialized"}), 500

    try:
        with Session(db_engine) as session:
            recipe = session.get(Recipe, recipe_id)

            if not recipe:
                return jsonify({"error": "Recipe not found"}), 404

            # Get the specific dish image
            dish_image = (
                session.query(DishImage)
                .filter(DishImage.recipe_id == recipe_id)
                .filter(DishImage.image_number == image_number)
                .first()
            )

            if not dish_image or not dish_image.thumbnail_data:
                return jsonify(
                    {"error": f"No thumbnail available for dish image {image_number}"}
                ), 404

            # Return thumbnail as PNG
            return Response(
                dish_image.thumbnail_data,
                mimetype="image/png",
                headers={
                    "Content-Disposition": f"inline; filename=recipe_{recipe_id}_dish{image_number}_thumb.png"
                },
            )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flask_app.route(
    "/api/recipe/<int:recipe_id>/dish/<int:image_number>/image", methods=["GET"]
)
def get_dish_image(recipe_id: int, image_number: int):
    """
    Get the full image for a specific dish image.
    Returns the image data as PNG.
    """
    if db_engine is None:
        return jsonify({"error": "Database not initialized"}), 500

    try:
        with Session(db_engine) as session:
            recipe = session.get(Recipe, recipe_id)

            if not recipe:
                return jsonify({"error": "Recipe not found"}), 404

            # Get the specific dish image
            dish_image = (
                session.query(DishImage)
                .filter(DishImage.recipe_id == recipe_id)
                .filter(DishImage.image_number == image_number)
                .first()
            )

            if not dish_image or not dish_image.image_data:
                return jsonify(
                    {"error": f"No image available for dish image {image_number}"}
                ), 404

            # Return image as PNG
            return Response(
                dish_image.image_data,
                mimetype="image/png",
                headers={
                    "Content-Disposition": f"inline; filename=recipe_{recipe_id}_dish{image_number}.png"
                },
            )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flask_app.route("/api/recipe/<int:recipe_id>/rotation", methods=["POST"])
def update_recipe_rotation(recipe_id: int):
    """
    Update the rotation value for a specific recipe image.
    Expects JSON: {"rotation": 0|90|180|270, "image_type": "recipe"|"page"|"dish", "page_number": int (optional), "dish_number": int (optional)}
    """
    if db_engine is None:
        return jsonify({"error": "Database not initialized"}), 500

    try:
        data = request.get_json()
        if not data or "rotation" not in data:
            return jsonify({"error": "Missing rotation in request"}), 400

        rotation = int(data["rotation"])
        if rotation not in [0, 90, 180, 270]:
            return jsonify({"error": "Rotation must be 0, 90, 180, or 270"}), 400

        image_type = data.get(
            "image_type", "recipe"
        )  # Default to 'recipe' for backward compatibility
        page_number = data.get("page_number")
        dish_number = data.get("dish_number")

        with Session(db_engine) as session:
            recipe = session.get(Recipe, recipe_id)

            if not recipe:
                return jsonify({"error": "Recipe not found"}), 404

            if image_type == "page" and page_number is not None:
                # Update specific page image
                recipe_image = (
                    session.query(RecipeImage)
                    .filter(RecipeImage.recipe_id == recipe_id)
                    .filter(RecipeImage.pdf_page_number == page_number)
                    .first()
                )
                if not recipe_image:
                    return jsonify(
                        {"error": f"No image found for page {page_number + 1}"}
                    ), 404
                recipe_image.rotation = rotation
                session.add(recipe_image)
            elif image_type == "dish" and dish_number is not None:
                # Update specific dish image
                dish_image = (
                    session.query(DishImage)
                    .filter(DishImage.recipe_id == recipe_id)
                    .filter(DishImage.image_number == dish_number)
                    .first()
                )
                if not dish_image:
                    return jsonify(
                        {"error": f"No image found for dish image {dish_number}"}
                    ), 404
                dish_image.rotation = rotation
                session.add(dish_image)
            else:
                # Default to page 1 image (backward compatibility)
                recipe_image = (
                    session.query(RecipeImage)
                    .filter(RecipeImage.recipe_id == recipe_id)
                    .filter(RecipeImage.pdf_page_number == 0)
                    .first()
                )
                if not recipe_image:
                    return jsonify({"error": "No image found for page 1"}), 404
                recipe_image.rotation = rotation
                session.add(recipe_image)

            session.commit()
            return jsonify({"success": True, "rotation": rotation})

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
