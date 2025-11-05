"""
Initialize the Flask application package.
This file allows the /app directory to be treated as a Python module.
"""

from .app import app

__all__ = ["app"]
