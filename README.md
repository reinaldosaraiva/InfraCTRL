# MCP Server

![GitHub License](https://img.shields.io/github/license/reinaldosaraiva/InfraCTRL?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![Last Commit](https://img.shields.io/github/last-commit/reinaldosaraiva/InfraCTRL?style=for-the-badge)

**Multi-tool Control Platform Server** para gerenciamento de infraestrutura - uma plataforma extensível para integração com diversas ferramentas de infraestrutura.

> MCP Server transforma a maneira como você interage com suas ferramentas de infraestrutura, fornecendo uma API unificada e extensível que permite integrar e automatizar tarefas em múltiplas plataformas.

## 🚀 Funcionalidades

- ✅ Arquitetura extensível de adaptadores para ferramentas de infraestrutura
- ✅ API RESTful para interação com as ferramentas integradas
- ✅ Sistema de autenticação baseado em API keys
- ✅ Suporte para execução assíncrona de tarefas
- ✅ Adaptador para NetBox com funcionalidades de gerenciamento de inventário
- ✅ Modo de simulação para testes sem dependências externas

## 🔌 Adaptadores Disponíveis

- **NetBox**: Gerenciamento de inventário de infraestrutura

## 📋 Status do Projeto

O projeto está em desenvolvimento ativo. Próximas melhorias incluem:

- [x] Arquitetura base de adaptadores
- [x] API RESTful com FastAPI
- [x] Adaptador NetBox para gerenciamento de inventário
- [ ] Persistência de configuração em banco de dados
- [ ] Interface web de administração
- [ ] Adaptadores para outras ferramentas (Ansible, Terraform, etc.)
- [ ] Sistema de plugins para extensões

## ⚙️ Pré-requisitos

Antes de começar, você vai precisar ter instalado:

- Python 3.8+
- Ferramentas integradas conforme necessário (ex: NetBox)
- HTTPie (opcional, para testes de API via linha de comando)

## 💻 Instalação

### Clone o repositório
```bash
git clone https://github.com/reinaldosaraiva/InfraCTRL.git
cd InfraCTRL
```

### Crie um ambiente virtual
```bash
# Linux/macOS
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Instale o pacote
```bash
pip install -e .
```

## ⚙️ Configuração

Copie o arquivo `.env.example` para `.env` e configure suas configurações:

```bash
cp .env.example .env
```

Edite o arquivo `.env`:

```
# Configuração do Servidor
ADMIN_API_KEY=sua_chave_api_admin  # Opcional, será gerada se não especificada

# Configuração da API do NetBox (Opcional)
NETBOX_API_URL=http://your-netbox-instance/api
NETBOX_API_TOKEN=your_netbox_api_token
NETBOX_SIMULATION_MODE=false  # Defina como true para usar dados simulados
```

## 🔍 Uso do Servidor

### Iniciar o Servidor

```bash
# Iniciar o servidor na porta padrão 8000
mcp-server serve

# Especificar host e porta
mcp-server serve --host 0.0.0.0 --port 9000

# Modo de desenvolvimento com auto-reload
mcp-server serve --reload
```

### Gerenciar API Keys

```bash
# Criar uma nova API key
mcp-server key create "Nome da Chave"
```

## 🔑 Autenticação

Todas as requisições à API exigem autenticação usando uma chave API através do cabeçalho `X-API-Key`. Você tem três opções para obter uma chave API:

1. **Configuração no .env**: Defina a variável `ADMIN_API_KEY` no arquivo `.env`
2. **Chave Gerada Automaticamente**: Ao iniciar o servidor sem a variável `ADMIN_API_KEY`, uma chave será gerada e exibida no console
3. **Criar Nova Chave**: Use o comando `mcp-server key create "Nome da Chave"`

**Importante**: Ao criar uma nova chave, ela será exibida apenas uma vez. Guarde-a em um local seguro.

## 📡 Utilizando a API

### Usando HTTPie

[HTTPie](https://httpie.io/) é uma ferramenta de linha de comando amigável para interações HTTP. Instale com `pip install httpie`.

**IMPORTANTE**: Para comandos GET, você DEVE especificar explicitamente o método HTTP:

```bash
# Listar adaptadores (observe o 'GET' explícito)
http GET http://localhost:9000/api/v1/adapters/ X-API-Key:sua_api_key
```

### Comandos Básicos com HTTPie

#### Listar Adaptadores
```bash
http GET http://localhost:9000/api/v1/adapters/ X-API-Key:sua_api_key
```

#### Listar Chaves API
```bash
http GET http://localhost:9000/api/v1/auth/api-keys X-API-Key:sua_api_key
```

#### Criar Nova Chave API
```bash
echo '{"name": "Nova Chave"}' | http POST http://localhost:9000/api/v1/auth/api-keys X-API-Key:sua_api_key
```

### Operações com Adaptadores

#### Listar Dispositivos (NetBox)
```bash
echo '{"adapter": "default-netbox", "capability": "list_devices", "resource_type": "device", "parameters": {}}' | \
http POST http://localhost:9000/api/v1/commands/ X-API-Key:sua_api_key
```

#### Filtrar Dispositivos por Tipo
```bash
echo '{"adapter": "default-netbox", "capability": "list_devices", "resource_type": "device", "parameters": {"device_type": "switch"}}' | \
http POST http://localhost:9000/api/v1/commands/ X-API-Key:sua_api_key
```

#### Obter Dispositivo Específico
```bash
echo '{"adapter": "default-netbox", "capability": "get_device", "resource_type": "device", "parameters": {"name": "router-core-01"}}' | \
http POST http://localhost:9000/api/v1/commands/ X-API-Key:sua_api_key
```

#### Criar Novo Dispositivo
```bash
echo '{
  "adapter": "default-netbox",
  "capability": "create_device",
  "resource_type": "device",
  "parameters": {
    "name": "new-router-01",
    "device_type": "router",
    "manufacturer": "Cisco",
    "site_name": "Data Center 1",
    "status": "active"
  }
}' | http POST http://localhost:9000/api/v1/commands/ X-API-Key:sua_api_key
```

### Usando cURL

Se preferir usar cURL, os mesmos endpoints estão disponíveis:

```bash
# Listar adaptadores
curl -X GET "http://localhost:9000/api/v1/adapters/" \
     -H "X-API-Key: sua_api_key"

