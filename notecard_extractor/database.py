#!/usr/bin/env python3
"""
Database models for the recipe scan tool.
Uses SQLModel to define the database schema.
"""

from enum import Enum
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import LargeBinary, DateTime
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
    Stores recipe data including original PDF, cropped images, and metadata.
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

    # Cropped image data
    cropped_image_data: Optional[bytes] = Field(
        default=None, sa_column=Column(LargeBinary)
    )
    cropped_image_sha256: Optional[str] = Field(default=None, index=True, max_length=64)

    # Rotation (0, 90, 180, or 270 degrees)
    rotation: int = Field(default=0, ge=0, le=270)

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

    # Dish pictures (4 fields)
    dish_picture_1: Optional[bytes] = Field(default=None, sa_column=Column(LargeBinary))
    dish_picture_2: Optional[bytes] = Field(default=None, sa_column=Column(LargeBinary))
    dish_picture_3: Optional[bytes] = Field(default=None, sa_column=Column(LargeBinary))
    dish_picture_4: Optional[bytes] = Field(default=None, sa_column=Column(LargeBinary))
