#!/usr/bin/env python3
"""
Flask route definitions.
Registers all API routes with their handlers.
"""

from flask import Flask, render_template
from notecard_extractor.api.handlers import recipes, images, tags


def register_routes(app: Flask):
    """
    Register all API routes with the Flask app.
    
    Args:
        app: Flask application instance
    """
    # Main page
    @app.route("/")
    def index():
        """Serve the main HTML page."""
        return render_template("index.html")

    # Recipe routes
    @app.route("/api/upload-pdfs", methods=["POST"])
    def upload_pdfs():
        return recipes.handle_upload_pdfs()

    @app.route("/api/recipes", methods=["GET"])
    def get_recipes():
        return recipes.handle_get_recipes()

    @app.route("/api/recipe/<int:recipe_id>", methods=["GET"])
    def get_recipe(recipe_id: int):
        return recipes.handle_get_recipe(recipe_id)

    @app.route("/api/recipe/<int:recipe_id>", methods=["PUT"])
    def update_recipe(recipe_id: int):
        return recipes.handle_update_recipe(recipe_id)

    @app.route("/api/recipe/<int:recipe_id>/rotation", methods=["POST"])
    def update_recipe_rotation(recipe_id: int):
        return recipes.handle_update_recipe_rotation(recipe_id)

    @app.route("/api/recipe/<int:recipe_id>/page/<int:page_number>/unneeded", methods=["POST"])
    def update_recipe_image_unneeded(recipe_id: int, page_number: int):
        return recipes.handle_update_recipe_image_unneeded(recipe_id, page_number)

    # Image routes
    @app.route("/api/recipe/<int:recipe_id>/image", methods=["GET"])
    def get_recipe_image(recipe_id: int):
        return images.handle_get_recipe_image(recipe_id)

    @app.route("/api/recipe/<int:recipe_id>/thumbnail", methods=["GET"])
    def get_recipe_thumbnail(recipe_id: int):
        return images.handle_get_recipe_thumbnail(recipe_id)

    @app.route("/api/recipe/<int:recipe_id>/medium", methods=["GET"])
    def get_recipe_medium(recipe_id: int):
        return images.handle_get_recipe_medium(recipe_id)

    @app.route("/api/recipe/<int:recipe_id>/page/<int:page_number>/thumbnail", methods=["GET"])
    def get_recipe_page_thumbnail(recipe_id: int, page_number: int):
        return images.handle_get_recipe_page_thumbnail(recipe_id, page_number)

    @app.route("/api/recipe/<int:recipe_id>/page/<int:page_number>/image", methods=["GET"])
    def get_recipe_page_image(recipe_id: int, page_number: int):
        return images.handle_get_recipe_page_image(recipe_id, page_number)

    @app.route("/api/recipe/<int:recipe_id>/dish/<int:image_number>/thumbnail", methods=["GET"])
    def get_dish_image_thumbnail(recipe_id: int, image_number: int):
        return images.handle_get_dish_image_thumbnail(recipe_id, image_number)

    @app.route("/api/recipe/<int:recipe_id>/dish/<int:image_number>/image", methods=["GET"])
    def get_dish_image(recipe_id: int, image_number: int):
        return images.handle_get_dish_image(recipe_id, image_number)

    # Tag routes
    @app.route("/api/recipe/<int:recipe_id>/tags", methods=["POST"])
    def add_recipe_tag(recipe_id: int):
        return tags.handle_add_recipe_tag(recipe_id)

    @app.route("/api/recipe/<int:recipe_id>/tags/<int:recipe_tag_id>", methods=["DELETE"])
    def remove_recipe_tag(recipe_id: int, recipe_tag_id: int):
        return tags.handle_remove_recipe_tag(recipe_id, recipe_tag_id)

    @app.route("/api/tags", methods=["GET"])
    def get_tags_with_counts():
        return tags.handle_get_tags_with_counts()
