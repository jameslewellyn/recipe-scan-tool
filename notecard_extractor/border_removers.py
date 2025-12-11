#!/usr/bin/env python3
"""
Border removal commands.
CLI commands for removing white and grey borders from images.
"""

from pathlib import Path
import typer
from PIL import Image
from notecard_extractor.image_processing import (
    autocrop_white_border,
    autocrop_grey_border,
)


def white_border_remover(
    input_folder: Path = typer.Argument(
        ..., help="Folder containing image files to process"
    ),
    threshold: int = typer.Option(
        250,
        "--threshold",
        help="Pixel value threshold for white detection (0-255). Higher values remove more border.",
    ),
):
    """
    Remove white borders from images in the input folder.
    Cropped images are saved to '{input_folder}_white-removed' next to the input folder.
    """
    # Validate input folder
    input_folder = Path(input_folder).resolve()
    if not input_folder.is_dir():
        typer.echo(f"Error: '{input_folder}' is not a valid directory.", err=True)
        raise typer.Exit(code=1)

    # Validate threshold
    if not 0 <= threshold <= 255:
        typer.echo("Error: Threshold must be between 0 and 255.", err=True)
        raise typer.Exit(code=1)

    # Create output folder
    output_folder = input_folder.parent / f"{input_folder.name}_white-removed"
    output_folder.mkdir(parents=True, exist_ok=True)
    typer.echo(f"Output folder: {output_folder}")
    typer.echo(f"White threshold: {threshold}")

    # Find all image files
    image_extensions = [
        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.gif",
        "*.bmp",
        "*.tiff",
        "*.webp",
    ]
    image_files = []
    for ext in image_extensions:
        image_files.extend(input_folder.glob(ext))
        image_files.extend(input_folder.glob(ext.upper()))

    image_files = sorted(set(image_files))  # Remove duplicates and sort

    if not image_files:
        typer.echo(f"No image files found in '{input_folder}'.", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Found {len(image_files)} image file(s) to process...")

    # Process each image
    for image_file in image_files:
        try:
            typer.echo(f"Processing: {image_file.name}")

            # Open and process image
            with Image.open(image_file) as img:
                # Convert to RGB if needed (for saving as JPEG)
                if img.mode in ("RGBA", "LA", "P"):
                    # Create white background for transparent images
                    rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    rgb_img.paste(
                        img, mask=img.split()[-1] if img.mode == "RGBA" else None
                    )
                    img = rgb_img
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                # Crop white borders
                cropped_img = autocrop_white_border(img, threshold)

                # Save the cropped image
                output_path = output_folder / image_file.name
                # Preserve format, but convert RGBA to RGB for JPEG
                if output_path.suffix.lower() in [".jpg", ".jpeg"]:
                    if cropped_img.mode == "RGBA":
                        rgb_img = Image.new("RGB", cropped_img.size, (255, 255, 255))
                        rgb_img.paste(cropped_img, mask=cropped_img.split()[-1])
                        cropped_img = rgb_img
                    cropped_img.save(output_path, "JPEG", quality=95)
                else:
                    cropped_img.save(output_path)

                typer.echo(f"  ✓ Cropped image: {output_path.name}")

        except Exception as e:
            typer.echo(f"  ✗ Error processing '{image_file.name}': {e}", err=True)

    typer.echo(f"\nDone! Cropped images saved to: {output_folder}")


def grey_border_remover(
    input_folder: Path = typer.Argument(
        ..., help="Folder containing image files to process"
    ),
    border_r: int = typer.Option(
        None,
        "--border-r",
        help="Red component of border color (0-255). If not specified, auto-detects from image edges.",
    ),
    border_g: int = typer.Option(
        None,
        "--border-g",
        help="Green component of border color (0-255). If not specified, auto-detects from image edges.",
    ),
    border_b: int = typer.Option(
        None,
        "--border-b",
        help="Blue component of border color (0-255). If not specified, auto-detects from image edges.",
    ),
    tolerance: int = typer.Option(
        60,
        "--tolerance",
        help="Color distance tolerance for matching border pixels (0-255). Higher values remove more border.",
    ),
):
    """
    Remove greyish left and right margins from images in the input folder.
    Only removes side margins, keeping full height. Cropped images are saved to '{input_folder}_grey-removed' next to the input folder.
    """
    # Validate input folder
    input_folder = Path(input_folder).resolve()
    if not input_folder.is_dir():
        typer.echo(f"Error: '{input_folder}' is not a valid directory.", err=True)
        raise typer.Exit(code=1)

    # Validate color components if provided
    if border_r is not None or border_g is not None or border_b is not None:
        if not all(c is not None for c in [border_r, border_g, border_b]):
            typer.echo(
                "Error: All border color components (--border-r, --border-g, --border-b) must be provided together, or none at all for auto-detection.",
                err=True,
            )
            raise typer.Exit(code=1)
        if not all(0 <= c <= 255 for c in [border_r, border_g, border_b]):
            typer.echo(
                "Error: Border color components must be between 0 and 255.", err=True
            )
            raise typer.Exit(code=1)
        border_color = (border_r, border_g, border_b)
    else:
        border_color = None  # Will be auto-detected

    # Validate tolerance
    if not 0 <= tolerance <= 255:
        typer.echo("Error: Tolerance must be between 0 and 255.", err=True)
        raise typer.Exit(code=1)

    # Create output folder
    output_folder = input_folder.parent / f"{input_folder.name}_grey-removed"
    output_folder.mkdir(parents=True, exist_ok=True)
    typer.echo(f"Output folder: {output_folder}")
    if border_color:
        typer.echo(f"Border color: RGB{border_color}")
    else:
        typer.echo("Border color: Auto-detecting from image edges")
    typer.echo(f"Tolerance: {tolerance}")

    # Find all image files
    image_extensions = [
        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.gif",
        "*.bmp",
        "*.tiff",
        "*.webp",
    ]
    image_files = []
    for ext in image_extensions:
        image_files.extend(input_folder.glob(ext))
        image_files.extend(input_folder.glob(ext.upper()))

    image_files = sorted(set(image_files))  # Remove duplicates and sort

    if not image_files:
        typer.echo(f"No image files found in '{input_folder}'.", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Found {len(image_files)} image file(s) to process...")

    # Process each image
    for image_file in image_files:
        try:
            typer.echo(f"Processing: {image_file.name}")

            # Open and process image
            with Image.open(image_file) as img:
                # Convert to RGB if needed (for saving as JPEG)
                if img.mode in ("RGBA", "LA", "P"):
                    # Create white background for transparent images
                    rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    rgb_img.paste(
                        img, mask=img.split()[-1] if img.mode == "RGBA" else None
                    )
                    img = rgb_img
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                # Crop grey borders
                cropped_img = autocrop_grey_border(img, border_color, tolerance)

                # Save the cropped image
                output_path = output_folder / image_file.name
                # Preserve format, but convert RGBA to RGB for JPEG
                if output_path.suffix.lower() in [".jpg", ".jpeg"]:
                    if cropped_img.mode == "RGBA":
                        rgb_img = Image.new("RGB", cropped_img.size, (255, 255, 255))
                        rgb_img.paste(cropped_img, mask=cropped_img.split()[-1])
                        cropped_img = rgb_img
                    cropped_img.save(output_path, "JPEG", quality=95)
                else:
                    cropped_img.save(output_path)

                typer.echo(f"  ✓ Cropped image: {output_path.name}")

        except Exception as e:
            typer.echo(f"  ✗ Error processing '{image_file.name}': {e}", err=True)

    typer.echo(f"\nDone! Cropped images saved to: {output_folder}")
