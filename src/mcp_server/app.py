"""Main application for MCP Server."""

import os
import logging
from typing import Dict, List, Optional, Any, Union

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from mcp_server.api.routes import router as api_router
from mcp_server.adapters.registry import adapter_registry
from mcp_server.adapters.netbox import NetBoxAdapter
from mcp_server.auth.api_key import api_key_service
from mcp_server.cursor_integration import create_cursor_integration_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_server")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    # Create FastAPI app
    app = FastAPI(
        title="MCP Server",
        description="Multi-tool Control Platform Server for infrastructure management",
        version="0.1.0",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # For development, restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API router
    app.include_router(api_router)
    
    # Mount Cursor IDE integration app
    cursor_app = create_cursor_integration_app()
    app.mount("/cursor", cursor_app)
    
    # Add direct route for debugging tools list
    @app.get("/debug-tools")
    async def debug_tools_list():
        """Debug endpoint to check available MCP tools."""
        from mcp_server.cursor_integration import mcp_server
        tools = await mcp_server.list_tools()
        return {"tools": [t.model_dump() for t in tools]}
    
    # Register built-in adapters
    adapter_registry.register_adapter_class("netbox", NetBoxAdapter)
    
    # Add startup event to initialize adapters from config
    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting MCP Server")
        
        # Create a default NetBox adapter if environment variables are available
        netbox_api_url = os.environ.get("NETBOX_API_URL")
        netbox_api_token = os.environ.get("NETBOX_API_TOKEN")
        netbox_simulation = os.environ.get("NETBOX_SIMULATION_MODE", "false").lower() == "true"
        
        if netbox_api_url or netbox_simulation:
            # Create a default NetBox adapter
            config = {
                "api_url": netbox_api_url or "http://localhost:8000/api",
                "api_token": netbox_api_token or "dummy_token",
                "simulation_mode": netbox_simulation,
            }
            
            # Register adapter
            adapter = adapter_registry.create_adapter_instance(
                "netbox",
                "default-netbox",
                config,
            )
            
            if adapter:
                logger.info("Created default NetBox adapter")
                try:
                    # Connect to NetBox
                    connected = await adapter.connect()
                    if connected:
                        logger.info("Connected to NetBox")
                    else:
                        logger.warning("Failed to connect to NetBox")
                except Exception as e:
                    logger.error(f"Error connecting to NetBox: {e}")
    
    # Add shutdown event to clean up resources
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down MCP Server")
        
        # Disconnect all adapters
        for name, adapter in adapter_registry.get_all_adapter_instances().items():
            try:
                await adapter.disconnect()
                logger.info(f"Disconnected adapter: {name}")
            except Exception as e:
                logger.error(f"Error disconnecting adapter {name}: {e}")
    
    # Add exception handler for generic exceptions
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error", "detail": str(exc)},
        )
    
    return app


# Create app instance
app = create_app()