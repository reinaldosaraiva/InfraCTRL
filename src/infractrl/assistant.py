"""InfraCTRL Assistant - Natural language interface for infrastructure management."""

import os
import sys
import json
import re
import requests
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from infractrl.netbox_client import get_client_from_env

# Initialize console
console = Console()


def detect_intent_regex(query: str) -> Dict[str, Any]:
    """
    Fallback function to detect intent using regex patterns.
    Used when OpenAI API is not available.
    
    Args:
        query: Natural language query
        
    Returns:
        Dictionary with intent and parameters
    """
    query = query.lower().strip()
    
    # Patterns for list devices
    list_devices_patterns = [
        r"(?:listar?|most(?:ra|re)|exib(?:a|ir)|quais|ver)?\s+(?:os\s+)?(?:todos\s+os\s+)?(?P<device_type>roteadores?|routers?|switches|firewalls?|load\s*balancers?|balanceadores?|servidores?|servers?|dispositivos?|equipamentos?)",
        r"list(?:ar?)?(?:\s+all)?\s+(?P<device_type>router|routers|switch|switches|firewall|firewalls|load\s*balancers?|servers?|devices?)"
    ]
    
    # Patterns for device by name
    device_by_name_patterns = [
        r"(?:find|show|get|display|details?|info(?:rmation)?)(?:\s+for)?\s+(?:device|router|switch|firewall|server|load\s*balancer)?\s+(?:named|called)?\s*[\"']?(?P<device_name>[\w\-\_]+)[\"']?",
        r"(?:encontr(?:e|ar)|mostr(?:e|ar)|exib(?:a|ir)|busc(?:a|ar))(?:\s+o)?\s+(?:dispositivo|roteador|switch|firewall|servidor|balanceador)?\s+(?:chamado|nomeado)?\s*[\"']?(?P<device_name>[\w\-\_]+)[\"']?"
    ]
    
    # Patterns for creation
    create_device_patterns = [
        r"(?:create|add|register|new)\s+(?:a\s+)?(?:new\s+)?(?P<device_type>router|switch|firewall|server|load\s*balancer)(?:\s+named|\s+called)?\s+[\"']?(?P<device_name>[\w\-\_]+)[\"']?",
        r"(?:cri(?:e|ar)|adicionar|cadastrar|novo)\s+(?:um\s+)?(?:novo\s+)?(?P<device_type>roteador|router|switch|firewall|servidor|server|balanceador|load\s*balancer)(?:\s+chamado|\s+nomeado)?\s+[\"']?(?P<device_name>[\w\-\_]+)[\"']?"
    ]
    
    # Check for list devices
    for pattern in list_devices_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            device_type = match.groupdict().get('device_type')
            if device_type:
                # Map common types
                device_type_map = {
                    'roteador': 'router', 'roteadores': 'router',
                    'routers': 'router',  # Ensure "routers" is mapped to singular "router"
                    'balanceador': 'load-balancer', 'balanceadores': 'load-balancer',
                    'servidor': 'server', 'servidores': 'server'
                }
                device_type = device_type_map.get(device_type, device_type)
                
            return {
                "intent": "list_devices",
                "params": {"device_type": device_type}
            }
    
    # Check for device by name
    for pattern in device_by_name_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return {
                "intent": "device_by_name",
                "params": match.groupdict()
            }
            
    # Check for device creation
    for pattern in create_device_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            params = match.groupdict()
            
            # Try to extract manufacturer from additional text
            manufacturer_match = re.search(r"(?:from|by|made by|manufacturer|fabricante|marca)\s+[\"']?([A-Za-z0-9\s]+)[\"']?", query, re.IGNORECASE)
            if manufacturer_match:
                params['manufacturer'] = manufacturer_match.group(1).strip()
                
            # Try to extract site
            site_match = re.search(r"(?:in|at|on|site|location|local|em|no|na)\s+[\"']?([\w\s]+(?:data\s*center|site|dc|datacenter|location)[\w\s]*)[\"']?", query, re.IGNORECASE)
            if site_match:
                params['site_name'] = site_match.group(1).strip()
                
            return {
                "intent": "create_device",
                "params": params
            }
            
    # Default to unknown intent
    return {
        "intent": "unknown",
        "params": {}
    }


