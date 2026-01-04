#!/usr/bin/env python3
"""
Image processing service.
Handles image processing operations.
"""

from PIL import Image
from notecard_extractor.utils.image_utils import (
    convert_image_to_rgb,
    image_to_bytes,
    create_thumbnail,
    create_medium_image,
    calculate_image_hash,
)
from notecard_extractor.image_processing import autocrop_white_border, autocrop_grey_border
from notecard_extractor.config import (
    THUMBNAIL_MAX_SIZE,
    MEDIUM_IMAGE_MAX_SIZE,
    WHITE_BORDER_THRESHOLD,
    GREY_BORDER_TOLERANCE,
)


def process_image_pipeline(image: Image.Image) -> tuple[bytes, str, bytes, str, bytes, str]:
    """
    Process an image through the full pipeline:
    1. Convert to RGB
    2. Remove white borders
    3. Remove grey borders (left and right)
    4. Create thumbnail and medium versions
    
    Args:
        image: PIL Image to process
        
    Returns:
        Tuple of (full_image_bytes, full_image_hash, medium_bytes, medium_hash,
                  thumbnail_bytes, thumbnail_hash)
    """
    # Convert to RGB if needed
    image = convert_image_to_rgb(image)

    # Remove white border
    image = autocrop_white_border(image, threshold=WHITE_BORDER_THRESHOLD)

    # Remove grey borders (left and right)
    image = autocrop_grey_border(
        image, border_color=None, tolerance=GREY_BORDER_TOLERANCE, sides="left"
    )
    image = autocrop_grey_border(
        image, border_color=None, tolerance=GREY_BORDER_TOLERANCE, sides="right"
    )

    # Convert processed image to bytes (PNG format)
    image_bytes = image_to_bytes(image)
    image_hash = calculate_image_hash(image_bytes)

    # Create medium and thumbnail versions
    medium_bytes, medium_hash = create_medium_image(image, MEDIUM_IMAGE_MAX_SIZE)
    thumbnail_bytes, thumbnail_hash = create_thumbnail(image, THUMBNAIL_MAX_SIZE)

    return image_bytes, image_hash, medium_bytes, medium_hash, thumbnail_bytes, thumbnail_hash
