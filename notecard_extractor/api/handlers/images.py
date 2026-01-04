#!/usr/bin/env python3
"""
Image API handlers.
Handles image retrieval endpoints.
"""

from flask import request, Response
from notecard_extractor.utils.db_utils import get_db_session, get_db_engine
from notecard_extractor.utils.cache_utils import get_cache_headers, check_cache_etag
from notecard_extractor.database import Recipe, RecipeImage, DishImage
from notecard_extractor.api.responses import (
    not_found_response,
    database_not_initialized_response,
)


def handle_get_recipe_image(recipe_id: int):
    """Handle get recipe image (page 1) endpoint."""
    db_engine = get_db_engine()
    if db_engine is None:
        return database_not_initialized_response()

    try:
        with get_db_session() as session:
            recipe = session.get(Recipe, recipe_id)
            if not recipe:
                return not_found_response("Recipe")

            recipe_image = (
                session.query(RecipeImage)
                .filter(RecipeImage.recipe_id == recipe_id)
                .filter(RecipeImage.pdf_page_number == 0)
                .first()
            )

            if not recipe_image or not recipe_image.cropped_image_data:
                return not_found_response("Processed image for page 1")

            # Check cache with ETag
            request_etag = request.headers.get("If-None-Match")
            image_hash = recipe_image.cropped_image_sha256
            if check_cache_etag(request_etag, image_hash):
                return Response(status=304)  # Not Modified

            headers = get_cache_headers(image_hash)
            headers["Content-Disposition"] = f"inline; filename=recipe_{recipe_id}.png"

            return Response(
                recipe_image.cropped_image_data,
                mimetype="image/png",
                headers=headers,
            )

    except Exception as e:
        from notecard_extractor.api.responses import error_response
        return error_response(str(e))


def handle_get_recipe_thumbnail(recipe_id: int):
    """Handle get recipe thumbnail (page 1) endpoint."""
    db_engine = get_db_engine()
    if db_engine is None:
        return database_not_initialized_response()

    try:
        with get_db_session() as session:
            recipe = session.get(Recipe, recipe_id)
            if not recipe:
                return not_found_response("Recipe")

            recipe_image = (
                session.query(RecipeImage)
                .filter(RecipeImage.recipe_id == recipe_id)
                .filter(RecipeImage.pdf_page_number == 0)
                .first()
            )

            if not recipe_image or not recipe_image.thumbnail_data:
                return not_found_response("Thumbnail for page 1")

            request_etag = request.headers.get("If-None-Match")
            image_hash = recipe_image.thumbnail_sha256
            if check_cache_etag(request_etag, image_hash):
                return Response(status=304)

            headers = get_cache_headers(image_hash)
            headers["Content-Disposition"] = f"inline; filename=recipe_{recipe_id}_thumb.png"

            return Response(
                recipe_image.thumbnail_data,
                mimetype="image/png",
                headers=headers,
            )

    except Exception as e:
        from notecard_extractor.api.responses import error_response
        return error_response(str(e))


def handle_get_recipe_medium(recipe_id: int):
    """Handle get recipe medium image (page 1) endpoint."""
    db_engine = get_db_engine()
    if db_engine is None:
        return database_not_initialized_response()

    try:
        with get_db_session() as session:
            recipe = session.get(Recipe, recipe_id)
            if not recipe:
                return not_found_response("Recipe")

            recipe_image = (
                session.query(RecipeImage)
                .filter(RecipeImage.recipe_id == recipe_id)
                .filter(RecipeImage.pdf_page_number == 0)
                .first()
            )

            if not recipe_image or not recipe_image.medium_image_data:
                return not_found_response("Medium image for page 1")

            request_etag = request.headers.get("If-None-Match")
            image_hash = recipe_image.medium_image_sha256
            if check_cache_etag(request_etag, image_hash):
                return Response(status=304)

            headers = get_cache_headers(image_hash)
            headers["Content-Disposition"] = f"inline; filename=recipe_{recipe_id}_medium.png"

            return Response(
                recipe_image.medium_image_data,
                mimetype="image/png",
                headers=headers,
            )

    except Exception as e:
        from notecard_extractor.api.responses import error_response
        return error_response(str(e))


