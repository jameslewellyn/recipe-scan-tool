from pathlib import Path
import typer
from pypdf import PdfReader
from PIL import Image
import io

app = typer.Typer()


@app.command()
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
    Extract a single image from each PDF file in the input folder.
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

            # Iterate through pages to find the first image
            for page_num, page in enumerate(reader.pages):
                if images_found:
                    break

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

                        # Save the first image found
                        output_path = output_folder / f"{pdf_file.stem}{ext}"
                        image.save(output_path)
                        typer.echo(f"  ✓ Extracted image: {output_path.name}")
                        images_found = True
                        break

                    except Exception as e:
                        typer.echo(
                            f"  ⚠ Error extracting image {image_index} from page {page_num + 1}: {e}",
                            err=True,
                        )
                        continue

            if not images_found:
                typer.echo(f"  ⚠ No images found in '{pdf_file.name}'", err=True)

        except Exception as e:
            typer.echo(f"  ✗ Error processing '{pdf_file.name}': {e}", err=True)

    typer.echo(f"\nDone! Images saved to: {output_folder}")


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


@app.command()
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


# Separate app for white-border-remover command
white_border_remover_app = typer.Typer()
white_border_remover_app.command()(white_border_remover)


if __name__ == "__main__":
    app()