# Executar comando (listar dispositivos)
curl -X POST "http://localhost:9000/api/v1/commands/" \
     -H "X-API-Key: sua_api_key" \
     -H "Content-Type: application/json" \
     -d '{
           "adapter": "default-netbox",
           "capability": "list_devices",
           "resource_type": "device",
           "parameters": {}
         }'
```

## 🧪 Modo de Simulação

Para testes ou demonstração sem instâncias reais das ferramentas, configure as variáveis de ambiente correspondentes para o modo de simulação:

```
NETBOX_SIMULATION_MODE=true
```

Isso permite testar as funcionalidades sem dependências externas, usando dados simulados.

## 🔍 Solução de Problemas

### Erro "Invalid API key"
- Verifique se a chave API está correta
- Certifique-se de que o servidor está iniciado com a mesma chave API definida no .env
- Tente reiniciar o servidor para aplicar alterações no arquivo .env

### Erro "Method Not Allowed" com HTTPie
- Para requisições GET, especifique explicitamente o método: `http GET ...` em vez de apenas `http ...`
- HTTPie por padrão envia POST se não especificado

### Erro "Field required" no corpo da requisição
- Certifique-se de que está enviando um corpo JSON válido para endpoints POST
- Use o formato correto de pipe com echo para HTTPie: `echo '{"json":"data"}' | http POST ...`

## 📦 Arquitetura

A plataforma é construída com uma arquitetura modular baseada em adaptadores:

```
┌─────────────────────────────────────────────────────────────┐
│                        MCP Server                           │
├─────────────┬───────────────┬──────────────────────────────┤
│ API Gateway │ Auth Provider │ Tool Registry & Orchestrator │
└─────────────┴───────────────┴──────────────────────────────┘
        ▲                                     ▲
        │                                     │
        ▼                                     ▼
┌─────────────────────────┐  ┌─────────────────────────────────┐
│     Tool Adapters       │  │       Storage & Execution       │
├───────────┬─────────────┤  ├────────────────┬────────────────┤
│  NetBox   │   Other     │  │ Configuration  │   Task Queue   │
└───────────┴─────────────┘  └────────────────┴────────────────┘
```

- **API Gateway**: Fornece a interface RESTful para clientes
- **Auth Provider**: Gerencia autenticação e autorização
- **Tool Registry**: Cataloga e gerencia adaptadores de ferramentas
- **Orchestrator**: Coordena operações entre múltiplas ferramentas
- **Adapters**: Conectores para ferramentas específicas

## 👨‍💻 Contribuindo

Contribuições são bem-vindas! Consulte o arquivo [CONTRIBUTING.md](CONTRIBUTING.md) para obter mais informações sobre como contribuir para este projeto.

## 📄 Licença

Este projeto está sob a licença MIT - veja o arquivo [LICENSE](LICENSE.md) para mais detalhes.

---

Feito com ❤️ por [Reinaldo Saraiva](https://github.com/reinaldosaraiva)