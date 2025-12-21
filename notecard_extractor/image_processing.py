#!/usr/bin/env python3
"""
Image processing functions.
Functions for cropping and processing images.
"""

from PIL import Image
import statistics


def autocrop_white_border(image: Image.Image, threshold: int = 250) -> Image.Image:
    """
    Remove white borders from an image by finding the bounding box of non-white content.

    Args:
        image: PIL Image to crop
        threshold: Pixel value threshold for considering a pixel as white (0-255)

    Returns:
        Cropped PIL Image
    """
    # Convert to grayscale if needed
    if image.mode != "L":
        gray = image.convert("L")
    else:
        gray = image

    # Get image data
    pixels = gray.load()
    width, height = gray.size

    # Find bounding box of non-white content
    top = height
    bottom = 0
    left = width
    right = 0

    # Scan for non-white pixels
    for y in range(height):
        for x in range(width):
            pixel_value = pixels[x, y]
            if pixel_value < threshold:  # Non-white pixel found
                top = min(top, y)
                bottom = max(bottom, y)
                left = min(left, x)
                right = max(right, x)

    # If no content found, return original image
    if top == height or left == width:
        return image

    # Add small padding to avoid cutting too close
    padding = 2
    top = max(0, top - padding)
    bottom = min(height, bottom + padding + 1)
    left = max(0, left - padding)
    right = min(width, right + padding + 1)

    # Crop the image
    return image.crop((left, top, right, bottom))


