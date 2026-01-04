#!/usr/bin/env python3
"""
Tag API handlers.
Handles tag-related API endpoints.
"""

from flask import request, jsonify
from notecard_extractor.utils.db_utils import get_db_session, get_db_engine
from notecard_extractor.services.recipe_service import (
    get_recipe_tags,
    add_tag_to_recipe,
    remove_tag_from_recipe,
    get_all_tags_with_counts,
)
from notecard_extractor.api.responses import (
    success_response,
    error_response,
    not_found_response,
    bad_request_response,
    database_not_initialized_response,
)


def handle_add_recipe_tag(recipe_id: int):
    """Handle add tag to recipe endpoint."""
    db_engine = get_db_engine()
    if db_engine is None:
        return database_not_initialized_response()

    try:
        data = request.get_json()
        if not data or "tag_name" not in data:
            return bad_request_response("tag_name is required")

        tag_name = data["tag_name"].strip()
        if not tag_name:
            return bad_request_response("tag_name cannot be empty")

        with get_db_session() as session:
            result = add_tag_to_recipe(session, recipe_id, tag_name)
            if result is None:
                # Check if recipe exists
                from notecard_extractor.database import Recipe
                recipe = session.get(Recipe, recipe_id)
                if not recipe:
                    return not_found_response("Recipe")
                # Tag already assigned
                return bad_request_response("Tag already assigned to this recipe")

            session.commit()
            return success_response(data={"tag": result})

    except Exception as e:
        return error_response(str(e))


def handle_remove_recipe_tag(recipe_id: int, recipe_tag_id: int):
    """Handle remove tag from recipe endpoint."""
    db_engine = get_db_engine()
    if db_engine is None:
        return database_not_initialized_response()

    try:
        with get_db_session() as session:
            success = remove_tag_from_recipe(session, recipe_id, recipe_tag_id)
            if not success:
                return not_found_response("Tag for this recipe")

            session.commit()
            return success_response()

    except Exception as e:
        return error_response(str(e))


def handle_get_tags_with_counts():
    """Handle get all tags with counts endpoint."""
    db_engine = get_db_engine()
    if db_engine is None:
        return database_not_initialized_response()

    try:
        with get_db_session() as session:
            tags = get_all_tags_with_counts(session)
            return jsonify({"tags": tags})

    except Exception as e:
        return error_response(str(e))
