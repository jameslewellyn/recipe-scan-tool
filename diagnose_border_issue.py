#!/usr/bin/env python3
"""
Diagnose the grey border removal issue on the left side.
Examines the left border of the image and tests the removal function.
"""

import sys
from pathlib import Path
from PIL import Image
import statistics

# Import border removal functions
sys.path.insert(0, str(Path(__file__).parent))
from notecard_extractor.image_processing import autocrop_grey_border


def analyze_left_border(image_path: Path):
    """Analyze the left border of an image to understand why removal might fail."""
    print(f"{'=' * 60}")
    print(f"Analyzing: {image_path.name}")
    print(f"{'=' * 60}\n")

    image = Image.open(image_path)
    if image.mode != "RGB":
        image = image.convert("RGB")

    width, height = image.size
    pixels = image.load()

    print(f"Image size: {width}x{height} pixels\n")

    # Sample left edge pixels (first 50 pixels)
    sample_width = min(50, width)
    edge_exclusion = max(10, height // 20)
    scan_y_start = edge_exclusion
    scan_y_end = height - edge_exclusion

    print(f"Sampling left edge (first {sample_width} pixels)")
    print(f"Excluding top/bottom {edge_exclusion}px\n")

    # Collect left edge pixels
    left_edge_pixels = []
    for x in range(sample_width):
        for y in range(
            scan_y_start, scan_y_end, max(1, (scan_y_end - scan_y_start) // 20)
        ):
            left_edge_pixels.append(pixels[x, y])

    if left_edge_pixels:
        r_vals = [p[0] for p in left_edge_pixels]
        g_vals = [p[1] for p in left_edge_pixels]
        b_vals = [p[2] for p in left_edge_pixels]

        avg_color = (
            int(statistics.mean(r_vals)),
            int(statistics.mean(g_vals)),
            int(statistics.mean(b_vals)),
        )

        print(f"Average left border color: RGB{avg_color}")
        print(f"  R: {avg_color[0]} (min: {min(r_vals)}, max: {max(r_vals)})")
        print(f"  G: {avg_color[1]} (min: {min(g_vals)}, max: {max(g_vals)})")
        print(f"  B: {avg_color[2]} (min: {min(b_vals)}, max: {max(b_vals)})\n")

        # Check variance in the border
        r_variance = statistics.variance(r_vals) if len(r_vals) > 1 else 0
        g_variance = statistics.variance(g_vals) if len(g_vals) > 1 else 0
        b_variance = statistics.variance(b_vals) if len(b_vals) > 1 else 0

        print(f"Color variance in border:")
        print(f"  R variance: {r_variance:.2f}")
        print(f"  G variance: {g_variance:.2f}")
        print(f"  B variance: {b_variance:.2f}\n")

        # Sample content area at different x positions to see where content actually starts
        print("Checking columns to find where content starts:")
        print("(Looking for columns with different colors or higher variance)\n")

        def color_distance(rgb1, rgb2):
            return sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)) ** 0.5

        # Check columns at different x positions
        check_positions = [0, 10, 20, 50, 100, 150, 200, 300, 400, 500]
        for x_pos in check_positions:
            if x_pos >= width:
                break

            column_pixels = []
            for y in range(
                scan_y_start, scan_y_end, max(1, (scan_y_end - scan_y_start) // 30)
            ):
                column_pixels.append(pixels[x_pos, y])

            if column_pixels:
                col_r = [p[0] for p in column_pixels]
                col_g = [p[1] for p in column_pixels]
                col_b = [p[2] for p in column_pixels]

                col_avg = (
                    int(statistics.mean(col_r)),
                    int(statistics.mean(col_g)),
                    int(statistics.mean(col_b)),
                )

                col_variance = (
                    statistics.variance(col_r)
                    + statistics.variance(col_g)
                    + statistics.variance(col_b)
                )
                distance = color_distance(col_avg, avg_color)

                # Check if this column would be considered "border" with tolerance 60
                margin_count = 0
                total_samples = 0
                for pixel in column_pixels:
                    dist = color_distance(pixel, avg_color)
                    total_samples += 1
                    if dist <= 60:
                        margin_count += 1

                margin_ratio = margin_count / total_samples if total_samples > 0 else 0
                is_border = margin_ratio >= 0.9  # Same threshold as the algorithm

                status = "BORDER" if is_border else "CONTENT"
                print(
                    f"  Column {x_pos:4d}: RGB{col_avg} | Distance: {distance:6.2f} | "
                    f"Variance: {col_variance:7.2f} | Margin ratio: {margin_ratio:.2f} | {status}"
                )

        # Sample content area (around column 200-300)
        content_start_x = 200
        content_end_x = min(300, width)
        content_pixels = []
        for x in range(content_start_x, content_end_x):
            for y in range(
                scan_y_start, scan_y_end, max(1, (scan_y_end - scan_y_start) // 20)
            ):
                content_pixels.append(pixels[x, y])

        if content_pixels:
            content_r = [p[0] for p in content_pixels]
            content_g = [p[1] for p in content_pixels]
            content_b = [p[2] for p in content_pixels]

            avg_content_color = (
                int(statistics.mean(content_r)),
                int(statistics.mean(content_g)),
                int(statistics.mean(content_b)),
            )

            print(
                f"\nAverage content color (x={content_start_x}-{content_end_x}): RGB{avg_content_color}\n"
            )

            # Calculate color distance
            distance = color_distance(avg_color, avg_content_color)
            print(f"Color distance between border and content: {distance:.2f}\n")

    # Now test the actual function
    print(f"{'=' * 60}")
    print("Testing autocrop_grey_border function:")
    print(f"{'=' * 60}\n")

    original_size = image.size
    result = autocrop_grey_border(image, border_color=None, tolerance=60, sides="left")
    result_size = result.size

    print(f"Original size: {original_size[0]}x{original_size[1]}")
    print(f"Result size: {result_size[0]}x{result_size[1]}")
    width_removed = original_size[0] - result_size[0]
    print(f"Width removed: {width_removed}px\n")

    if width_removed == 0:
        print("❌ ISSUE: No border was removed from the left side!")
        print("\nAnalysis:")
        print("The algorithm scans columns from left to right, checking if each column")
        print("is 'all margin' (90%+ pixels within tolerance of border color).")
        print("It stops when it finds a column that is NOT all margin.")
        print("\nIf no border is removed, it means:")
        print("1. The content color is too similar to the border color")
        print("2. The algorithm never finds a 'non-margin' column to stop at")
        print("3. The border might extend very far into the image")
    else:
        print(f"✓ Border removal worked: removed {width_removed}px")


if __name__ == "__main__":
    diagnose_dir = Path(__file__).parent / "diagnose"

    # Look for white_removed image
    white_removed = diagnose_dir / "page2_image1_white_removed.jpg"
    if white_removed.exists():
        analyze_left_border(white_removed)
    else:
        # Try the extracted_pages folder
        white_removed = (
            Path(__file__).parent
            / "extracted_pages"
            / "01_white_removed"
            / "page2_image1.jpg"
        )
        if white_removed.exists():
            analyze_left_border(white_removed)
        else:
            print(f"Error: Could not find white_removed image")
            print(f"Looked in: {diagnose_dir}")
            print(
                f"         : {Path(__file__).parent / 'extracted_pages' / '01_white_removed'}"
            )
