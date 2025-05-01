"""API routes for MCP Server."""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from fastapi.security import APIKeyHeader
from fastapi.responses import StreamingResponse
import asyncio
import json

from mcp_server.adapters.registry import adapter_registry
from mcp_server.adapters.base import Command, CommandResult, CommandStatus
from mcp_server.api.models import (
    AdapterInfo,
    AdapterConfig,
    AdapterConfigSchema,
    CommandRequest,
    CommandResponse,
    ApiKeyCreate,
    ApiKeyResponse,
    ApiKeyInfo,
    ErrorResponse,
)
from mcp_server.auth.api_key import api_key_service, get_api_key

logger = logging.getLogger(__name__)

# Create routers
router = APIRouter(prefix="/api/v1")
adapters_router = APIRouter(prefix="/adapters", tags=["adapters"])
commands_router = APIRouter(prefix="/commands", tags=["commands"])
auth_router = APIRouter(prefix="/auth", tags=["auth"])
tools_router = APIRouter(prefix="/tools", tags=["tools"])
sse_router = APIRouter(prefix="/sse", tags=["sse"])


# Adapter routes
@adapters_router.get(
    "/",
    response_model=List[AdapterInfo],
    summary="List all adapters",
)
async def list_adapters(
    api_key: str = Depends(get_api_key),
):
    """
    List all registered adapter instances.
    """
    adapter_instances = adapter_registry.get_all_adapter_instances()
    result = []
    
    for name, adapter in adapter_instances.items():
        # Get connection status
        connected = False
        try:
            connected = await adapter.test_connection()
        except Exception as e:
            logger.error(f"Error testing connection for adapter {name}: {e}")
        
        result.append({
            "name": name,
            "type": adapter.__class__.__name__,
            "capabilities": [c.to_dict() for c in adapter.capabilities],
            "status": "ready" if connected else "error",
            "connected": connected,
        })
    
    return result


@adapters_router.get(
    "/types",
    response_model=List[str],
    summary="List available adapter types",
)
async def list_adapter_types(
    api_key: str = Depends(get_api_key),
):
    """
    List all available adapter types.
    """
    return adapter_registry.get_available_adapter_types()


@adapters_router.get(
    "/{name}",
    response_model=AdapterInfo,
    summary="Get adapter information",
)
async def get_adapter(
    name: str = Path(..., description="Adapter instance name"),
    api_key: str = Depends(get_api_key),
):
    """
    Get information about a specific adapter instance.
    """
    adapter = adapter_registry.get_adapter_instance(name)
    if not adapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Adapter not found: {name}",
        )
    
    # Get connection status
    connected = False
    try:
        connected = await adapter.test_connection()
    except Exception as e:
        logger.error(f"Error testing connection for adapter {name}: {e}")
    
    return {
        "name": name,
        "type": adapter.__class__.__name__,
        "capabilities": [c.to_dict() for c in adapter.capabilities],
        "status": "ready" if connected else "error",
        "connected": connected,
    }


@adapters_router.get(
    "/types/{adapter_type}/schema",
    response_model=AdapterConfigSchema,
    summary="Get adapter configuration schema",
)
async def get_adapter_config_schema(
    adapter_type: str = Path(..., description="Adapter type"),
    api_key: str = Depends(get_api_key),
):
    """
    Get the configuration schema for an adapter type.
    """
    adapter_class = adapter_registry.get_adapter_class(adapter_type)
    if not adapter_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Adapter type not found: {adapter_type}",
        )
    
    # Create temporary instance to get schema
    temp_adapter = adapter_class("temp", {})
    schema = temp_adapter.get_config_schema()
    
    return {
        "properties": schema["properties"],
        "required": schema["required"],
    }


