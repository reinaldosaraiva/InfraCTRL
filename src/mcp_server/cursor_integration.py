"""Cursor IDE Integration for MCP Server using the mcp package."""

import logging
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Mount, Route

from mcp_server.adapters.registry import adapter_registry

logger = logging.getLogger(__name__)

# Create a FastMCP server
mcp_server = FastMCP("InfraCTRL")

# Set up tool functions that map to our adapter capabilities
@mcp_server.tool()
async def list_devices(device_type: str = None) -> str:
    """
    List devices from NetBox, optionally filtered by type.
    
    Args:
        device_type: Optional device type filter (e.g., "router", "switch")
        
    Returns:
        String representation of device list
    """
    # Get the adapter
    adapter = adapter_registry.get_adapter_instance("default-netbox")
    if not adapter:
        return "Error: NetBox adapter not found"
    
    # Execute the command
    from mcp_server.adapters.base import Command
    cmd = Command(
        capability="list_devices",
        parameters={"device_type": device_type} if device_type else {},
        resource_type="device",
    )
    
    try:
        result = await adapter.execute(cmd)
        if result.data:
            # Format the output as a table
            output = "Device List:\n"
            output += f"{'Name':<20} {'Type':<15} {'Manufacturer':<15} {'Site':<15} {'Status':<10}\n"
            output += "-" * 75 + "\n"
            
            for device in result.data:
                name = device.get('name', 'N/A')
                device_type = device.get('device_type', {}).get('model', 'N/A')
                manufacturer = device.get('device_type', {}).get('manufacturer', {}).get('name', 'N/A')
                site = device.get('site', {}).get('name', 'N/A')
                status = device.get('status', {}).get('value', 'N/A')
                
                output += f"{name:<20} {device_type:<15} {manufacturer:<15} {site:<15} {status:<10}\n"
                
            return output
        else:
            return "No devices found"
    except Exception as e:
        logger.error(f"Error executing list_devices: {str(e)}")
        return f"Error: {str(e)}"


@mcp_server.tool()
async def get_device(name: str) -> str:
    """
    Get detailed information about a specific device.
    
    Args:
        name: Name of the device to find
        
    Returns:
        String representation of device details
    """
    # Get the adapter
    adapter = adapter_registry.get_adapter_instance("default-netbox")
    if not adapter:
        return "Error: NetBox adapter not found"
    
    # Execute the command
    from mcp_server.adapters.base import Command
    cmd = Command(
        capability="get_device",
        parameters={"name": name},
        resource_type="device",
    )
    
    try:
        result = await adapter.execute(cmd)
        if result.data:
            device = result.data
            # Format the output as a detailed view
            output = f"Device: {device.get('name', 'N/A')}\n"
            output += "=" * 50 + "\n"
            output += f"Model: {device.get('device_type', {}).get('model', 'N/A')}\n"
            output += f"Manufacturer: {device.get('device_type', {}).get('manufacturer', {}).get('name', 'N/A')}\n"
            output += f"Serial: {device.get('serial', 'N/A')}\n"
            output += f"Site: {device.get('site', {}).get('name', 'N/A')}\n"
            output += f"Rack: {device.get('rack', {}).get('name', 'N/A') if device.get('rack') else 'N/A'}\n"
            output += f"Position: {device.get('position', 'N/A')}\n"
            output += f"Status: {device.get('status', {}).get('value', 'N/A')}\n"
            output += f"IP Address: {device.get('primary_ip', {}).get('address', 'N/A') if device.get('primary_ip') else 'N/A'}\n"
            
            return output
        else:
            return f"Device '{name}' not found"
    except Exception as e:
        logger.error(f"Error executing get_device: {str(e)}")
        return f"Error: {str(e)}"


@mcp_server.tool()
async def create_device(name: str, device_type: str, manufacturer: str, site_name: str) -> str:
    """
    Create a new device in NetBox.
    
    Args:
        name: Name of the new device
        device_type: Type of device (e.g., router, switch)
        manufacturer: Manufacturer of the device
        site_name: Site where the device is located
        
    Returns:
        String describing the result of the operation
    """
    # Get the adapter
    adapter = adapter_registry.get_adapter_instance("default-netbox")
    if not adapter:
        return "Error: NetBox adapter not found"
    
    # Execute the command
    from mcp_server.adapters.base import Command
    cmd = Command(
        capability="create_device",
        parameters={
            "name": name,
            "device_type": device_type,
            "manufacturer": manufacturer,
            "site_name": site_name,
            "status": "active"
        },
        resource_type="device",
    )
    
    try:
        result = await adapter.execute(cmd)
        if result.data:
            return f"Device '{name}' created successfully"
        else:
            return "Failed to create device"
    except Exception as e:
        logger.error(f"Error executing create_device: {str(e)}")
        return f"Error: {str(e)}"


def create_cursor_integration_app() -> Starlette:
    """
    Create a Starlette application for Cursor IDE integration.
    
    Returns:
        Starlette app that can be mounted in the main FastAPI app
    """
    transport = SseServerTransport("/messages/")
    
    # Define handler function
    async def handle_sse(request):
        async with transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await mcp_server._mcp_server.run(
                streams[0], streams[1], mcp_server._mcp_server.create_initialization_options()
            )
    
    # Create Starlette routes
    routes = [
        Route("/sse/", endpoint=handle_sse),
        Mount("/messages/", app=transport.handle_post_message),
    ]
    
    # Create a Starlette app
    return Starlette(routes=routes)