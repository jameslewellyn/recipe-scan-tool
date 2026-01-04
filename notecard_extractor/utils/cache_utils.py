#!/usr/bin/env python3
"""
HTTP cache utility functions.
Handles cache headers and ETag validation.
"""

from typing import Optional


def get_cache_headers(image_hash: Optional[str] = None) -> dict:
    """
    Generate HTTP caching headers for images.
    Uses ETag based on image hash for validation.
    
    Args:
        image_hash: Optional SHA256 hash of the image
        
    Returns:
        Dictionary of HTTP headers
    """
    headers = {
        "Cache-Control": "public, max-age=31536000, immutable",  # 1 year cache
    }
    
    if image_hash:
        headers["ETag"] = f'"{image_hash}"'
    
    return headers


def check_cache_etag(request_etag: Optional[str], image_hash: Optional[str]) -> bool:
    """
    Check if the client's ETag matches the image hash.
    Returns True if cache is valid (should return 304 Not Modified).
    
    Args:
        request_etag: ETag from request headers (If-None-Match)
        image_hash: SHA256 hash of the image
        
    Returns:
        True if cache is valid, False otherwise
    """
    if not request_etag or not image_hash:
        return False
    
    # Remove quotes from ETag if present
    request_etag = request_etag.strip('"')
    return request_etag == image_hash
