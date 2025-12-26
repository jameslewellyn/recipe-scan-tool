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

## Table 3: `dishimage`

Stores dish images associated with recipes. Each recipe can have multiple dish images.

### Columns:

| Column Name           | Type                                       | Description                                     |
| --------------------- | ------------------------------------------ | ----------------------------------------------- |
| `id`                  | INTEGER (Primary Key)                      | Unique identifier for the dish image            |
| `recipe_id`           | INTEGER (Foreign Key → recipe.id, Indexed) | Reference to the parent Recipe                  |
| `image_number`        | INTEGER                                    | Image number/position (1-indexed, for ordering) |
| `rotation`            | INTEGER                                    | Rotation angle (0, 90, 180, or 270 degrees)     |
| `image_data`          | BLOB                                       | Full dish image data                            |
| `image_sha256`        | VARCHAR(64) (Indexed)                      | SHA256 hash of the full image                   |
| `medium_image_data`   | BLOB                                       | Medium-sized version of the image (max 800px)   |
| `medium_image_sha256` | VARCHAR(64) (Indexed)                      | SHA256 hash of the medium image                 |
| `thumbnail_data`      | BLOB                                       | Thumbnail version of the image (max 200px)      |
| `thumbnail_sha256`    | VARCHAR(64) (Indexed)                      | SHA256 hash of the thumbnail                    |

---

## Table 4: `recipetaglist`

Stores the list of available tags that can be assigned to recipes.

### Columns:

| Column Name | Type                  | Description                    |
| ---------- | --------------------- | ------------------------------ |
| `id`       | INTEGER (Primary Key) | Unique identifier for the tag  |
| `tag_name` | VARCHAR(100) (Indexed, Unique) | The name of the tag (must be unique) |

---

## Table 5: `recipetag`

Junction table linking recipes to tags (many-to-many relationship). Each recipe can have many tags, and each tag can be assigned to many recipes.

### Columns:

| Column Name | Type                                       | Description                        |
| ----------- | ------------------------------------------ | ---------------------------------- |
| `id`        | INTEGER (Primary Key)                      | Unique identifier for the tag link |
| `recipe_id` | INTEGER (Foreign Key → recipe.id, Indexed) | Reference to the Recipe            |
| `tag_id`    | INTEGER (Foreign Key → recipetaglist.id, Indexed) | Reference to the Tag            |

### Constraints:

- Unique constraint on (`recipe_id`, `tag_id`) to prevent duplicate tag assignments to the same recipe

---

## Relationships

-   **One-to-Many**: One `Recipe` can have multiple `RecipeImage` entries (one per PDF page)
-   **One-to-Many**: One `Recipe` can have multiple `DishImage` entries
-   **Many-to-Many**: One `Recipe` can have multiple `RecipeTag` entries, linking to multiple tags in `RecipeTagList`
-   **Many-to-Many**: One tag in `RecipeTagList` can be assigned to multiple recipes via `RecipeTag`
-   The web GUI displays images from `RecipeImage` where `pdf_page_number = 0` (page 1) for each recipe
-   Rotation is stored per image in both `RecipeImage` and `DishImage` tables, allowing different rotations for different images
