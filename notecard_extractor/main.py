import os
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
import typer
from pdf2image import convert_from_path
from PIL import Image

app = typer.Typer()

def trim_borders(image: np.ndarray, threshold_value: int = 250) -> np.ndarray:
    """Remove borders of a specific brightness threshold from the image."""
    # Convert to grayscale if not already
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Apply threshold to identify non-border pixels
    _, thresh = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY_INV)

    # Find the bounding box of content pixels
    coords = cv2.findNonZero(thresh)
    if coords is None:
        return image  # Return original image if no content pixels found
        
    x, y, w, h = cv2.boundingRect(coords)
    
    # Add a small padding around the content
    padding = 5  # Reduced padding since we're doing two passes
    x = max(0, x - padding)
    y = max(0, y - padding)
    w = min(image.shape[1] - x, w + 2 * padding)
    h = min(image.shape[0] - y, h + 2 * padding)
    
    # Crop the image to the content area
    return image[y:y+h, x:x+w]

def process_image(image: np.ndarray) -> np.ndarray:
    """Process image by removing white borders first, then grey padding."""
    # First pass: remove pure white borders (threshold 250)
    image = trim_borders(image, threshold_value=250)
    
    # Second pass: remove light grey padding (threshold 235)
    image = trim_borders(image, threshold_value=235)
    
    # Third pass: remove darker grey padding (threshold 225)
    image = trim_borders(image, threshold_value=140)
    
    return image

@app.command()
def extract_notecards(
    input_folder: str = typer.Argument(..., help="Folder containing PDF files"),
    output_folder: str = typer.Option(None, help="Optional output folder (defaults to same as input)")
):
    """Extract and trim white borders and grey padding from PDF pages."""
    input_path = Path(input_folder)
    if not input_path.exists():
        typer.echo(f"Error: Input folder '{input_folder}' does not exist")
        raise typer.Exit(1)
        
    if output_folder:
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = input_path
        
    # Process each PDF file in the input folder
    for pdf_file in input_path.glob("*.pdf"):
        typer.echo(f"Processing {pdf_file.name}...")
        
        # Convert PDF to images
        pages = convert_from_path(pdf_file)
        
        # Process each page
        for i, page in enumerate(pages, start=1):
            # Convert PIL Image to OpenCV format
            opencv_image = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
            
            # Process the image
            processed = process_image(opencv_image)
            
            # Save the processed image
            output_filename = f"{pdf_file.stem}_page{i}.jpg"
            output_file = output_path / output_filename
            cv2.imwrite(str(output_file), processed)
            typer.echo(f"Saved {output_filename}")

if __name__ == "__main__":
    app() 