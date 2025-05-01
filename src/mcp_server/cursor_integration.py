"""Cursor IDE integration for MCP Server.

This module provides integration with Cursor IDE using MCP (Multi-tool Control
Platform) protocol. It defines tools that can be used by Cursor IDE and creates
a Starlette application that serves as an endpoint for Cursor IDE to connect to.
"""

import logging
import asyncio
import json
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from mcp_server.adapters.registry import adapter_registry

logger = logging.getLogger(__name__)

# Create MCP server instance and register tools
mcp_server = FastMCP("InfraCTRL")
logger.info("FastMCP instance 'mcp_server' created.")

@mcp_server.tool()
async def list_devices(device_type: str = None) -> str:
    """List devices from NetBox."""
    logger.info(f"Tool 'list_devices' called with type: {device_type}")
    adapter = adapter_registry.get_adapter_instance("default-netbox")
    
    if not adapter:
        return "Error: NetBox adapter not found"
    
    from mcp_server.adapters.base import Command
    cmd = Command(
        capability="list_devices",
        parameters={"device_type": device_type} if device_type else {},
        resource_type="device"
    )
    
    try:
        result = await adapter.execute(cmd)
        if result and result.data:
            output = "Device List:\n"
            output += f"{'Name':<20} {'Type':<15} {'Manufacturer':<15} {'Site':<15} {'Status':<10}\n"
            output += "-" * 75 + "\n"
            
            for device in result.data:
                name = device.get('name', 'N/A')
                dt = device.get('device_type', {}).get('model', 'N/A')
                mfg = device.get('device_type', {}).get('manufacturer', {}).get('name', 'N/A')
                site = device.get('site', {}).get('name', 'N/A')
                status = device.get('status', {}).get('value', 'N/A')
                output += f"{name:<20} {dt:<15} {mfg:<15} {site:<15} {status:<10}\n"
            
            return output
        else:
            return "No devices found"
    except Exception as e:
        logger.error(f"Tool 'list_devices' Error: {e}", exc_info=True)
        return f"Error: {str(e)}"

@mcp_server.tool()
async def get_device(name: str) -> str:
    """Get detailed information about a specific device."""
    logger.info(f"Tool 'get_device' called for: {name}")
    adapter = adapter_registry.get_adapter_instance("default-netbox")
    
    if not adapter:
        return "Error: NetBox adapter not found"
    
    from mcp_server.adapters.base import Command
    cmd = Command(
        capability="get_device", 
        parameters={"name": name}, 
        resource_type="device"
    )
    
    try:
        result = await adapter.execute(cmd)
        if result and result.data:
            device = result.data
            output = f"Device: {device.get('name', 'N/A')}\n"
            output += "=" * 50 + "\n"
            output += f"Model: {device.get('device_type', {}).get('model', 'N/A')}\n"
            output += f"Manufacturer: {device.get('device_type', {}).get('manufacturer', {}).get('name', 'N/A')}\n"
            output += f"Serial: {device.get('serial', 'N/A')}\n"
            output += f"Site: {device.get('site', {}).get('name', 'N/A')}\n"
            output += f"Rack: {device.get('rack', {}).get('name', 'N/A')}\n"
            output += f"Position: {device.get('position', 'N/A')}\n"
            output += f"Status: {device.get('status', {}).get('value', 'N/A')}\n"
            output += f"IP Address: {device.get('primary_ip', {}).get('address', 'N/A')}\n"
            return output
        else:
            return f"Device '{name}' not found"
    except Exception as e:
        logger.error(f"Tool 'get_device' Error: {e}", exc_info=True)
        return f"Error: {str(e)}"

@mcp_server.tool()
async def create_device(name: str, device_type: str, manufacturer: str, site_name: str) -> str:
    """Create a new device in NetBox."""
    logger.info(f"Tool 'create_device' called for: {name}")
    adapter = adapter_registry.get_adapter_instance("default-netbox")
    
    if not adapter:
        return "Error: NetBox adapter not found"
    
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
        resource_type="device"
    )
    
    try:
        result = await adapter.execute(cmd)
        
        if result and getattr(result, 'success', False):
            device_id = result.data.get('id', 'UNKNOWN') if result.data else 'UNKNOWN'
            return f"Device '{name}' created successfully with ID: {device_id}"
        elif result and getattr(result, 'error_message', None):
            error_msg = result.error_message
            logger.error(f"Failed to create device '{name}': {error_msg}")
            return f"Failed to create device: {error_msg}"
        else:
            logger.error(f"Failed to create device '{name}' - Unknown error.")
            return "Failed to create device (unknown reason)"
    except Exception as e:
        logger.error(f"Tool 'create_device' Error: {e}", exc_info=True)
        return f"Error creating device: {str(e)}"

logger.info("Tools registered on mcp_server.")

# Create SSE transport for Cursor IDE integration
transport = SseServerTransport("messages")
logger.info("Created SSE transport for Cursor IDE integration")

