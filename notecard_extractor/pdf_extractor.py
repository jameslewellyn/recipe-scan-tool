#!/usr/bin/env python3
"""
PDF extraction functionality.
Extracts images from PDF files.
"""

from pathlib import Path
import typer
from pypdf import PdfReader
from PIL import Image
import io


def extract_notecards(
    input_folder: Path = typer.Argument(
        ..., help="Folder containing PDF files to process"
    ),
    output_folder: Path = typer.Option(
        None,
        "--output-folder",
        help="Optional output folder for extracted images. If not provided, images will be saved to '{input_folder}_images' next to the input folder.",
    ),
):
    """
    Extract images from each page of each PDF file in the input folder.
    Each page's image is saved as a separate file with _page# before the suffix.
    Images are saved to the specified output folder, or to '{input_folder}_images' if not provided.
    """
    # Validate input folder
    input_folder = Path(input_folder).resolve()
    if not input_folder.is_dir():
        typer.echo(f"Error: '{input_folder}' is not a valid directory.", err=True)
        raise typer.Exit(code=1)

    # Determine output folder
    if output_folder is None:
        output_folder = input_folder.parent / f"{input_folder.name}_images"
    else:
        output_folder = Path(output_folder).resolve()

    output_folder.mkdir(parents=True, exist_ok=True)
    typer.echo(f"Output folder: {output_folder}")

    # Find all PDF files
    pdf_files = sorted(input_folder.glob("*.pdf"))
    if not pdf_files:
        typer.echo(f"No PDF files found in '{input_folder}'.", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Found {len(pdf_files)} PDF file(s) to process...")

    # Process each PDF
    for pdf_file in pdf_files:
        try:
            typer.echo(f"Processing: {pdf_file.name}")

            # Read PDF and extract images
            reader = PdfReader(pdf_file)
            images_found = False

            # Iterate through pages to extract one image per page
            for page_num, page in enumerate(reader.pages):
                page_image_found = False

                # Extract images from the page
                for image_index, image_file_object in enumerate(page.images):
                    try:
                        # Get image data
                        image_data = image_file_object.data

                        # Determine file extension from image name or default to png
                        image_name = image_file_object.name
                        if image_name:
                            # Try to infer extension from name
                            ext = Path(image_name).suffix.lower()
                            if ext not in [
                                ".png",
                                ".jpg",
                                ".jpeg",
                                ".gif",
                                ".bmp",
                                ".tiff",
                            ]:
                                ext = ".png"  # Default to PNG
                        else:
                            ext = ".png"  # Default to PNG

                        # Open image with PIL
                        image = Image.open(io.BytesIO(image_data))

                        # Save image with _page# before the suffix
                        output_path = (
                            output_folder / f"{pdf_file.stem}_page{page_num}{ext}"
                        )
                        image.save(output_path)
                        typer.echo(
                            f"  ✓ Extracted image from page {page_num + 1}: {output_path.name}"
                        )
                        images_found = True
                        page_image_found = True
                        break  # Only extract the first image from each page

                    except Exception as e:
                        typer.echo(
                            f"  ⚠ Error extracting image {image_index} from page {page_num + 1}: {e}",
                            err=True,
                        )
                        continue

                if not page_image_found:
                    typer.echo(
                        f"  ⚠ No image found on page {page_num + 1} of '{pdf_file.name}'",
                        err=True,
                    )

            if not images_found:
                typer.echo(f"  ⚠ No images found in '{pdf_file.name}'", err=True)

        except Exception as e:
            typer.echo(f"  ✗ Error processing '{pdf_file.name}': {e}", err=True)

    typer.echo(f"\nDone! Images saved to: {output_folder}")
