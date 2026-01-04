#!/usr/bin/env python3
"""
Web GUI for the notecard extractor tool.
Provides a browser-based interface for uploading PDF files and storing them in the database.
"""

from flask import Flask
from pathlib import Path
from typing import Annotated
import typer
from sqlmodel import SQLModel, create_engine
from notecard_extractor.utils.db_utils import set_db_engine
from notecard_extractor.api.routes import register_routes
from notecard_extractor.config import DEFAULT_DATABASE_PATH
# Import database models to register them with SQLModel
from notecard_extractor.database import Recipe, RecipeImage, DishImage, RecipeTagList, RecipeTag

# Get the directory where this module is located
BASE_DIR = Path(__file__).parent

flask_app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
    static_url_path="/static"
)
app = typer.Typer()

# Register all routes
register_routes(flask_app)


@app.command()
def run_server(
    host: Annotated[
        str | None, typer.Argument(help="Host to bind the server to")
    ] = "127.0.0.1",
    port: Annotated[int, typer.Argument(help="Port to bind the server to")] = 5000,
    debug: Annotated[
        bool, typer.Option("--debug", "-d", help="Enable debug mode")
    ] = False,
    database: Annotated[
        Path | None,
        typer.Option("--database", "-db", help="Path to SQLite database file"),
    ] = DEFAULT_DATABASE_PATH,
):
    """Run the Flask development server."""
    # Initialize database if path provided
    # Create parent directory if it doesn't exist
    database.parent.mkdir(parents=True, exist_ok=True)

    # Create database URL
    db_url = f"sqlite:///{database}"
    db_engine = create_engine(db_url, echo=debug)
    
    # Set the global database engine for use in handlers
    set_db_engine(db_engine)

    # Create all tables (Recipe model is imported above, so it's registered)
    SQLModel.metadata.create_all(db_engine)

    typer.echo(f"Database initialized at: {database}")

    typer.echo(f"Starting web server at http://{host}:{port}")
    typer.echo("Press Ctrl+C to stop the server")
    flask_app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    app()