@adapters_router.post(
    "/",
    response_model=AdapterInfo,
    status_code=status.HTTP_201_CREATED,
    summary="Create adapter instance",
)
async def create_adapter(
    adapter_config: AdapterConfig,
    api_key: str = Depends(get_api_key),
):
    """
    Create a new adapter instance.
    """
    # Check if adapter type exists
    adapter_type = adapter_config.type
    adapter_class = adapter_registry.get_adapter_class(adapter_type)
    if not adapter_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Adapter type not found: {adapter_type}",
        )
    
    # Check if name is already used
    name = adapter_config.name
    if adapter_registry.get_adapter_instance(name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Adapter name already in use: {name}",
        )
    
    # Create adapter instance
    adapter = adapter_registry.create_adapter_instance(
        adapter_type,
        name,
        adapter_config.config,
    )
    
    if not adapter:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create adapter instance",
        )
    
    # Connect and return
    connected = False
    try:
        connected = await adapter.connect()
    except Exception as e:
        logger.error(f"Error connecting to adapter {name}: {e}")
    
    return {
        "name": name,
        "type": adapter_type,
        "capabilities": [c.to_dict() for c in adapter.capabilities],
        "status": "ready" if connected else "error",
        "connected": connected,
    }


@adapters_router.delete(
    "/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete adapter instance",
)
async def delete_adapter(
    name: str = Path(..., description="Adapter instance name"),
    api_key: str = Depends(get_api_key),
):
    """
    Delete an adapter instance.
    """
    adapter = adapter_registry.get_adapter_instance(name)
    if not adapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Adapter not found: {name}",
        )
    
    # Disconnect
    try:
        await adapter.disconnect()
    except Exception as e:
        logger.error(f"Error disconnecting adapter {name}: {e}")
    
    # Remove from registry
    adapter_registry.remove_adapter_instance(name)
    
    return None


# Command routes
@commands_router.post(
    "/",
    response_model=CommandResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Execute command",
)
async def execute_command(
    command: CommandRequest,
    api_key: str = Depends(get_api_key),
):
    """
    Execute a command on an adapter.
    """
    # Get adapter
    adapter_name = command.adapter
    adapter = adapter_registry.get_adapter_instance(adapter_name)
    if not adapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Adapter not found: {adapter_name}",
        )
    
    # Check if adapter supports capability
    capability = command.capability
    if not adapter.has_capability(capability):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Adapter {adapter_name} does not support capability: {capability}",
        )
    
    # Create command
    cmd = Command(
        capability=capability,
        parameters=command.parameters,
        resource_type=command.resource_type,
        resource_id=command.resource_id,
    )
    
    # Execute command
    try:
        result = await adapter.execute(cmd)
    except Exception as e:
        logger.error(f"Error executing command on adapter {adapter_name}: {e}")
        result = CommandResult(
            status=CommandStatus.FAILED,
            error=f"Error executing command: {str(e)}",
        )
    
    # Create response
    now = datetime.utcnow()
    return {
        "id": str(uuid.uuid4()),
        "adapter": adapter_name,
        "capability": capability,
        "status": result.status.value,
        "data": result.data,
        "message": result.message,
        "error": result.error,
        "created_at": now,
        "updated_at": now,
    }


# Auth routes
@auth_router.get(
    "/api-keys",
    response_model=List[ApiKeyInfo],
    summary="List API keys",
)
def list_api_keys(
    api_key: str = Depends(get_api_key),
):
    """
    List all API keys.
    """
    keys = api_key_service.list_keys()
    return keys


@auth_router.post(
    "/api-keys",
    response_model=ApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create API key",
)
def create_api_key(
    key_info: ApiKeyCreate,
    api_key: str = Depends(get_api_key),
):
    """
    Create a new API key.
    """
    key = api_key_service.create_key(key_info.name)
    return key


@auth_router.delete(
    "/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete API key",
)
def delete_api_key(
    key_id: str = Path(..., description="API key ID"),
    api_key: str = Depends(get_api_key),
):
    """
    Delete an API key.
    """
    if not api_key_service.delete_key(key_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key not found: {key_id}",
        )
    return None


# Root API endpoint
@router.get(
    "/",
    summary="API Root",
)
async def api_root(
    api_key: str = Depends(get_api_key),
):
    """
    API root information.
    """
    return {
        "name": "MCP Server API",
        "version": "0.1.0",
        "endpoints": [
            "/adapters",
            "/commands",
            "/auth/api-keys",
            "/tools",
            "/sse"
        ]
    }