# Main function to create Starlette app
def create_cursor_integration_app() -> Starlette:
    """
    Create a Starlette application for Cursor IDE integration.
    
    Returns:
        Starlette: A configured Starlette application with routes for Cursor IDE integration
    """
    async def root_handler(request: Request):
        """Provide basic info about the integration."""
        logger.info(f"Handling root request from {request.client.host}:{request.client.port} for {request.url.path}")
        return JSONResponse({
            "name": "InfraCTRL Cursor IDE Integration",
            "version": "0.1.0",
            "endpoints": ["/sse/", "/cursor/sse/", "/messages"],
            "description": "Cursor IDE integration using MCP"
        })

    async def sse_handler(request: Request):
        """
        Handle SSE connections for Cursor IDE integration.
        """
        logger.info(f"New SSE connection from {request.client.host}:{request.client.port} for {request.url.path}")

        async def event_generator():
            logger.info(f"Starting SSE event generator for {request.client.host}:{request.client.port}")
            try:
                # Enviar evento inicial de conexão
                yield {"event": "connected", "data": {"status": "ok"}}
                logger.info(f"Sent connected event to {request.client.host}:{request.client.port}")

                # Enviar notificação de inicialização
                options = {
                    "serverInfo": {
                        "name": "InfraCTRL MCP Server",
                        "version": "0.1.0"
                    }
                }
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": options
                    })
                }
                logger.info(f"Sent initialize notification to {request.client.host}:{request.client.port}")

                # Enviar notificação com as ferramentas disponíveis
                tools = await mcp_server.list_tools()
                tool_dicts = []
                for tool in tools:
                    try:
                        tool_dict = tool.model_dump()
                    except AttributeError:
                        tool_dict = tool.__dict__
                        if "_sa_instance_state" in tool_dict:
                            del tool_dict["_sa_instance_state"]
                    tool_dicts.append(tool_dict)

                yield {
                    "event": "message",
                    "data": json.dumps({
                        "jsonrpc": "2.0",
                        "method": "capabilities",
                        "params": {
                            "tools": tool_dicts
                        }
                    })
                }
                logger.info(f"Sent capabilities notification to {request.client.host}:{request.client.port}")

                # Manter conexão viva com pings
                while True:
                    await asyncio.sleep(10)
                    yield {"event": "ping", "data": {}}
                    logger.info(f"Sent ping event to {request.client.host}:{request.client.port}")

            except Exception as e:
                logger.error(f"SSE event generator error for {request.client.host}:{request.client.port}: {e}", exc_info=True)
                yield {"event": "error", "data": {"error": str(e)}}
            finally:
                logger.info(f"SSE connection closed for {request.client.host}:{request.client.port}")

        headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }

        # Usar EventSourceResponse diretamente com o gerador de eventos
        return EventSourceResponse(event_generator(), media_type="text/event-stream", headers=headers)

    async def message_handler(request: Request):
        """Handle POST messages for MCP."""
        logger.info(f"Received POST request from {request.client.host}:{request.client.port}")
        try:
            body = await request.json()
            logger.info(f"Request body: {body}")

            message_id = body.get("id")
            method = body.get("method")

            if method == "initialize":
                tools = await mcp_server.list_tools()
                tool_dicts = []
                for tool in tools:
                    try:
                        tool_dict = tool.model_dump()
                    except AttributeError:
                        tool_dict = tool.__dict__
                        if "_sa_instance_state" in tool_dict:
                            del tool_dict["_sa_instance_state"]
                    tool_dicts.append(tool_dict)

                response = {
                    "jsonrpc": "2.0",
                    "result": {
                        "capabilities": {
                            "tools": tool_dicts
                        },
                        "serverInfo": {
                            "name": "InfraCTRL MCP Server",
                            "version": "0.1.0"
                        }
                    },
                    "id": message_id
                }
                logger.info(f"Sending initialize response: {response}")
                return JSONResponse(response)

            result = await mcp_server.handle_json_rpc(body)
            try:
                json_str = json.dumps(result)
                response = json.loads(json_str)
            except (TypeError, json.JSONDecodeError) as e:
                logger.error(f"Result not JSON serializable: {e}")
                response = {
                    "jsonrpc": "2.0",
                    "result": str(result),
                    "id": message_id
                }

            logger.info(f"Sending response: {response}")
            return JSONResponse(response)

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": str(e)},
                    "id": body.get("id") if "body" in locals() else None
                },
                status_code=500
            )

    # --- Define as Rotas ---
    routes = [
        Route("/", endpoint=root_handler),
        Route("/sse/", endpoint=sse_handler),
        Route("/cursor/sse/", endpoint=sse_handler),  # Adicionado para suportar a URL usada pelo Cursor IDE
        Route("/messages", endpoint=message_handler, methods=["POST"]),
    ]

    logger.info("Creating Starlette app for Cursor integration.")
    app = Starlette(routes=routes)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Ajuste para origens específicas em produção
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app

# ============================================================
# Fim do arquivo cursor_integration.py
# ============================================================