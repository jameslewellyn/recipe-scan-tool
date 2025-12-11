#!/usr/bin/env python3
"""
Main entry point for the notecard extractor CLI.
Sets up and wires together all Typer applications.
"""

import typer
from notecard_extractor.pdf_extractor import extract_notecards
from notecard_extractor.border_removers import (
    white_border_remover,
    grey_border_remover,
)

# Main app for extract-notecards command
app = typer.Typer()
app.command()(extract_notecards)

# Separate app for white-border-remover command
white_border_remover_app = typer.Typer()
white_border_remover_app.command()(white_border_remover)

# Separate app for grey-border-remover command
grey_border_remover_app = typer.Typer()
grey_border_remover_app.command()(grey_border_remover)


if __name__ == "__main__":
    app()
