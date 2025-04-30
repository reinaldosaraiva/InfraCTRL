# NetBox GPT

A natural language interface for NetBox using OpenAI's GPT models. Query and manage your network infrastructure using simple English or Portuguese commands.

## Features

- Query NetBox inventory using natural language
- Search for devices by type, name, site, and status
- Create new devices using conversational commands
- Support for both English and Portuguese queries
- Fallback to regex pattern matching when OpenAI API is unavailable
- Simulation mode for testing without a NetBox instance

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/netbox-gpt.git
cd netbox-gpt

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
# venv\Scripts\activate  # Windows

# Install the package
pip install -e .
```

## Configuration

Copy the `.env.example` file to `.env` and configure your settings:

```bash
cp .env.example .env
```

Edit the `.env` file:

```
# NetBox API configuration
NETBOX_API_URL=http://your-netbox-instance/api
NETBOX_API_TOKEN=your_netbox_api_token
NETBOX_SIMULATION_MODE=false  # Set to true to use mock data

# OpenAI (ChatGPT) configuration
OPENAI_API_KEY=sk-your-openai-api-key
```

## Usage

### Command Line Interface

```bash
# Run with a direct query
netbox-gpt "list all routers"
netbox-gpt "find device switch-core-01"
netbox-gpt "create new firewall named fw-edge-02 from Fortinet in Data Center 2"

# Start interactive mode
netbox-gpt
```

### Example Queries

#### Listing Devices
- "List all devices"
- "Show me the routers"
- "What load balancers do we have?"
- "Mostrar todos os switches" (Portuguese)

#### Finding Specific Devices
- "Find device router-core-01"
- "Show details for switch-access-02"
- "Encontrar dispositivo firewall-edge-01" (Portuguese)

#### Creating Devices
- "Create a new switch named switch-core-03 from Cisco in Data Center 1"
- "Add firewall Fortinet FortiGate 3700F in site Data Center 2"
- "Criar um novo servidor HP DL380 chamado server-db-01" (Portuguese)

## Simulation Mode

For testing or demonstration without a NetBox instance, set `NETBOX_SIMULATION_MODE=true` in your `.env` file. This uses predefined mock data.

## Offline Mode

If the OpenAI API is not available or you don't have an API key, the assistant will automatically fall back to regex-based pattern matching for basic queries.

## Requirements

- Python 3.8+
- requests
- python-dotenv
- rich (for formatted output)
- OpenAI API key (optional)

## License

MIT