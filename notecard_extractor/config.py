#!/usr/bin/env python3
"""
Configuration and constants for the notecard extractor.
"""

from pathlib import Path

# Image processing constants
THUMBNAIL_MAX_SIZE = (200, 200)
MEDIUM_IMAGE_MAX_SIZE = (800, 800)
WHITE_BORDER_THRESHOLD = 250
GREY_BORDER_TOLERANCE = 60

# Database constants
HOME_DIR = Path.home()
DEFAULT_DATABASE_PATH = HOME_DIR / "notecard_extractor.db"

# Cache constants
CACHE_MAX_AGE = 31536000  # 1 year in seconds