# Tools routes
@tools_router.get(
    "/",
    response_model=ToolsResponse,
    summary="List available tools",
)
async def list_tools(
    api_key: str = Depends(get_api_key),
):
    """
    List all available tools that can be used with this MCP Server.
    """
    # Convert capabilities from adapters to tools format expected by Cursor
    tools = []
    adapter_instances = adapter_registry.get_all_adapter_instances()
    
    for name, adapter in adapter_instances.items():
        for capability in adapter.capabilities:
            # Create tool parameters from capability parameters
            parameters = []
            try:
                for param_name, param_info in capability.parameters.items():
                    if not isinstance(param_info, dict):
                        logger.warning(f"Parameter {param_name} is not a dict: {param_info}")
                        continue  # Skip non-dict parameters
                        
                    parameters.append({
                        "name": param_name,
                        "type": param_info.get("type", "string"),
                        "description": param_info.get("description", ""),
                        "required": param_info.get("required", False),
                        "default": param_info.get("default")
                    })
            except Exception as e:
                logger.error(f"Error processing parameters for capability {capability.name}: {str(e)}")
                parameters = []  # Reset parameters on error
            
            # Add tool based on capability
            tools.append({
                "name": f"{name}.{capability.name}",
                "description": capability.description,
                "parameters": parameters
            })
    
    return {"tools": tools}


@tools_router.post(
    "/execute",
    response_model=CommandResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Execute a tool",
)
async def execute_tool(
    request: Request,
    api_key: str = Depends(get_api_key),
):
    """
    Execute a tool with the provided parameters.
    """
    # Parse request body
    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request body: {str(e)}",
        )
    
    # Extract tool name and parameters
    tool_name = body.get("name", "")
    if not tool_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tool name is required",
        )
    
    # Parse adapter name and capability from tool name
    parts = tool_name.split(".", 1)
    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tool name format: {tool_name}. Expected format: adapter_name.capability_name",
        )
    
    adapter_name, capability_name = parts
    
    # Get adapter
    adapter = adapter_registry.get_adapter_instance(adapter_name)
    if not adapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Adapter not found: {adapter_name}",
        )
    
    # Check if adapter supports capability
    if not adapter.has_capability(capability_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Adapter {adapter_name} does not support capability: {capability_name}",
        )
    
    # Extract parameters
    params = body.get("parameters", {})
    
    # Create command
    cmd = Command(
        capability=capability_name,
        parameters=params,
        resource_type=body.get("resource_type"),
        resource_id=body.get("resource_id"),
    )
    
    # Execute command
    try:
        result = await adapter.execute(cmd)
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        result = CommandResult(
            status=CommandStatus.FAILED,
            error=f"Error executing tool: {str(e)}",
        )
    
    # Create response
    now = datetime.utcnow()
    return {
        "id": str(uuid.uuid4()),
        "adapter": adapter_name,
        "capability": capability_name,
        "status": result.status.value,
        "data": result.data,
        "message": result.message,
        "error": result.error,
        "created_at": now,
        "updated_at": now,
    }

# SSE endpoint for real-time events
async def sse_event_generator():
    """Generate SSE events."""
    try:
        # Send initial connected event
        yield f"event: connected\ndata: {json.dumps({})}\n\n"
        
        # Keep connection alive with heartbeat events
        count = 0
        while count < 10:  # Limit to prevent infinite loops
            await asyncio.sleep(30)
            yield f"event: heartbeat\ndata: {json.dumps({})}\n\n"
            count += 1
            
    except Exception as e:
        logger.error(f"Error in SSE generator: {str(e)}")
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    finally:
        logger.info("SSE connection closed")
        yield f"event: disconnect\ndata: {json.dumps({})}\n\n"

@sse_router.get(
    "/",
    summary="SSE endpoint for real-time events",
)
async def sse_endpoint(
    request: Request,
    api_key: str = Depends(get_api_key),
):
    """
    Server-Sent Events (SSE) endpoint for real-time events.
    """
    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

# Add sub-routers to main router
router.include_router(adapters_router)
router.include_router(commands_router)
router.include_router(auth_router)
router.include_router(tools_router)
router.include_router(sse_router)