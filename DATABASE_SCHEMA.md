# Database Schema

## Table 1: `recipe`

Stores recipe data including original PDF and metadata. Each PDF upload creates one Recipe entry.

### Columns:

| Column Name            | Type                  | Description                                                                 |
| ---------------------- | --------------------- | --------------------------------------------------------------------------- |
| `id`                   | INTEGER (Primary Key) | Unique identifier for the recipe                                            |
| `original_pdf_data`    | BLOB                  | The original PDF file data                                                  |
| `original_pdf_sha256`  | VARCHAR(64) (Indexed) | SHA256 hash of the original PDF                                             |
| `pdf_filename`         | VARCHAR(500)          | Original filename of the uploaded PDF                                       |
| `pdf_upload_timestamp` | DATETIME              | Timestamp when the PDF was uploaded                                         |
| `state`                | VARCHAR               | Recipe state (not_started, partially_complete, complete, broken, duplicate) |
| `title`                | VARCHAR(500)          | Recipe title                                                                |
| `description`          | TEXT                  | Recipe description                                                          |
| `year`                 | INTEGER               | Year associated with the recipe                                             |
| `author`               | VARCHAR(200)          | Author of the recipe                                                        |
| `ingredients`          | TEXT                  | Recipe ingredients                                                          |
| `recipe`               | TEXT                  | Recipe instructions/steps                                                   |
| `cook_time`            | VARCHAR(100)          | Cooking time                                                                |
| `notes`                | TEXT                  | Additional notes                                                            |
| `dish_picture_1`       | BLOB                  | First dish picture                                                          |
| `dish_picture_2`       | BLOB                  | Second dish picture                                                         |
| `dish_picture_3`       | BLOB                  | Third dish picture                                                          |
| `dish_picture_4`       | BLOB                  | Fourth dish picture                                                         |

---

## Table 2: `recipeimage`

Stores images extracted from PDF pages. Each page of a PDF gets one RecipeImage entry, associated with a Recipe via `recipe_id`.

### Columns:

| Column Name            | Type                                       | Description                                            |
| ---------------------- | ------------------------------------------ | ------------------------------------------------------ |
| `id`                   | INTEGER (Primary Key)                      | Unique identifier for the recipe image                 |
| `recipe_id`            | INTEGER (Foreign Key → recipe.id, Indexed) | Reference to the parent Recipe                         |
| `pdf_page_number`      | INTEGER                                    | PDF page number (0-indexed, where 0 is the first page) |
| `rotation`             | INTEGER                                    | Rotation angle (0, 90, 180, or 270 degrees)            |
| `cropped_image_data`   | BLOB                                       | Processed cropped image data (PNG format)              |
| `cropped_image_sha256` | VARCHAR(64) (Indexed)                      | SHA256 hash of the cropped image                       |
| `medium_image_data`    | BLOB                                       | Medium-sized version of the image (max 800px)          |
| `medium_image_sha256`  | VARCHAR(64) (Indexed)                      | SHA256 hash of the medium image                        |
| `thumbnail_data`       | BLOB                                       | Thumbnail version of the image (max 200px)             |
| `thumbnail_sha256`     | VARCHAR(64) (Indexed)                      | SHA256 hash of the thumbnail                           |

---

## Relationships

-   **One-to-Many**: One `Recipe` can have multiple `RecipeImage` entries (one per PDF page)
-   The web GUI displays images from `RecipeImage` where `pdf_page_number = 0` (page 1) for each recipe
-   Rotation is stored per image in the `RecipeImage` table, allowing different rotations for different pages
