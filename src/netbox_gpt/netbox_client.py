"""NetBox API client for retrieving and creating devices."""

import os
import requests
from typing import Dict, List, Optional, Any
from rich.console import Console

# Initialize console
console = Console()


class NetBoxClient:
    """Client for interacting with NetBox API."""

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

    def __init__(self, api_url: str, api_token: str):
        """
        Initialize NetBox client.

        Args:
            api_url: NetBox API base URL
            api_token: NetBox API authentication token
        """
        self.api_url = api_url.rstrip('/')
        self.headers = {
            'Authorization': f'Token {api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
    
    def test_connection(self) -> bool:
        """Test NetBox API connection.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        # Check if we should use simulation mode
        if os.getenv('NETBOX_SIMULATION_MODE', 'false').lower() == 'true':
            console.print("[yellow]NetBox in simulation mode - using mock data[/]")
            return True
            
        try:
            response = requests.get(
                f'{self.api_url}/dcim/devices/',
                headers=self.headers,
                params={'limit': 1}
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            console.print(f"[bold red]Error connecting to NetBox:[/] {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                console.print(f"[bold red]Response:[/] {e.response.text}")
            return False
    
    def get_devices(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Get devices from NetBox.
        
        Args:
            limit: Maximum number of devices to return
            offset: Pagination offset
            
        Returns:
            List of device dictionaries
        """
        # Check if we should use simulation mode
        if os.getenv('NETBOX_SIMULATION_MODE', 'false').lower() == 'true':
            console.print("[yellow]Using mock device data[/]")
            # Return all mock devices up to the limit
            return NetBoxClient.MOCK_DEVICES[:limit]
            
        try:
            response = requests.get(
                f'{self.api_url}/dcim/devices/',
                headers=self.headers,
                params={
                    'limit': limit,
                    'offset': offset,
                    'status': 'active'
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
        except requests.RequestException as e:
            console.print(f"[bold red]Error fetching devices:[/] {str(e)}")
            return []
    
    def create_device(self, device_data: Dict) -> Optional[Dict]:
        """
        Create a new device in NetBox.
        
        Args:
            device_data: Dictionary with device information
            
        Returns:
            Newly created device dictionary or None if failed
        """
        # Map device_name to name if present
        if device_data.get('device_name') and not device_data.get('name'):
            device_data['name'] = device_data['device_name']
            
        required_fields = ['name', 'device_type', 'manufacturer', 'site_name']
        missing_fields = [field for field in required_fields if not device_data.get(field)]
        
        if missing_fields:
            console.print(f"[bold red]Error:[/] Missing required fields: {', '.join(missing_fields)}")
            return None
            
        # Check if we should use simulation mode
        if os.getenv('NETBOX_SIMULATION_MODE', 'false').lower() == 'true':
            console.print("[yellow]Creating mock device[/]")
            
            # Generate next ID
            next_id = max([device.get('id', 0) for device in NetBoxClient.MOCK_DEVICES]) + 1
            
            # Create new device in mock format
            new_device = {
                "id": next_id,
                "name": device_data.get('device_name', device_data.get('name')),
                "serial": device_data.get('serial', ''),
                "device_type": {
                    "model": device_data.get('device_type', ''),
                    "manufacturer": {
                        "name": device_data.get('manufacturer', '')
                    }
                },
                "site": {
                    "name": device_data.get('site_name', '')
                },
                "rack": {
                    "name": device_data.get('rack', '')
                } if device_data.get('rack') else None,
                "position": device_data.get('position', None),
                "status": {
                    "value": device_data.get('status', 'active'),
                    "label": device_data.get('status', 'active').capitalize()
                },
                "primary_ip": {
                    "address": device_data.get('primary_ip', '')
                } if device_data.get('primary_ip') else None
            }
            
            # Add to mock devices
            NetBoxClient.MOCK_DEVICES.append(new_device)
            
            return new_device
            
        # In real mode, create device in NetBox
        try:
            # Transform the data to NetBox API format
            api_data = {
                "name": device_data.get('device_name', device_data.get('name')),
                "serial": device_data.get('serial', ''),
                # In a real implementation, we would need to query for IDs of related objects
                # like device_type, site, rack, etc.
                # This is simplified for demo purposes
                "device_type": 1,  # Would be a real ID in production
                "site": 1,  # Would be a real ID in production
                "status": device_data.get('status', 'active'),
            }
            
            # Add optional fields if present
            if device_data.get('rack'):
                api_data["rack"] = 1  # Would be a real ID in production
            
            if device_data.get('position'):
                api_data["position"] = device_data.get('position')
                
            # Send request to NetBox API
            response = requests.post(
                f'{self.api_url}/dcim/devices/',
                headers=self.headers,
                json=api_data
            )
            response.raise_for_status()
            
            return response.json()
        except requests.RequestException as e:
            console.print(f"[bold red]Error creating device:[/] {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                console.print(f"[bold red]Response:[/] {e.response.text}")
            return None


def get_client_from_env() -> Optional[NetBoxClient]:
    """
    Create NetBox client from environment variables.
    
    Returns:
        NetBoxClient instance or None if configuration is missing
    """
    api_url = os.getenv('NETBOX_API_URL')
    api_token = os.getenv('NETBOX_API_TOKEN')
    
    if not api_url or not api_token:
        console.print("[bold red]Error:[/] NETBOX_API_URL and NETBOX_API_TOKEN must be set in .env file")
        return None
    
    return NetBoxClient(api_url, api_token)