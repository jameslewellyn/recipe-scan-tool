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


if __name__ == "__main__":
    app()
