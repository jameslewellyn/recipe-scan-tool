#!/usr/bin/env python3
"""
Image utility functions.
Handles image resizing, hashing, format conversion, and byte conversion.
"""

import hashlib
import io
from PIL import Image
from typing import Tuple


def calculate_image_hash(image_bytes: bytes) -> str:
    """
    Calculate SHA256 hash of image bytes.
    
    Args:
        image_bytes: Image data as bytes
        
    Returns:
        SHA256 hash as hex string
    """
    return hashlib.sha256(image_bytes).hexdigest()


def create_thumbnail(image: Image.Image, max_size: Tuple[int, int] = (200, 200)) -> Tuple[bytes, str]:
    """
    Create a thumbnail version of an image.
    
    Args:
        image: PIL Image to create thumbnail from
        max_size: Maximum size tuple (width, height) for thumbnail
        
    Returns:
        Tuple of (thumbnail_bytes, thumbnail_hash)
    """
    thumbnail_image = image.copy()
    thumbnail_image.thumbnail(max_size, Image.Resampling.LANCZOS)
    thumbnail_bytes = image_to_bytes(thumbnail_image)
    thumbnail_hash = calculate_image_hash(thumbnail_bytes)
    return thumbnail_bytes, thumbnail_hash


def create_medium_image(image: Image.Image, max_size: Tuple[int, int] = (800, 800)) -> Tuple[bytes, str]:
    """
    Create a medium-sized version of an image.
    
    Args:
        image: PIL Image to create medium version from
        max_size: Maximum size tuple (width, height) for medium image
        
    Returns:
        Tuple of (medium_bytes, medium_hash)
    """
    medium_image = image.copy()
    medium_image.thumbnail(max_size, Image.Resampling.LANCZOS)
    medium_bytes = image_to_bytes(medium_image)
    medium_hash = calculate_image_hash(medium_bytes)
    return medium_bytes, medium_hash


def convert_image_to_rgb(image: Image.Image) -> Image.Image:
    """
    Convert image to RGB format, handling transparency.
    
    Args:
        image: PIL Image to convert
        
    Returns:
        RGB PIL Image
    """
    if image.mode in ("RGBA", "LA", "P"):
        # Create white background for transparent images
        rgb_img = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        rgb_img.paste(
            image,
            mask=image.split()[-1] if image.mode == "RGBA" else None,
        )
        return rgb_img
    elif image.mode != "RGB":
        return image.convert("RGB")
    return image


def image_to_bytes(image: Image.Image, format: str = "PNG") -> bytes:
    """
    Convert PIL Image to bytes.
    
    Args:
        image: PIL Image to convert
        format: Image format (default: "PNG")
        
    Returns:
        Image data as bytes
    """
    image_bytes = io.BytesIO()
    image.save(image_bytes, format=format)
    return image_bytes.getvalue()
