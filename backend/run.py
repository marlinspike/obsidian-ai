#!/usr/bin/env python3
"""Run the Obsidian AI backend server with configuration from .env."""

import uvicorn

from app.config import get_settings


def main() -> None:
    """Start the server with configured settings."""
    settings = get_settings()

    print(f"Starting Obsidian AI Backend on {settings.backend_host}:{settings.backend_port}")
    print(f"Notes path: {settings.notes_path}")
    print(f"Configured providers: {settings.get_configured_providers()}")

    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
