"""Command-line interface for MCP Server."""

import os
import sys
import argparse
import asyncio
import uvicorn
import dotenv
from typing import Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

# Initialize console
console = Console()


def main():
    """Main entry point for MCP Server CLI."""
    # Load environment variables from .env file
    dotenv.load_dotenv()
    
    # Create argument parser
    parser = argparse.ArgumentParser(
        description="MCP Server - Multi-tool Control Platform Server for infrastructure management",
    )
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Server command
    server_parser = subparsers.add_parser("serve", help="Start the API server")
    server_parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="Host to bind to",
    )
    server_parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to",
    )
    server_parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload",
    )
    
    # Key command
    key_parser = subparsers.add_parser("key", help="API key management")
    key_subparsers = key_parser.add_subparsers(dest="key_command", help="Key management command")
    
    # Create key command
    create_key_parser = key_subparsers.add_parser("create", help="Create a new API key")
    create_key_parser.add_argument(
        "name", type=str, help="Name for the API key",
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle commands
    if args.command == "serve":
        run_server(args.host, args.port, args.reload)
    elif args.command == "key":
        if args.key_command == "create":
            create_api_key(args.name)
        else:
            key_parser.print_help()
    else:
        # Show welcome message and help
        show_welcome()
        parser.print_help()


def run_server(host: str, port: int, reload: bool):
    """
    Start the API server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Whether to enable auto-reload
    """
    console.print(Panel.fit(
        "[bold cyan]MCP Server[/]\n"
        "Multi-tool Control Platform Server for infrastructure management",
        title="Starting Server"
    ))
    
    # Check for admin API key
    if not os.environ.get("ADMIN_API_KEY"):
        # Generate a random key
        import secrets
        admin_key = secrets.token_urlsafe(32)
        os.environ["ADMIN_API_KEY"] = admin_key
        console.print("[bold yellow]Warning:[/] No ADMIN_API_KEY found in environment")
        console.print(f"[bold green]Generated admin API key:[/] {admin_key}")
        console.print("Use this key in the X-API-Key header for API requests\n")
    
    # Run server
    console.print(f"[bold]Server running at:[/] http://{host}:{port}")
    console.print("Press CTRL+C to stop the server\n")
    
    # Start Uvicorn
    uvicorn.run(
        "mcp_server.app:app",
        host=host,
        port=port,
        reload=reload,
    )


def create_api_key(name: str):
    """
    Create a new API key.
    
    Args:
        name: Name for the API key
    """
    # Import here to avoid circular imports
    from mcp_server.auth.api_key import api_key_service
    
    # Create key
    key = api_key_service.create_key(name)
    
    console.print(Panel.fit(
        f"[bold]Name:[/] {key['name']}\n"
        f"[bold]ID:[/] {key['id']}\n"
        f"[bold]Key:[/] [bold green]{key['key']}[/]\n"
        f"[bold]Prefix:[/] {key['prefix']}\n"
        f"[bold]Created:[/] {key['created_at']}\n\n"
        "[bold yellow]WARNING:[/] This key will only be shown once. Store it securely.",
        title="New API Key Created"
    ))


def show_welcome():
    """Show welcome message."""
    console.print(Panel.fit(
        "[bold cyan]MCP Server[/]\n"
        "Multi-tool Control Platform Server for infrastructure management",
        title="Welcome"
    ))
    
    console.print(Markdown("""
    ## Available Commands

    - `mcp-server serve` - Start the API server
    - `mcp-server key create <name>` - Create a new API key

    ## Environment Variables

    - `ADMIN_API_KEY` - Admin API key for authentication
    - `NETBOX_API_URL` - NetBox API URL (for default adapter)
    - `NETBOX_API_TOKEN` - NetBox API token (for default adapter)
    - `NETBOX_SIMULATION_MODE` - Use simulation mode (true/false)
    """))


if __name__ == "__main__":
    main()