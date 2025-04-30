"""NetBox adapter for MCP Server."""

import os
import requests
import logging
from typing import Dict, List, Optional, Any, Union
import asyncio

from mcp_server.adapters.base import (
    ToolAdapter, 
    Capability, 
    CapabilityType, 
    Command, 
    CommandResult,
    CommandStatus
)

logger = logging.getLogger(__name__)


class NetBoxAdapter(ToolAdapter):
    """Adapter for interacting with NetBox API."""
    
    # Default capabilities
    DEFAULT_CAPABILITIES = [
        Capability(
            name="list_devices",
            description="List devices from NetBox, optionally filtered by type",
            capability_type=CapabilityType.READ,
            resource_types=["device"],
            parameters={
                "limit": {
                    "type": "integer",
                    "default": 100,
                    "description": "Maximum number of devices to return",
                },
                "offset": {
                    "type": "integer",
                    "default": 0,
                    "description": "Pagination offset",
                },
                "device_type": {
                    "type": "string",
                    "default": None,
                    "description": "Filter by device type",
                },
            },
        ),
        Capability(
            name="get_device",
            description="Get a specific device by name or ID",
            capability_type=CapabilityType.READ,
            resource_types=["device"],
            parameters={
                "name": {
                    "type": "string",
                    "description": "Device name to look up",
                },
                "id": {
                    "type": "integer",
                    "description": "Device ID to look up",
                },
            },
        ),
        Capability(
            name="create_device",
            description="Create a new device in NetBox",
            capability_type=CapabilityType.CREATE,
            resource_types=["device"],
            parameters={
                "name": {
                    "type": "string",
                    "description": "Name of the new device",
                    "required": True,
                },
                "device_type": {
                    "type": "string",
                    "description": "Device type/model",
                    "required": True,
                },
                "manufacturer": {
                    "type": "string",
                    "description": "Device manufacturer",
                    "required": True,
                },
                "site_name": {
                    "type": "string",
                    "description": "Location where the device is installed",
                    "required": True,
                },
                "status": {
                    "type": "string",
                    "description": "Device status (active, offline, planned, etc.)",
                    "default": "active",
                },
                "serial": {
                    "type": "string",
                    "description": "Device serial number",
                },
                "rack": {
                    "type": "string",
                    "description": "Rack name where installed",
                },
                "position": {
                    "type": "integer",
                    "description": "Position in the rack",
                },
                "primary_ip": {
                    "type": "string",
                    "description": "Device primary IP address",
                },
            },
        ),
    ]
    
    # Mock devices for simulation mode
    MOCK_DEVICES = [
        {
            "id": 1,
            "name": "router-core-01",
            "serial": "FOC123456789",
            "device_type": {
                "model": "Cisco ASR 9922",
                "manufacturer": {
                    "name": "Cisco"
                }
            },
            "site": {
                "name": "Data Center 1"
            },
            "rack": {
                "name": "R101"
            },
            "position": 10,
            "status": {
                "value": "active",
                "label": "Active"
            },
            "primary_ip": {
                "address": "10.0.0.1/24"
            }
        },
        {
            "id": 2,
            "name": "switch-access-01",
            "serial": "CAT987654321",
            "device_type": {
                "model": "Cisco Catalyst 9300",
                "manufacturer": {
                    "name": "Cisco"
                }
            },
            "site": {
                "name": "Data Center 1"
            },
            "rack": {
                "name": "R102"
            },
            "position": 15,
            "status": {
                "value": "active",
                "label": "Active"
            },
            "primary_ip": {
                "address": "10.0.1.1/24"
            }
        },
        {
            "id": 3,
            "name": "firewall-edge-01",
            "serial": "FTX0987654321",
            "device_type": {
                "model": "Fortinet FortiGate 3700F",
                "manufacturer": {
                    "name": "Fortinet"
                }
            },
            "site": {
                "name": "Data Center 2"
            },
            "rack": {
                "name": "R201"
            },
            "position": 5,
            "status": {
                "value": "active",
                "label": "Active"
            },
            "primary_ip": {
                "address": "192.168.1.1/24"
            }
        },
        {
            "id": 4,
            "name": "server-vm-host-01",
            "serial": "MXQ123456789",
            "device_type": {
                "model": "HPE ProLiant DL380 Gen10",
                "manufacturer": {
                    "name": "HPE"
                }
            },
            "site": {
                "name": "Data Center 1"
            },
            "rack": {
                "name": "R103"
            },
            "position": 20,
            "status": {
                "value": "active",
                "label": "Active"
            },
            "primary_ip": {
                "address": "10.0.2.1/24"
            }
        },
        {
            "id": 5,
            "name": "load-balancer-01",
            "serial": "F5-ABCDEF1234",
            "device_type": {
                "model": "F5 BIG-IP i15800",
                "manufacturer": {
                    "name": "F5 Networks"
                }
            },
            "site": {
                "name": "Data Center 2"
            },
            "rack": {
                "name": "R202"
            },
            "position": 8,
            "status": {
                "value": "active",
                "label": "Active"
            },
            "primary_ip": {
                "address": "192.168.2.1/24"
            }
        }
    ]
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize NetBox adapter.
        
        Args:
            name: Unique name for this adapter instance
            config: Configuration for this adapter
        """
        super().__init__(name, config)
        
        # Initialize API client
        self.api_url = self.config.get("api_url", "").rstrip('/')
        self.api_token = self.config.get("api_token", "")
        self.simulation_mode = self.config.get("simulation_mode", False)
        
        self.headers = {
            'Authorization': f'Token {self.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        self._connected = False
    
    def _get_capabilities(self) -> List[Capability]:
        """
        Get the capabilities supported by this adapter.
        
        Returns:
            List of capabilities
        """
        return self.DEFAULT_CAPABILITIES
    
    async def connect(self) -> bool:
        """
        Connect to NetBox.
        
        Returns:
            True if connection was successful, False otherwise
        """
        if self._connected:
            return True
            
        # If in simulation mode, we're always connected
        if self.simulation_mode:
            logger.info(f"NetBox adapter {self.name} in simulation mode")
            self._connected = True
            return True
            
        try:
            # Test connection to NetBox
            result = await self.test_connection()
            if result:
                self._connected = True
                logger.info(f"NetBox adapter {self.name} connected successfully")
                return True
            else:
                logger.error(f"NetBox adapter {self.name} failed to connect")
                return False
        except Exception as e:
            logger.error(f"Error connecting to NetBox: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from NetBox."""
        self._connected = False
        logger.info(f"NetBox adapter {self.name} disconnected")
    
    async def test_connection(self) -> bool:
        """
        Test connection to NetBox.
        
        Returns:
            True if connection was successful, False otherwise
        """
        # If in simulation mode, we're always connected
        if self.simulation_mode:
            return True
            
        try:
            # Make a non-blocking request
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(
                    f'{self.api_url}/dcim/devices/',
                    headers=self.headers,
                    params={'limit': 1}
                )
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error(f"Error connecting to NetBox: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return False
    
    async def execute(self, command: Command) -> CommandResult:
        """
        Execute a command on NetBox.
        
        Args:
            command: Command to execute
            
        Returns:
            Result of the command execution
        """
        # Ensure we're connected
        if not self._connected and not await self.connect():
            return CommandResult(
                status=CommandStatus.FAILED,
                error="Not connected to NetBox"
            )
            
        capability = command.capability
        params = command.parameters
        
        # Handle different capabilities
        if capability == "list_devices":
            return await self._handle_list_devices(params)
        elif capability == "get_device":
            return await self._handle_get_device(params)
        elif capability == "create_device":
            return await self._handle_create_device(params)
        else:
            return CommandResult(
                status=CommandStatus.FAILED,
                error=f"Unsupported capability: {capability}"
            )
    
    async def _handle_list_devices(self, params: Dict[str, Any]) -> CommandResult:
        """
        Handle list_devices capability.
        
        Args:
            params: Command parameters
            
        Returns:
            Command result
        """
        limit = params.get("limit", 100)
        offset = params.get("offset", 0)
        device_type = params.get("device_type")
        
        try:
            # Get devices
            if self.simulation_mode:
                logger.info("Using mock device data")
                devices = self.MOCK_DEVICES.copy()
                
                # Filter by device type if specified
                if device_type:
                    device_type_lower = device_type.lower()
                    devices = [
                        device for device in devices
                        if (device_type_lower in device.get('device_type', {}).get('model', '').lower() or
                            device_type_lower in device.get('name', '').lower())
                    ]
                
                # Apply pagination
                paginated_devices = devices[offset:offset + limit]
                
                return CommandResult(
                    status=CommandStatus.COMPLETED,
                    data=paginated_devices,
                    message=f"Retrieved {len(paginated_devices)} devices"
                )
            else:
                # Make a non-blocking request
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: requests.get(
                        f'{self.api_url}/dcim/devices/',
                        headers=self.headers,
                        params={
                            'limit': limit,
                            'offset': offset,
                            'status': 'active'
                        }
                    )
                )
                response.raise_for_status()
                data = response.json()
                
                devices = data.get('results', [])
                
                # Filter by device type if specified
                if device_type:
                    device_type_lower = device_type.lower()
                    devices = [
                        device for device in devices
                        if (device_type_lower in device.get('device_type', {}).get('model', '').lower() or
                            device_type_lower in device.get('name', '').lower())
                    ]
                
                return CommandResult(
                    status=CommandStatus.COMPLETED,
                    data=devices,
                    message=f"Retrieved {len(devices)} devices"
                )
        except Exception as e:
            logger.error(f"Error listing devices: {e}")
            return CommandResult(
                status=CommandStatus.FAILED,
                error=f"Error listing devices: {str(e)}"
            )
    
    async def _handle_get_device(self, params: Dict[str, Any]) -> CommandResult:
        """
        Handle get_device capability.
        
        Args:
            params: Command parameters
            
        Returns:
            Command result
        """
        device_name = params.get("name")
        device_id = params.get("id")
        
        if not device_name and not device_id:
            return CommandResult(
                status=CommandStatus.FAILED,
                error="Either name or id parameter is required"
            )
            
        try:
            if self.simulation_mode:
                logger.info("Using mock device data")
                
                # Find device by name or id
                for device in self.MOCK_DEVICES:
                    if device_name and device_name.lower() in device.get('name', '').lower():
                        return CommandResult(
                            status=CommandStatus.COMPLETED,
                            data=device,
                            message=f"Retrieved device: {device.get('name')}"
                        )
                    elif device_id and device.get('id') == device_id:
                        return CommandResult(
                            status=CommandStatus.COMPLETED,
                            data=device,
                            message=f"Retrieved device: {device.get('name')}"
                        )
                
                return CommandResult(
                    status=CommandStatus.FAILED,
                    error="Device not found"
                )
            else:
                # Make a non-blocking request
                loop = asyncio.get_event_loop()
                
                if device_id:
                    # Get device by ID
                    response = await loop.run_in_executor(
                        None,
                        lambda: requests.get(
                            f'{self.api_url}/dcim/devices/{device_id}/',
                            headers=self.headers
                        )
                    )
                    response.raise_for_status()
                    device = response.json()
                    
                    return CommandResult(
                        status=CommandStatus.COMPLETED,
                        data=device,
                        message=f"Retrieved device: {device.get('name')}"
                    )
                else:
                    # Get all devices and filter by name
                    response = await loop.run_in_executor(
                        None,
                        lambda: requests.get(
                            f'{self.api_url}/dcim/devices/',
                            headers=self.headers,
                            params={'name': device_name}
                        )
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    devices = data.get('results', [])
                    
                    if devices:
                        device = devices[0]
                        return CommandResult(
                            status=CommandStatus.COMPLETED,
                            data=device,
                            message=f"Retrieved device: {device.get('name')}"
                        )
                    else:
                        return CommandResult(
                            status=CommandStatus.FAILED,
                            error="Device not found"
                        )
        except Exception as e:
            logger.error(f"Error getting device: {e}")
            return CommandResult(
                status=CommandStatus.FAILED,
                error=f"Error getting device: {str(e)}"
            )
    
    async def _handle_create_device(self, params: Dict[str, Any]) -> CommandResult:
        """
        Handle create_device capability.
        
        Args:
            params: Command parameters
            
        Returns:
            Command result
        """
        # Check required parameters
        required_fields = ['name', 'device_type', 'manufacturer', 'site_name']
        missing_fields = [field for field in required_fields if not params.get(field)]
        
        if missing_fields:
            return CommandResult(
                status=CommandStatus.FAILED,
                error=f"Missing required fields: {', '.join(missing_fields)}"
            )
            
        try:
            if self.simulation_mode:
                logger.info("Creating mock device")
                
                # Generate next ID
                next_id = max([device.get('id', 0) for device in self.MOCK_DEVICES]) + 1
                
                # Create new device in mock format
                new_device = {
                    "id": next_id,
                    "name": params.get('name'),
                    "serial": params.get('serial', ''),
                    "device_type": {
                        "model": params.get('device_type', ''),
                        "manufacturer": {
                            "name": params.get('manufacturer', '')
                        }
                    },
                    "site": {
                        "name": params.get('site_name', '')
                    },
                    "rack": {
                        "name": params.get('rack', '')
                    } if params.get('rack') else None,
                    "position": params.get('position', None),
                    "status": {
                        "value": params.get('status', 'active'),
                        "label": params.get('status', 'active').capitalize()
                    },
                    "primary_ip": {
                        "address": params.get('primary_ip', '')
                    } if params.get('primary_ip') else None
                }
                
                # Add to mock devices
                self.MOCK_DEVICES.append(new_device)
                
                return CommandResult(
                    status=CommandStatus.COMPLETED,
                    data=new_device,
                    message=f"Created device: {new_device.get('name')}"
                )
            else:
                # In real mode, transform the data to NetBox API format
                api_data = {
                    "name": params.get('name'),
                    "serial": params.get('serial', ''),
                    # In a real implementation, we would need to query for IDs of related objects
                    # like device_type, site, rack, etc.
                    # This is simplified for demo purposes
                    "device_type": 1,  # Would be a real ID in production
                    "site": 1,  # Would be a real ID in production
                    "status": params.get('status', 'active'),
                }
                
                # Add optional fields if present
                if params.get('rack'):
                    api_data["rack"] = 1  # Would be a real ID in production
                
                if params.get('position'):
                    api_data["position"] = params.get('position')
                
                # Make a non-blocking request
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: requests.post(
                        f'{self.api_url}/dcim/devices/',
                        headers=self.headers,
                        json=api_data
                    )
                )
                response.raise_for_status()
                
                device = response.json()
                
                return CommandResult(
                    status=CommandStatus.COMPLETED,
                    data=device,
                    message=f"Created device: {device.get('name')}"
                )
        except Exception as e:
            logger.error(f"Error creating device: {e}")
            return CommandResult(
                status=CommandStatus.FAILED,
                error=f"Error creating device: {str(e)}"
            )
    
    def _get_config_schema_properties(self) -> Dict[str, Any]:
        """
        Get the configuration schema properties for this adapter.
        
        Returns:
            Configuration schema properties as a dictionary
        """
        return {
            "api_url": {
                "type": "string",
                "description": "NetBox API URL"
            },
            "api_token": {
                "type": "string",
                "description": "NetBox API token"
            },
            "simulation_mode": {
                "type": "boolean",
                "description": "Whether to use simulation mode",
                "default": False
            }
        }
    
    def _get_config_schema_required(self) -> List[str]:
        """
        Get the required configuration properties for this adapter.
        
        Returns:
            List of required configuration property names
        """
        return ["api_url", "api_token"]