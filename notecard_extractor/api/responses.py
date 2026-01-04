#!/usr/bin/env python3
"""
API response utilities.
Standardized response formatting and error handling.
"""

from flask import jsonify, Response
from typing import Optional, Dict, Any


def success_response(data: Optional[Dict[str, Any]] = None, message: Optional[str] = None) -> Response:
    """
    Create a standardized success response.
    
    Args:
        data: Optional data to include in response
        message: Optional success message
        
    Returns:
        JSON response
    """
    response = {"success": True}
    if message:
        response["message"] = message
    if data:
        response.update(data)
    return jsonify(response)


def error_response(error: str, status_code: int = 500) -> Response:
    """
    Create a standardized error response.
    
    Args:
        error: Error message
        status_code: HTTP status code
        
    Returns:
        JSON response with error status code
    """
    return jsonify({"error": error}), status_code


def not_found_response(resource: str = "Resource") -> Response:
    """
    Create a standardized 404 not found response.
    
    Args:
        resource: Resource name that was not found
        
    Returns:
        JSON response with 404 status code
    """
    return error_response(f"{resource} not found", 404)


def bad_request_response(message: str) -> Response:
    """
    Create a standardized 400 bad request response.
    
    Args:
        message: Error message
        
    Returns:
        JSON response with 400 status code
    """
    return error_response(message, 400)


def database_not_initialized_response() -> Response:
    """
    Create a standardized database not initialized response.
    
    Returns:
        JSON response with 500 status code
    """
    return error_response("Database not initialized", 500)