def autocrop_grey_border(
    image: Image.Image,
    border_color: tuple = None,
    tolerance: int = 60,
    sides: str = "left",
) -> Image.Image:
    """
    Remove greyish margins from specified side of an image.
    Samples edge pixels to determine margin color, then scans inward until finding
    non-margin content. Removes only the specified side (left, right, top, or bottom).

    Args:
        image: PIL Image to crop
        border_color: RGB color of the margins to remove. If None, auto-detects from edges.
        tolerance: Color distance tolerance for matching margin pixels (0-255)
        sides: Which side to process. Options: "left", "right", "top", "bottom" (default: "left")

    Returns:
        Cropped PIL Image with specified margin removed
    """
    # Convert to RGB if needed
    if image.mode != "RGB":
        img_rgb = image.convert("RGB")
    else:
        img_rgb = image

    # Get image data
    pixels = img_rgb.load()
    width, height = img_rgb.size

    # Calculate color distance function
    def color_distance(rgb1, rgb2):
        """Calculate Euclidean distance between two RGB colors."""
        return sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)) ** 0.5

    # Exclude top and bottom edges (often have different colors like headers/footers)
    edge_exclusion = max(10, height // 20)  # Exclude ~5% from top and bottom
    scan_y_start = edge_exclusion
    scan_y_end = height - edge_exclusion

    # Sample first 20 pixels from left edge to determine left margin color
    left_margin_pixels = []
    sample_width = min(20, width)
    for x in range(sample_width):
        for y in range(
            scan_y_start, scan_y_end, max(1, (scan_y_end - scan_y_start) // 20)
        ):
            left_margin_pixels.append(pixels[x, y])

    if left_margin_pixels:
        r_vals = [p[0] for p in left_margin_pixels]
        g_vals = [p[1] for p in left_margin_pixels]
        b_vals = [p[2] for p in left_margin_pixels]
        left_margin_color = (
            int(statistics.mean(r_vals)),
            int(statistics.mean(g_vals)),
            int(statistics.mean(b_vals)),
        )
    else:
        # Fallback to provided border_color or default
        left_margin_color = border_color if border_color else (240, 240, 240)

    # Sample first 20 pixels from right edge to determine right margin color
    right_margin_pixels = []
    for x in range(max(0, width - sample_width), width):
        for y in range(
            scan_y_start, scan_y_end, max(1, (scan_y_end - scan_y_start) // 20)
        ):
            right_margin_pixels.append(pixels[x, y])

    if right_margin_pixels:
        r_vals = [p[0] for p in right_margin_pixels]
        g_vals = [p[1] for p in right_margin_pixels]
        b_vals = [p[2] for p in right_margin_pixels]
        right_margin_color = (
            int(statistics.mean(r_vals)),
            int(statistics.mean(g_vals)),
            int(statistics.mean(b_vals)),
        )
    else:
        # Fallback to left margin color or provided border_color
        right_margin_color = (
            left_margin_color
            if left_margin_pixels
            else (border_color if border_color else (240, 240, 240))
        )

    # Normalize sides parameter
    side = sides.lower()

    if side == "left":
        # Scan from left edge inward until we find a column with non-margin content
        # Ensure we scan at least 50% of width from the left edge to catch left borders
        min_scan_distance = min(
            int(width * 0.5), 1000
        )  # Always scan at least 50% from left edge (or 1000px)
        scan_limit = min_scan_distance  # Maximum distance to scan from left edge

        left = 0
        # Scan from left edge, ensuring we check at least 50% from left
        for x in range(scan_limit):
            # Check if this column has only margin color (within tolerance)
            all_margin = True
            sample_size = min(30, scan_y_end - scan_y_start)
            step = max(1, (scan_y_end - scan_y_start) // sample_size)

            for y in range(scan_y_start, scan_y_end, step):
                pixel_rgb = pixels[x, y]
                distance = color_distance(pixel_rgb, left_margin_color)
                if distance > tolerance:
                    # Found a non-margin pixel - this column has content
                    all_margin = False
                    break

            if not all_margin:
                # Found content, stop here
                left = x
                break

        # Add small padding to avoid cutting too close
        padding = 2
        left = max(0, left - padding)

        # Crop only left margin, keep full width and height
        return image.crop((left, 0, width, height))

    elif side == "right":
        # Scan from right edge inward until we find a column with non-margin content
        # Ensure we scan at least 50% of width from the right edge to catch right borders
        min_scan_distance = int(width * 0.5)  # Always scan at least 50% from right edge
        max_scan_start = (
            width - min_scan_distance
        )  # Maximum scan_start to ensure we scan enough

        right = width
        scan_start = max_scan_start
        for x in range(width - 1, scan_start - 1, -1):
            # Check if this column has only margin color (within tolerance)
            all_margin = True
            sample_size = min(30, scan_y_end - scan_y_start)
            step = max(1, (scan_y_end - scan_y_start) // sample_size)

            for y in range(scan_y_start, scan_y_end, step):
                pixel_rgb = pixels[x, y]
                distance = color_distance(pixel_rgb, right_margin_color)
                if distance > tolerance:
                    # Found a non-margin pixel - this column has content
                    all_margin = False
                    break

            if not all_margin:
                # Found content, stop here (content extends to x+1)
                right = x + 1
                break

        # Add small padding to avoid cutting too close
        padding = 2
        right = min(width, right + padding)

        # Crop only right margin, keep full height
        return image.crop((0, 0, right, height))

    elif side == "top":
        # Scan from top edge downward until we find a row with non-margin content
        # Sample first 20 pixels from top edge to determine top margin color
        top_margin_pixels = []
        sample_height = min(20, height)
        edge_exclusion_x = max(10, width // 20)  # Exclude ~5% from left and right
        scan_x_start = edge_exclusion_x
        scan_x_end = width - edge_exclusion_x

        for y in range(sample_height):
            for x in range(
                scan_x_start, scan_x_end, max(1, (scan_x_end - scan_x_start) // 20)
            ):
                top_margin_pixels.append(pixels[x, y])

        if top_margin_pixels:
            r_vals = [p[0] for p in top_margin_pixels]
            g_vals = [p[1] for p in top_margin_pixels]
            b_vals = [p[2] for p in top_margin_pixels]
            top_margin_color = (
                int(statistics.mean(r_vals)),
                int(statistics.mean(g_vals)),
                int(statistics.mean(b_vals)),
            )
        else:
            top_margin_color = border_color if border_color else (240, 240, 240)

        # Ensure we scan at least 50% of height from the top edge
        min_scan_distance = min(int(height * 0.5), 1000)
        scan_limit = min_scan_distance

        top = 0
        for y in range(scan_limit):
            # Check if this row has only margin color (within tolerance)
            all_margin = True
            sample_size = min(30, scan_x_end - scan_x_start)
            step = max(1, (scan_x_end - scan_x_start) // sample_size)

            for x in range(scan_x_start, scan_x_end, step):
                pixel_rgb = pixels[x, y]
                distance = color_distance(pixel_rgb, top_margin_color)
                if distance > tolerance:
                    all_margin = False
                    break

            if not all_margin:
                top = y
                break

        padding = 2
        top = max(0, top - padding)

        # Crop only top margin, keep full width
        return image.crop((0, top, width, height))

    elif side == "bottom":
        # Scan from bottom edge upward until we find a row with non-margin content
        # Sample last 20 pixels from bottom edge to determine bottom margin color
        bottom_margin_pixels = []
        sample_height = min(20, height)
        edge_exclusion_x = max(10, width // 20)  # Exclude ~5% from left and right
        scan_x_start = edge_exclusion_x
        scan_x_end = width - edge_exclusion_x

        for y in range(max(0, height - sample_height), height):
            for x in range(
                scan_x_start, scan_x_end, max(1, (scan_x_end - scan_x_start) // 20)
            ):
                bottom_margin_pixels.append(pixels[x, y])

        if bottom_margin_pixels:
            r_vals = [p[0] for p in bottom_margin_pixels]
            g_vals = [p[1] for p in bottom_margin_pixels]
            b_vals = [p[2] for p in bottom_margin_pixels]
            bottom_margin_color = (
                int(statistics.mean(r_vals)),
                int(statistics.mean(g_vals)),
                int(statistics.mean(b_vals)),
            )
        else:
            bottom_margin_color = border_color if border_color else (240, 240, 240)

        # Ensure we scan at least 50% of height from the bottom edge
        min_scan_distance = int(height * 0.5)
        max_scan_start = height - min_scan_distance

        bottom = height
        scan_start = max_scan_start
        for y in range(height - 1, scan_start - 1, -1):
            # Check if this row has only margin color (within tolerance)
            all_margin = True
            sample_size = min(30, scan_x_end - scan_x_start)
            step = max(1, (scan_x_end - scan_x_start) // sample_size)

            for x in range(scan_x_start, scan_x_end, step):
                pixel_rgb = pixels[x, y]
                distance = color_distance(pixel_rgb, bottom_margin_color)
                if distance > tolerance:
                    all_margin = False
                    break

            if not all_margin:
                bottom = y + 1
                break

        padding = 2
        bottom = min(height, bottom + padding)

        # Crop only bottom margin, keep full width
        return image.crop((0, 0, width, bottom))
    else:
        # Invalid side parameter, return original
        return image
