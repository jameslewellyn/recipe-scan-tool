#!/usr/bin/env python3
"""
Recipe service.
Handles recipe business logic and database operations.
"""

from typing import List, Dict, Optional, Any
from sqlalchemy import func
from sqlmodel import Session
from notecard_extractor.database import (
    Recipe,
    RecipeState,
    RecipeImage,
    DishImage,
    RecipeTagList,
    RecipeTag,
)


def get_recipe_list(session: Session) -> List[Dict[str, Any]]:
    """
    Get a list of all recipes from the database.
    Returns recipes ordered by upload timestamp (newest first).
    
    Args:
        session: Database session
        
    Returns:
        List of recipe dictionaries
    """
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

        # Get tags for this recipe
        tags_list = get_recipe_tags(session, recipe.id)

        results.append(
            {
                "id": recipe.id,
                "count": idx,
                "upload_timestamp": upload_time,
                "pdf_filename": recipe.pdf_filename or "Unknown",
                "title": recipe.title,
                "pdf_size": pdf_size,
                "rotation": rotation,
                "state": recipe.state.value if recipe.state else "not_started",
                "tags": tags_list,
            }
        )

    return results


def get_recipe_details(session: Session, recipe_id: int) -> Optional[Dict[str, Any]]:
    """
    Get full details for a specific recipe.
    
    Args:
        session: Database session
        recipe_id: Recipe ID
        
    Returns:
        Recipe dictionary or None if not found
    """
    recipe = session.get(Recipe, recipe_id)

    if not recipe:
        return None

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

    # Get tags for this recipe
    tags_list = get_recipe_tags(session, recipe_id)

    # Build list of all pages
    pages = []
    for img in recipe_images:
        pages.append(
            {
                "pdf_page_number": img.pdf_page_number,
                "rotation": img.rotation,
                "unneeded": img.unneeded,
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
        "tags": tags_list,
    }

    return result


def update_recipe_fields(session: Session, recipe_id: int, data: Dict[str, Any]) -> bool:
    """
    Update recipe fields.
    
    Args:
        session: Database session
        recipe_id: Recipe ID
        data: Dictionary with fields to update
        
    Returns:
        True if recipe was found and updated, False otherwise
    """
    recipe = session.get(Recipe, recipe_id)

    if not recipe:
        return False

    # Update fields if provided
    if "title" in data:
        recipe.title = data["title"] if data["title"] else None
    if "description" in data:
        recipe.description = (
            data["description"] if data["description"] else None
        )
    if "year" in data:
        recipe.year = int(data["year"]) if data["year"] else None
    if "author" in data:
        recipe.author = data["author"] if data["author"] else None
    if "ingredients" in data:
        recipe.ingredients = (
            data["ingredients"] if data["ingredients"] else None
        )
    if "recipe" in data:
        recipe.recipe = data["recipe"] if data["recipe"] else None
    if "cook_time" in data:
        recipe.cook_time = data["cook_time"] if data["cook_time"] else None
    if "notes" in data:
        recipe.notes = data["notes"] if data["notes"] else None
    if "state" in data:
        recipe.state = RecipeState(data["state"])

    session.add(recipe)
    return True


def get_recipe_tags(session: Session, recipe_id: int) -> List[Dict[str, Any]]:
    """
    Get all tags for a recipe.
    
    Args:
        session: Database session
        recipe_id: Recipe ID
        
    Returns:
        List of tag dictionaries
    """
    recipe_tags = (
        session.query(RecipeTag, RecipeTagList)
        .join(RecipeTagList, RecipeTag.tag_id == RecipeTagList.id)
        .filter(RecipeTag.recipe_id == recipe_id)
        .all()
    )
    
    tags_list = []
    for recipe_tag, tag_list in recipe_tags:
        tags_list.append({
            "id": tag_list.id,
            "tag_name": tag_list.tag_name,
            "recipe_tag_id": recipe_tag.id
        })
    
    return tags_list


def add_tag_to_recipe(session: Session, recipe_id: int, tag_name: str) -> Optional[Dict[str, Any]]:
    """
    Add a tag to a recipe.
    Creates the tag in RecipeTagList if it doesn't exist, then links it to the recipe.
    
    Args:
        session: Database session
        recipe_id: Recipe ID
        tag_name: Tag name to add
        
    Returns:
        Tag dictionary if successful, None if recipe not found or tag already exists
    """
    # Check if recipe exists
    recipe = session.get(Recipe, recipe_id)
    if not recipe:
        return None

    # Find or create the tag in RecipeTagList
    tag_list = (
        session.query(RecipeTagList)
        .filter(RecipeTagList.tag_name == tag_name)
        .first()
    )

    if not tag_list:
        # Create new tag
        tag_list = RecipeTagList(tag_name=tag_name)
        session.add(tag_list)
        session.flush()  # Get the ID without committing

    # Check if tag is already assigned to this recipe
    existing_recipe_tag = (
        session.query(RecipeTag)
        .filter(RecipeTag.recipe_id == recipe_id)
        .filter(RecipeTag.tag_id == tag_list.id)
        .first()
    )

    if existing_recipe_tag:
        return None  # Tag already assigned

    # Create the link
    recipe_tag = RecipeTag(recipe_id=recipe_id, tag_id=tag_list.id)
    session.add(recipe_tag)
    session.flush()

    return {
        "id": tag_list.id,
        "tag_name": tag_list.tag_name,
        "recipe_tag_id": recipe_tag.id
    }


def remove_tag_from_recipe(session: Session, recipe_id: int, recipe_tag_id: int) -> bool:
    """
    Remove a tag from a recipe.
    
    Args:
        session: Database session
        recipe_id: Recipe ID
        recipe_tag_id: RecipeTag ID to remove
        
    Returns:
        True if tag was found and removed, False otherwise
    """
    # Find the recipe tag link
    recipe_tag = (
        session.query(RecipeTag)
        .filter(RecipeTag.id == recipe_tag_id)
        .filter(RecipeTag.recipe_id == recipe_id)
        .first()
    )

    if not recipe_tag:
        return False

    session.delete(recipe_tag)
    return True


def get_all_tags_with_counts(session: Session) -> List[Dict[str, Any]]:
    """
    Get all tags with their recipe counts.
    Only returns tags that have at least one associated recipe.
    
    Args:
        session: Database session
        
    Returns:
        List of tag dictionaries with counts
    """
    tags_with_counts = (
        session.query(
            RecipeTagList.id,
            RecipeTagList.tag_name,
            func.count(RecipeTag.recipe_id).label('recipe_count')
        )
        .join(RecipeTag, RecipeTagList.id == RecipeTag.tag_id)
        .group_by(RecipeTagList.id, RecipeTagList.tag_name)
        .having(func.count(RecipeTag.recipe_id) > 0)
        .order_by(RecipeTagList.tag_name)
        .all()
    )
    
    return [
        {
            "id": tag.id,
            "tag_name": tag.tag_name,
            "recipe_count": tag.recipe_count
        }
        for tag in tags_with_counts
    ]
