from pathlib import Path
import subprocess
import typer
import shutil

app = typer.Typer()


@app.command()
def extract_notecards(
    input_folder: Path = typer.Argument(
        ..., help="Folder containing PDF files to process"
    ),
):
    """
    Extract a single image from each PDF file in the input folder.
    Images are saved to a folder named '{input_folder}_images' next to the input folder.
    """
    # Validate input folder
    input_folder = Path(input_folder).resolve()
    if not input_folder.is_dir():
        typer.echo(f"Error: '{input_folder}' is not a valid directory.", err=True)
        raise typer.Exit(code=1)

    # Create output folder
    output_folder = input_folder.parent / f"{input_folder.name}_images"
    output_folder.mkdir(exist_ok=True)
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

            # Use pdfly to extract images - it extracts to a temp location
            # We'll extract to a temp folder first, then move the first image
            temp_output = pdf_file.parent / f"{pdf_file.stem}_temp_images"
            temp_output.mkdir(exist_ok=True)

            try:
                # Run pdfly extract-images command
                subprocess.run(
                    [
                        "pdfly",
                        "extract-images",
                        str(pdf_file),
                        "--output",
                        str(temp_output),
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                # Find the first extracted image (look for common image extensions)
                # pdfly might extract to subdirectories, so use rglob
                image_extensions = [
                    "*.png",
                    "*.jpg",
                    "*.jpeg",
                    "*.gif",
                    "*.bmp",
                    "*.tiff",
                ]
                extracted_images = []
                for ext in image_extensions:
                    extracted_images.extend(temp_output.rglob(ext))

                if extracted_images:
                    # Sort to get consistent ordering and take the first one
                    first_image = sorted(extracted_images)[0]
                    # Preserve the original extension
                    output_path = output_folder / f"{pdf_file.stem}{first_image.suffix}"

                    # Copy the image to the final output folder
                    shutil.copy2(first_image, output_path)
                    typer.echo(f"  ✓ Extracted image: {output_path.name}")
                else:
                    typer.echo(f"  ⚠ No images found in '{pdf_file.name}'", err=True)

            finally:
                # Clean up temp folder
                if temp_output.exists():
                    shutil.rmtree(temp_output)

        except subprocess.CalledProcessError as e:
            typer.echo(f"  ✗ Error processing '{pdf_file.name}': {e.stderr}", err=True)
        except Exception as e:
            typer.echo(f"  ✗ Error processing '{pdf_file.name}': {e}", err=True)

    typer.echo(f"\nDone! Images saved to: {output_folder}")


if __name__ == "__main__":
    app()