def query_openai(prompt: str) -> Dict:
    """
    Envia uma consulta para a API do OpenAI e retorna a resposta.
    
    Args:
        prompt: A consulta em linguagem natural
        
    Returns:
        Dicionário com a intenção e parâmetros extraídos
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        console.print("[bold yellow]Warning:[/] OPENAI_API_KEY not defined in .env file")
        console.print("[yellow]Falling back to regex pattern matching...[/]")
        return detect_intent_regex(prompt)
    
    # Construir o prompt para o OpenAI
    system_prompt = """
    You are a specialized assistant that extracts structured information from natural language queries about network devices in NetBox.
    
    Extract the intent and parameters from the user's query.
    
    Possible intents are:
    - list_devices: List devices, possibly filtered by type
    - device_by_name: Look up a specific device by name
    - devices_by_site: List devices at a specific site
    - devices_by_status: List devices with a specific status
    - create_device: Create a new device in NetBox
    
    Parameters for queries:
    - device_type: Device type (router, switch, firewall, load-balancer, etc.)
    - device_name: Specific device name
    - site_name: Site name
    - status: Device status (active, offline, maintenance, etc.)
    
    Parameters required for device creation:
    - device_name: Name of the new device (required)
    - device_type: Device type/model (required)
    - manufacturer: Device manufacturer (required)
    - site_name: Location where the device is installed (required)
    - status: Device status (active, offline, planned, etc.)
    - serial: Device serial number
    - rack: Rack name where installed
    - position: Position in the rack
    - primary_ip: Device primary IP address
    
    Respond ONLY with a valid JSON in the following format:
    {
        "intent": "intent_name",
        "params": {
            "param1": "value1",
            "param2": "value2"
        }
    }
    
    Map terms in Portuguese to their English equivalents in the parameters field.
    For example, "roteador" should be mapped to "router", "ativo" to "active".
    
    If the query seems to request device creation, classify as "create_device" intent and extract all mentioned parameters.
    """
    
    # URL da API do OpenAI
    url = "https://api.openai.com/v1/chat/completions"
    
    # Cabeçalhos da requisição
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Lista de modelos para tentar em ordem
    models = [
        "gpt-4",
        "gpt-4-turbo-preview",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
    ]
    
    # Corpo da requisição para o primeiro modelo
    data = {
        "model": models[0],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    response = None
    result = None
    
    # Tentar com diferentes modelos
    for model in models:
        try:
            # Atualizar modelo
            data["model"] = model
            console.print(f"[yellow]Trying with model: {model}[/]")
            
            # Enviar a requisição
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                console.print(f"[green]Success with model: {model}[/]")
                break
                
        except requests.RequestException as e:
            console.print(f"[bold red]Error communicating with model {model}:[/] {str(e)}")
            if model == models[-1]:  # If it's the last model
                console.print("[yellow]Falling back to regex pattern matching...[/]")
                return detect_intent_regex(prompt)
            else:
                console.print("[yellow]Trying next model...[/]")
    
    # If all models failed
    if not result:
        console.print("[bold red]All OpenAI models failed[/]")
        console.print("[yellow]Falling back to regex pattern matching...[/]")
        return detect_intent_regex(prompt)
    
    # Extract the response
    try:
        content = result["choices"][0]["message"]["content"].strip()
        
        # Try to parse JSON from the response
        try:
            # Sometimes GPT returns JSON with additional formatting
            json_str = content.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
                
            json_data = json.loads(json_str.strip())
            return json_data
        except json.JSONDecodeError as e:
            console.print(f"[bold red]Error processing OpenAI response:[/] {str(e)}")
            console.print("[yellow]Falling back to regex pattern matching...[/]")
            return detect_intent_regex(prompt)
            
    except (KeyError, IndexError) as e:
        console.print(f"[bold red]Error extracting content from response:[/] {str(e)}")
        console.print("[yellow]Falling back to regex pattern matching...[/]")
        return detect_intent_regex(prompt)


def get_devices_by_type(netbox_client, device_type: Optional[str] = None) -> List[Dict]:
    """
    Get devices from NetBox, optionally filtered by type.
    
    Args:
        netbox_client: NetBox client instance
        device_type: Device type to filter by (optional)
        
    Returns:
        List of device dictionaries
    """
    # Get all devices
    devices = netbox_client.get_devices(limit=500)
    
    # If no filter, return all
    if not device_type:
        return devices
    
    # Filter by type
    filtered_devices = []
    for device in devices:
        # Check if device type contains the search term
        device_model = device.get('device_type', {}).get('model', '').lower()
        device_type_lower = device_type.lower()
        
        # Check for partial match in model or name
        if (device_type_lower in device_model or 
            device_type_lower in device.get('name', '').lower()):
            filtered_devices.append(device)
    
    return filtered_devices


def get_device_by_name(netbox_client, device_name: str) -> Optional[Dict]:
    """
    Get a specific device by name.
    
    Args:
        netbox_client: NetBox client instance
        device_name: Device name to look up
        
    Returns:
        Device dictionary or None if not found
    """
    # Get all devices
    devices = netbox_client.get_devices(limit=500)
    
    # Clean up the search term
    device_name = device_name.strip().lower()
    
    # Look for exact or partial name match
    for device in devices:
        if device_name in device.get('name', '').lower():
            return device
    
    return None


def display_devices(devices: List[Dict]) -> None:
    """
    Display a formatted table of devices.
    
    Args:
        devices: List of device dictionaries to display
    """
    if not devices:
        console.print(Panel("[yellow]No devices found[/]", 
                          title="Query Result"))
        return
    
    table = Table(title=f"Devices ({len(devices)})")
    
    # Add columns
    table.add_column("Name", style="cyan")
    table.add_column("Model", style="green")
    table.add_column("Manufacturer")
    table.add_column("Site")
    table.add_column("Status", style="yellow")
    table.add_column("Primary IP", style="blue")
    
    # Add rows
    for device in devices:
        name = device.get('name', 'N/A')
        model = device.get('device_type', {}).get('model', 'N/A')
        manufacturer = device.get('device_type', {}).get('manufacturer', {}).get('name', 'N/A')
        site = device.get('site', {}).get('name', 'N/A')
        status = device.get('status', {}).get('value', 'N/A')
        ip = device.get('primary_ip', {}).get('address', 'N/A') if device.get('primary_ip') else 'N/A'
        
        table.add_row(name, model, manufacturer, site, status, ip)
    
    console.print(table)


def display_device_detail(device: Dict) -> None:
    """
    Display detailed information about a specific device.
    
    Args:
        device: Device dictionary to display
    """
    if not device:
        console.print(Panel("[yellow]Device not found[/]", 
                          title="Query Result"))
        return
    
    # Create detailed table
    table = Table(title=f"Device Details: {device.get('name', 'N/A')}")
    
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    # Add basic information
    table.add_row("Name", device.get('name', 'N/A'))
    table.add_row("Model", device.get('device_type', {}).get('model', 'N/A'))
    table.add_row("Manufacturer", device.get('device_type', {}).get('manufacturer', {}).get('name', 'N/A'))
    table.add_row("Serial Number", device.get('serial', 'N/A'))
    table.add_row("Site", device.get('site', {}).get('name', 'N/A'))
    table.add_row("Rack", device.get('rack', {}).get('name', 'N/A') if device.get('rack') else 'N/A')
    table.add_row("Position", str(device.get('position', 'N/A')))
    table.add_row("Status", device.get('status', {}).get('value', 'N/A'))
    table.add_row("Primary IP", device.get('primary_ip', {}).get('address', 'N/A') if device.get('primary_ip') else 'N/A')
    
    # Add additional properties if available
    if device.get('comments'):
        table.add_row("Comments", device.get('comments', ''))
    
    console.print(table)


def process_query(query: str) -> None:
    """
    Process a user query and display results.
    
    Args:
        query: Natural language query from the user
    """
    # Load environment variables
    load_dotenv()
    
    # Get NetBox client
    netbox_client = get_client_from_env()
    if not netbox_client:
        console.print("[bold red]Error:[/] Could not initialize NetBox client")
        return
    
    # Test connection to NetBox
    if not netbox_client.test_connection():
        console.print("[bold red]Error:[/] Could not connect to NetBox")
        return
    
    # Detect intent from the query
    console.print("[dim]Processing your query with GPT...[/]")
    intent_data = query_openai(query)
    
    intent = intent_data.get("intent", "unknown")
    params = intent_data.get("params", {})
    
    console.print(f"[dim]I understand you want to: {intent}[/]")
    
    # Process the intent
    if intent == "list_devices":
        device_type = params.get('device_type')
        if device_type:
            console.print(f"[dim]Looking for devices of type: {device_type}[/]")
            devices = get_devices_by_type(netbox_client, device_type)
        else:
            console.print("[dim]Looking for all devices[/]")
            devices = get_devices_by_type(netbox_client)
        
        display_devices(devices)
    
    elif intent == "device_by_name":
        device_name = params.get('device_name')
        if device_name:
            console.print(f"[dim]Looking for device: {device_name}[/]")
            device = get_device_by_name(netbox_client, device_name)
            display_device_detail(device)
        else:
            console.print("[bold yellow]Warning:[/] Device name not specified")
    
    elif intent == "create_device":
        console.print("[bold blue]Creating new device...[/]")
        
        # Display detected parameters
        console.print("[dim]Detected parameters:[/]")
        for key, value in params.items():
            console.print(f"[dim]- {key}: {value}[/]")
        
        # Confirm with user in interactive mode
        if len(sys.argv) <= 1:  # Interactive mode
            confirm = console.input("\n[bold yellow]Confirm device creation? (y/n)[/] ")
            if confirm.lower() not in ['y', 'yes', 's', 'sim']:
                console.print("[yellow]Operation cancelled by user[/]")
                return
        
        # Create the device
        result = netbox_client.create_device(params)
        
        if result:
            console.print("[bold green]✓[/] Device created successfully!")
            display_device_detail(result)
        else:
            console.print("[bold red]Failed to create device.[/] Check parameters and try again.")
    
    else:
        console.print("[bold yellow]I didn't understand your query.[/] Try phrasing it differently.")
        console.print(Markdown("""
        **Examples of queries you can try:**
        
        - List all devices
        - Show all routers
        - What load balancers do we have?
        - Find device router-core-01
        - List devices in "Data Center 1"
        - Show devices with active status
        - Create a new switch named switch-core-03 from Cisco in Data Center 1
        - Add a firewall Fortinet in site Data Center 2
        """))


def main():
    """Main function for the InfraCTRL assistant."""
    console.print(Panel.fit(
        "[bold cyan]InfraCTRL[/]\n"
        "Multi-tool Control Platform for infrastructure management",
        title="Welcome"
    ))
    
    # Check if a query was provided as argument
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        process_query(query)
        return
    
    # Interactive mode
    console.print("[yellow]Type 'exit' to quit[/]")
    
    while True:
        try:
            query = console.input("\n[bold green]What would you like to know?[/] ")
            if query.lower() in ['exit', 'quit', 'q', 'sair']:
                console.print("[yellow]Exiting assistant...[/]")
                break
                
            process_query(query)
            
        except KeyboardInterrupt:
            console.print("[yellow]\nExiting assistant...[/]")
            break
        except Exception as e:
            console.print(f"[bold red]Unexpected error:[/] {str(e)}")


if __name__ == "__main__":
    main()