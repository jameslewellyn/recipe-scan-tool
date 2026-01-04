#!/usr/bin/env python3
"""
Recipe API handlers.
Handles recipe-related API endpoints.
"""

import hashlib
from datetime import datetime
from flask import request
from notecard_extractor.utils.db_utils import get_db_session, get_db_engine
from notecard_extractor.utils.cache_utils import get_cache_headers, check_cache_etag
from notecard_extractor.services.pdf_service import process_pdf_images
from notecard_extractor.services.recipe_service import (
    get_recipe_list,
    get_recipe_details,
    update_recipe_fields,
)
from notecard_extractor.database import Recipe, RecipeImage, RecipeState
from notecard_extractor.api.responses import (
    success_response,
    error_response,
    not_found_response,
    bad_request_response,
    database_not_initialized_response,
)
from flask import Response, jsonify


def handle_upload_pdfs():
    """Handle PDF upload endpoint."""
    db_engine = get_db_engine()
    if db_engine is None:
        return database_not_initialized_response()

    try:
        if "files" not in request.files:
            return bad_request_response("No files provided")

        files = request.files.getlist("files")
        if not files or all(f.filename == "" for f in files):
            return bad_request_response("No files selected")

        results = []
        with get_db_session() as session:
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
                    image_results = process_pdf_images(pdf_data)

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
                            unneeded=False,
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
        return error_response(str(e))


def handle_get_recipes():
    """Handle get recipes list endpoint."""
    db_engine = get_db_engine()
    if db_engine is None:
        return database_not_initialized_response()

    try:
        with get_db_session() as session:
            results = get_recipe_list(session)
            return jsonify({"recipes": results, "total": len(results)})

    except Exception as e:
        return error_response(str(e))


def handle_get_recipe(recipe_id: int):
    """Handle get single recipe endpoint."""
    db_engine = get_db_engine()
    if db_engine is None:
        return database_not_initialized_response()

    try:
        with get_db_session() as session:
            result = get_recipe_details(session, recipe_id)
            if not result:
                return not_found_response("Recipe")
            return jsonify(result)

    except Exception as e:
        return error_response(str(e))


def handle_update_recipe(recipe_id: int):
    """Handle update recipe endpoint."""
    db_engine = get_db_engine()
    if db_engine is None:
        return database_not_initialized_response()

    try:
        data = request.get_json()
        if not data:
            return bad_request_response("No data provided")

        with get_db_session() as session:
            try:
                if "state" in data:
                    # Validate state
                    RecipeState(data["state"])
            except ValueError:
                return bad_request_response(f"Invalid state: {data['state']}")

            success = update_recipe_fields(session, recipe_id, data)
            if not success:
                return not_found_response("Recipe")

            session.commit()
            return success_response(message="Recipe updated successfully")

    except Exception as e:
        return error_response(str(e))


def handle_update_recipe_rotation(recipe_id: int):
    """Handle update recipe rotation endpoint."""
    db_engine = get_db_engine()
    if db_engine is None:
        return database_not_initialized_response()

    try:
        data = request.get_json()
        if not data or "rotation" not in data:
            return bad_request_response("Missing rotation in request")

        rotation = int(data["rotation"])
        if rotation not in [0, 90, 180, 270]:
            return bad_request_response("Rotation must be 0, 90, 180, or 270")

        image_type = data.get("image_type", "recipe")
        page_number = data.get("page_number")
        dish_number = data.get("dish_number")

        with get_db_session() as session:
            from notecard_extractor.database import DishImage
            
            recipe = session.get(Recipe, recipe_id)
            if not recipe:
                return not_found_response("Recipe")

            if image_type == "page" and page_number is not None:
                recipe_image = (
                    session.query(RecipeImage)
                    .filter(RecipeImage.recipe_id == recipe_id)
                    .filter(RecipeImage.pdf_page_number == page_number)
                    .first()
                )
                if not recipe_image:
                    return not_found_response(f"Image for page {page_number + 1}")
                recipe_image.rotation = rotation
                session.add(recipe_image)
            elif image_type == "dish" and dish_number is not None:
                dish_image = (
                    session.query(DishImage)
                    .filter(DishImage.recipe_id == recipe_id)
                    .filter(DishImage.image_number == dish_number)
                    .first()
                )
                if not dish_image:
                    return not_found_response(f"Dish image {dish_number}")
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
                    return not_found_response("Image for page 1")
                recipe_image.rotation = rotation
                session.add(recipe_image)

            session.commit()
            return success_response(data={"rotation": rotation})

    except Exception as e:
        return error_response(str(e))


def handle_update_recipe_image_unneeded(recipe_id: int, page_number: int):
    """Handle update recipe image unneeded flag endpoint."""
    db_engine = get_db_engine()
    if db_engine is None:
        return database_not_initialized_response()

    try:
        data = request.get_json()
        if not data or "unneeded" not in data:
            return bad_request_response("Missing unneeded in request")

        unneeded = bool(data["unneeded"])

        with get_db_session() as session:
            recipe = session.get(Recipe, recipe_id)
            if not recipe:
                return not_found_response("Recipe")

            recipe_image = (
                session.query(RecipeImage)
                .filter(RecipeImage.recipe_id == recipe_id)
                .filter(RecipeImage.pdf_page_number == page_number)
                .first()
            )
            
            if not recipe_image:
                return not_found_response(f"Image for page {page_number + 1}")
            
            recipe_image.unneeded = unneeded
            session.add(recipe_image)
            session.commit()
            
            return success_response(data={"unneeded": unneeded})

    except Exception as e:
        return error_response(str(e))
