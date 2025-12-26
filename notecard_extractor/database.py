#!/usr/bin/env python3
"""
Database models for the recipe scan tool.
Uses SQLModel to define the database schema.
"""

from enum import Enum
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import LargeBinary, DateTime, UniqueConstraint
from typing import Optional
from datetime import datetime


class RecipeState(str, Enum):
    """Enumeration of possible recipe states."""

    NOT_STARTED = "not_started"
    PARTIALLY_COMPLETE = "partially_complete"
    COMPLETE = "complete"
    BROKEN = "broken"
    DUPLICATE = "duplicate"


class RotationAngle(int, Enum):
    """Enumeration of rotation angles in degrees."""

    ZERO = 0
    NINETY = 90
    ONE_EIGHTY = 180
    TWO_SEVENTY = 270


class Recipe(SQLModel, table=True):
    """
    Recipe table model.
    Stores recipe data including original PDF and metadata.
    Images are stored in the RecipeImage table.
    """

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Original PDF data
    original_pdf_data: Optional[bytes] = Field(
        default=None, sa_column=Column(LargeBinary)
    )
    original_pdf_sha256: Optional[str] = Field(default=None, index=True, max_length=64)
    pdf_filename: Optional[str] = Field(default=None, max_length=500)
    pdf_upload_timestamp: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime)
    )

    # Recipe state
    state: RecipeState = Field(default=RecipeState.NOT_STARTED)

    # Recipe metadata
    title: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None)
    year: Optional[int] = Field(default=None)
    author: Optional[str] = Field(default=None, max_length=200)

    # Recipe content
    ingredients: Optional[str] = Field(default=None)
    recipe: Optional[str] = Field(default=None)  # Instructions/steps
    cook_time: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None)


class RecipeImage(SQLModel, table=True):
    """
    RecipeImage table model.
    Stores images extracted from PDF pages, associated with a Recipe.
    Each page of a PDF gets one RecipeImage entry.
    """

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign key to Recipe
    recipe_id: int = Field(foreign_key="recipe.id", index=True)

    # PDF page number (0-indexed, where 0 is the first page)
    pdf_page_number: int = Field(default=0, ge=0)

    # Rotation (0, 90, 180, or 270 degrees)
    rotation: int = Field(default=0, ge=0, le=270)

    # Cropped image data
    cropped_image_data: Optional[bytes] = Field(
        default=None, sa_column=Column(LargeBinary)
    )
    cropped_image_sha256: Optional[str] = Field(default=None, index=True, max_length=64)

    # Medium and thumbnail versions
    medium_image_data: Optional[bytes] = Field(
        default=None, sa_column=Column(LargeBinary)
    )
    medium_image_sha256: Optional[str] = Field(default=None, index=True, max_length=64)
    thumbnail_data: Optional[bytes] = Field(default=None, sa_column=Column(LargeBinary))
    thumbnail_sha256: Optional[str] = Field(default=None, index=True, max_length=64)


class DishImage(SQLModel, table=True):
    """
    DishImage table model.
    Stores dish images associated with a Recipe.
    Each recipe can have multiple dish images.
    """

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign key to Recipe
    recipe_id: int = Field(foreign_key="recipe.id", index=True)

    # Image number/position (1-indexed, for ordering)
    image_number: int = Field(default=1, ge=1)

    # Rotation (0, 90, 180, or 270 degrees)
    rotation: int = Field(default=0, ge=0, le=270)

    # Full image data
    image_data: Optional[bytes] = Field(default=None, sa_column=Column(LargeBinary))
    image_sha256: Optional[str] = Field(default=None, index=True, max_length=64)

    # Medium and thumbnail versions
    medium_image_data: Optional[bytes] = Field(
        default=None, sa_column=Column(LargeBinary)
    )
    medium_image_sha256: Optional[str] = Field(default=None, index=True, max_length=64)
    thumbnail_data: Optional[bytes] = Field(default=None, sa_column=Column(LargeBinary))
    thumbnail_sha256: Optional[str] = Field(default=None, index=True, max_length=64)


class RecipeTagList(SQLModel, table=True):
    """
    RecipeTagList table model.
    Stores the list of available tags that can be assigned to recipes.
    """

    __table_args__ = (UniqueConstraint("tag_name"),)

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Tag name (must be unique)
    tag_name: str = Field(index=True, max_length=100, unique=True)


class RecipeTag(SQLModel, table=True):
    """
    RecipeTag table model.
    Junction table linking recipes to tags (many-to-many relationship).
    Each recipe can have many tags, and each tag can be assigned to many recipes.
    """

    __table_args__ = (UniqueConstraint("recipe_id", "tag_id"),)

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign key to Recipe
    recipe_id: int = Field(foreign_key="recipe.id", index=True)

    # Foreign key to RecipeTagList
    tag_id: int = Field(foreign_key="recipetaglist.id", index=True)
