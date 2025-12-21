#!/usr/bin/env python3
"""
Extract images from specific pages of a PDF file.
"""

import sys
from pathlib import Path
from pypdf import PdfReader
from PIL import Image
import io

# Import border removal functions
sys.path.insert(0, str(Path(__file__).parent))
from notecard_extractor.image_processing import (
    autocrop_white_border,
    autocrop_grey_border,
)


def extract_page_images(
    pdf_path: Path,
    page_nums: list[int],
    raw_dir: Path,
    white_removed_dir: Path,
    grey_removed_dir: Path,
):
    """Extract images from specified pages of a PDF and process them in stages."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    white_removed_dir.mkdir(parents=True, exist_ok=True)
    grey_removed_dir.mkdir(parents=True, exist_ok=True)

    print(f"Processing PDF: {pdf_path}")
    print(f"Raw images directory: {raw_dir}")
    print(f"White removed images directory: {white_removed_dir}")
    print(f"Grey removed images directory: {grey_removed_dir}\n")

    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    print(f"PDF has {total_pages} page(s)\n")

    for page_num in page_nums:
        if page_num >= total_pages:
            print(
                f"⚠️  Page {page_num + 1} (index {page_num}) does not exist (PDF has {total_pages} pages)"
            )
            continue

        print(f"{'=' * 60}")
        print(f"Page {page_num + 1} (index {page_num})")
        print(f"{'=' * 60}")

        page = reader.pages[page_num]
        images_found = 0

        for image_index, image_file_object in enumerate(page.images):
            try:
                # Get image data
                image_data = image_file_object.data

                # Determine file extension
                image_name = image_file_object.name
                if image_name:
                    ext = Path(image_name).suffix.lower()
                    if ext not in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"]:
                        ext = ".png"
                else:
                    ext = ".png"

                # Open image with PIL
                image = Image.open(io.BytesIO(image_data))

                # Convert to RGB if needed
                if image.mode in ("RGBA", "LA", "P"):
                    rgb_img = Image.new("RGB", image.size, (255, 255, 255))
                    if image.mode == "P":
                        image = image.convert("RGBA")
                    rgb_img.paste(
                        image,
                        mask=image.split()[-1] if image.mode == "RGBA" else None,
                    )
                    image = rgb_img
                elif image.mode != "RGB":
                    image = image.convert("RGB")

                # Save raw image (Stage 1)
                raw_output_path = (
                    raw_dir / f"page{page_num + 1}_image{image_index + 1}{ext}"
                )
                image.save(raw_output_path)
                print(f"  ✓ Stage 1 - Raw image saved: {raw_output_path.name}")
                print(f"    Size: {image.size[0]}x{image.size[1]} pixels")

                # Stage 2: Remove white borders using autocrop_white_border
                original_size = image.size
                processed_image = autocrop_white_border(image, threshold=250)

                final_size = processed_image.size
                width_reduction = original_size[0] - final_size[0]
                height_reduction = original_size[1] - final_size[1]
                print(
                    f"  ✓ Stage 2 - White removed image size: {final_size[0]}x{final_size[1]} pixels"
                )
                if width_reduction > 0 or height_reduction > 0:
                    print(
                        f"    Removed {width_reduction}px width, {height_reduction}px height"
                    )
                else:
                    print(f"    No white borders detected")

                # Save processed image (Stage 2)
                processed_output_path = (
                    white_removed_dir
                    / f"page{page_num + 1}_image{image_index + 1}{ext}"
                )
                processed_image.save(processed_output_path)
                print(f"    Saved to: {processed_output_path.name}")

                # Stage 3: Remove grey borders (left and right)
                grey_removed_image = processed_image.copy()
                grey_removed_size_before = grey_removed_image.size

                # Remove left grey border
                grey_removed_image = autocrop_grey_border(
                    grey_removed_image,
                    border_color=None,
                    tolerance=60,
                    sides="left",
                )
                # Remove right grey border
                grey_removed_image = autocrop_grey_border(
                    grey_removed_image,
                    border_color=None,
                    tolerance=60,
                    sides="right",
                )

                grey_removed_size_after = grey_removed_image.size
                width_reduction = (
                    grey_removed_size_before[0] - grey_removed_size_after[0]
                )
                height_reduction = (
                    grey_removed_size_before[1] - grey_removed_size_after[1]
                )
                print(
                    f"  ✓ Stage 3 - Grey removed image size: {grey_removed_size_after[0]}x{grey_removed_size_after[1]} pixels"
                )
                if width_reduction > 0 or height_reduction > 0:
                    print(
                        f"    Removed {width_reduction}px width, {height_reduction}px height"
                    )
                else:
                    print(f"    No grey borders detected")

                # Save grey removed image (Stage 3)
                grey_removed_output_path = (
                    grey_removed_dir / f"page{page_num + 1}_image{image_index + 1}{ext}"
                )
                grey_removed_image.save(grey_removed_output_path)
                print(f"    Saved to: {grey_removed_output_path.name}")
                images_found += 1

            except Exception as e:
                print(f"  ✗ Error extracting image {image_index + 1}: {e}")
                continue

        if images_found == 0:
            print(f"  ⚠️  No images found on page {page_num + 1}")
        print()

    print(f"{'=' * 60}")
    print(f"Extraction complete!")
    print(f"Raw images saved to: {raw_dir}")
    print(f"White removed images saved to: {white_removed_dir}")
    print(f"Grey removed images saved to: {grey_removed_dir}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    project_root = Path(__file__).parent
    pdf_path = project_root / "inputs1" / "Scan2025-03-14_111121.pdf"

    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    raw_dir = project_root / "extracted_pages" / "00_raw"
    white_removed_dir = project_root / "extracted_pages" / "01_white_removed"
    grey_removed_dir = project_root / "extracted_pages" / "02_remove_grey"

    # Extract pages 1 and 2 (0-indexed: 0 and 1)
    extract_page_images(pdf_path, [0, 1], raw_dir, white_removed_dir, grey_removed_dir)
