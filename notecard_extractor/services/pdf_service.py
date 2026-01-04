#!/usr/bin/env python3
"""
PDF processing service.
Handles PDF extraction and image processing pipeline.
"""

import hashlib
from typing import List, Tuple
from notecard_extractor.utils.pdf_utils import read_pdf_from_bytes, extract_images_from_pdf_page
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


def process_pdf_images(
    pdf_data: bytes,
) -> List[Tuple[int, bytes, str, bytes, str, bytes, str]]:
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
        reader = read_pdf_from_bytes(pdf_data)

        # Iterate through pages to extract one image per page
        for page_num, page in enumerate(reader.pages):
            image = extract_images_from_pdf_page(page, page_num)
            
            if image is None:
                continue

            try:
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

            except Exception:
                # Continue to next image if this one fails
                continue

        return results

    except Exception:
        # PDF reading or processing failed
        return []
