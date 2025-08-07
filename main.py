#!/usr/bin/env python3
"""
JEECG A2A Platform - Main Entry Point

A complete A2A (Agent-to-Agent) protocol platform implementation.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

import click
import uvicorn
from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from core.platform import A2APlatform

# Load environment variables
load_dotenv()

# Setup rich console for beautiful output
console = Console()

# Configure logging with rich handler
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)

logger = logging.getLogger(__name__)


def setup_logging():
    """Configure logging for the application."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def start_server(host: str = None, port: int = None, reload: bool = False, debug: bool = False):
    """Start the JEECG A2A Platform server."""

    # Setup logging
    setup_logging()

    # Load settings
    settings = Settings()

    # Override settings with parameters
    if host:
        settings.HOST = host
    if port:
        settings.PORT = port
    if debug:
        settings.DEBUG = True

    # Display startup banner
    console.print("\n[bold blue]🚀 JEECG A2A Platform[/bold blue]", justify="center")
    console.print(f"[green]Version: {settings.PLATFORM_VERSION}[/green]", justify="center")
    console.print(f"[yellow]Starting server on {settings.HOST}:{settings.PORT}[/yellow]", justify="center")
    console.print()

    # Log configuration
    logger.info(f"Platform Name: {settings.PLATFORM_NAME}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info(f"Max Concurrent Tasks: {settings.MAX_CONCURRENT_TASKS}")
    logger.info(f"Agent Timeout: {settings.AGENT_TIMEOUT}s")

    try:
        # Run the server
        uvicorn.run(
            "api.app:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=reload or settings.DEBUG,
            log_level=settings.LOG_LEVEL.lower(),
            access_log=True,
            server_header=False,
            date_header=False,
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Shutting down gracefully...[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Error starting server: {e}[/red]")
        sys.exit(1)


@click.command()
@click.option("--host", default=None, help="Host to bind to")
@click.option("--port", default=None, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
@click.option("--debug", is_flag=True, help="Enable debug mode")
def main(host: str, port: int, reload: bool, debug: bool):
    """Start the JEECG A2A Platform."""
    start_server(host=host, port=port, reload=reload, debug=debug)


@click.group()
def cli():
    """JEECG A2A Platform CLI."""
    pass


# Add the main command to the CLI group
cli.add_command(main, name="start")


@cli.command()
def init():
    """Initialize the platform database and configuration."""
    console.print("[blue]🔧 Initializing JEECG A2A Platform...[/blue]")
    
    # Create necessary directories
    directories = [
        "logs",
        "data",
        "uploads",
        "static/uploads"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        console.print(f"✅ Created directory: {directory}")
    
    # Copy environment file if it doesn't exist
    if not Path(".env").exists():
        if Path(".env.example").exists():
            import shutil
            shutil.copy(".env.example", ".env")
            console.print("✅ Created .env file from .env.example")
        else:
            console.print("[yellow]⚠️  .env.example not found, please create .env manually[/yellow]")
    
    console.print("[green]✅ Platform initialized successfully![/green]")
    console.print("[yellow]📝 Please edit .env file with your configuration[/yellow]")


@cli.command()
def health():
    """Check platform health."""
    import httpx
    
    settings = Settings()
    url = f"http://{settings.HOST}:{settings.PORT}/health"
    
    try:
        response = httpx.get(url, timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            console.print("[green]✅ Platform is healthy[/green]")
            console.print(f"Status: {data.get('status')}")
            console.print(f"Version: {data.get('version')}")
        else:
            console.print(f"[red]❌ Health check failed: {response.status_code}[/red]")
    except Exception as e:
        console.print(f"[red]❌ Cannot connect to platform: {e}[/red]")


if __name__ == "__main__":
    # If called directly, run the main server
    if len(sys.argv) == 1:
        start_server()
    else:
        # Otherwise, use the CLI
        cli()
