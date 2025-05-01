#!/usr/bin/env python3
"""
Simple MCP client to test connection to InfraCTRL MCP server.
"""

import asyncio
import os
import sys
from mcp.client import MCPClient, ClientSession

async def main():
    # Use the URL from command line or default to Cursor integration endpoint
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9000/cursor/sse"
    api_key = os.environ.get("MCP_API_KEY", "Kz_-Fpm1DsAmmThvj0KEkWcFgupDCkMc1MHSAmTWx0o")
    
    print(f"Connecting to MCP server at {url}...")
    
    # Create MCP client
    client = MCPClient(url, api_key=api_key)
    
    try:
        # Connect to server
        async with ClientSession(client) as session:
            print("Connected to MCP server!")
            
            # List available tools
            tools = await session.list_tools()
            if not tools:
                print("No tools available.")
                return
            
            print(f"Found {len(tools)} tools:")
            for tool in tools:
                print(f"- {tool.name}: {tool.description}")
                for param in tool.parameters:
                    print(f"  - {param.name}: {param.description} (Required: {param.required})")
            
            # Test calling a tool if available
            if any(tool.name == "list_devices" for tool in tools):
                print("\nTesting list_devices tool...")
                try:
                    result = await session.call_tool("list_devices")
                    print("Result:")
                    print(result)
                except Exception as e:
                    print(f"Error calling list_devices: {e}")
    except Exception as e:
        print(f"Error connecting to MCP server: {e}")

if __name__ == "__main__":
    asyncio.run(main())