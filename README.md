# Notecard Extractor

A Python tool to extract and crop notecard images from PDF files. This tool processes PDF files where each page contains a picture of a notecard with some padding around it. It automatically detects the notecard boundaries, crops the image, and saves each page as a separate JPEG file.

## Installation

This project uses Poetry for dependency management. To install:

1. Make sure you have Poetry installed
2. Clone this repository
3. Run:
```bash
poetry install
```

## Usage

The tool can be used in two ways:

1. Using Poetry:
```bash
poetry run extract-notecards /path/to/pdf/folder
```

2. After activating the Poetry environment:
```bash
extract-notecards /path/to/pdf/folder
```

### Options

- `INPUT_FOLDER`: Required. The folder containing PDF files to process
- `--output-folder`: Optional. Specify a different output folder for the cropped images. If not provided, images will be saved alongside the original PDFs.

### Example

```bash
extract-notecards ./my-pdfs --output-folder ./cropped-images
```

This will:
1. Process all PDF files in the `./my-pdfs` directory
2. Extract each page as an image
3. Detect and crop the notecard from each image
4. Save the cropped images as JPEGs in the `./cropped-images` directory
5. Name each image using the format: `{original_pdf_name}_page{number}.jpg`

## Requirements

- Python 3.9 or higher
- Poppler (required by pdf2image)
  - On Ubuntu/Debian: `apt-get install poppler-utils`
  - On macOS: `brew install poppler`
  - On Windows: Download and install from [poppler releases](http://blog.alivate.com.au/poppler-windows/) 