def handle_get_recipe_page_thumbnail(recipe_id: int, page_number: int):
    """Handle get recipe page thumbnail endpoint."""
    db_engine = get_db_engine()
    if db_engine is None:
        return database_not_initialized_response()

    try:
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

            if not recipe_image or not recipe_image.thumbnail_data:
                return not_found_response(f"Thumbnail for page {page_number + 1}")

            request_etag = request.headers.get("If-None-Match")
            image_hash = recipe_image.thumbnail_sha256
            if check_cache_etag(request_etag, image_hash):
                return Response(status=304)

            headers = get_cache_headers(image_hash)
            headers["Content-Disposition"] = f"inline; filename=recipe_{recipe_id}_page{page_number}_thumb.png"

            return Response(
                recipe_image.thumbnail_data,
                mimetype="image/png",
                headers=headers,
            )

    except Exception as e:
        from notecard_extractor.api.responses import error_response
        return error_response(str(e))


def handle_get_recipe_page_image(recipe_id: int, page_number: int):
    """Handle get recipe page image endpoint."""
    db_engine = get_db_engine()
    if db_engine is None:
        return database_not_initialized_response()

    try:
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

            if not recipe_image or not recipe_image.cropped_image_data:
                return not_found_response(f"Image for page {page_number + 1}")

            request_etag = request.headers.get("If-None-Match")
            image_hash = recipe_image.cropped_image_sha256
            if check_cache_etag(request_etag, image_hash):
                return Response(status=304)

            headers = get_cache_headers(image_hash)
            headers["Content-Disposition"] = f"inline; filename=recipe_{recipe_id}_page{page_number}.png"

            return Response(
                recipe_image.cropped_image_data,
                mimetype="image/png",
                headers=headers,
            )

    except Exception as e:
        from notecard_extractor.api.responses import error_response
        return error_response(str(e))


def handle_get_dish_image_thumbnail(recipe_id: int, image_number: int):
    """Handle get dish image thumbnail endpoint."""
    db_engine = get_db_engine()
    if db_engine is None:
        return database_not_initialized_response()

    try:
        with get_db_session() as session:
            recipe = session.get(Recipe, recipe_id)
            if not recipe:
                return not_found_response("Recipe")

            dish_image = (
                session.query(DishImage)
                .filter(DishImage.recipe_id == recipe_id)
                .filter(DishImage.image_number == image_number)
                .first()
            )

            if not dish_image or not dish_image.thumbnail_data:
                return not_found_response(f"Thumbnail for dish image {image_number}")

            request_etag = request.headers.get("If-None-Match")
            image_hash = dish_image.thumbnail_sha256
            if check_cache_etag(request_etag, image_hash):
                return Response(status=304)

            headers = get_cache_headers(image_hash)
            headers["Content-Disposition"] = f"inline; filename=recipe_{recipe_id}_dish{image_number}_thumb.png"

            return Response(
                dish_image.thumbnail_data,
                mimetype="image/png",
                headers=headers,
            )

    except Exception as e:
        from notecard_extractor.api.responses import error_response
        return error_response(str(e))


def handle_get_dish_image(recipe_id: int, image_number: int):
    """Handle get dish image endpoint."""
    db_engine = get_db_engine()
    if db_engine is None:
        return database_not_initialized_response()

    try:
        with get_db_session() as session:
            recipe = session.get(Recipe, recipe_id)
            if not recipe:
                return not_found_response("Recipe")

            dish_image = (
                session.query(DishImage)
                .filter(DishImage.recipe_id == recipe_id)
                .filter(DishImage.image_number == image_number)
                .first()
            )

            if not dish_image or not dish_image.image_data:
                return not_found_response(f"Image for dish image {image_number}")

            request_etag = request.headers.get("If-None-Match")
            image_hash = dish_image.image_sha256
            if check_cache_etag(request_etag, image_hash):
                return Response(status=304)

            headers = get_cache_headers(image_hash)
            headers["Content-Disposition"] = f"inline; filename=recipe_{recipe_id}_dish{image_number}.png"

            return Response(
                dish_image.image_data,
                mimetype="image/png",
                headers=headers,
            )

    except Exception as e:
        from notecard_extractor.api.responses import error_response
        return error_response(str(e))
