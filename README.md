# MCP Server

![GitHub License](https://img.shields.io/github/license/reinaldosaraiva/netbox-gpt?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![Last Commit](https://img.shields.io/github/last-commit/reinaldosaraiva/netbox-gpt?style=for-the-badge)

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

## 💻 Instalação

### Clone o repositório
```bash
git clone https://github.com/reinaldosaraiva/netbox-gpt.git
cd netbox-gpt
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

## 🔍 Modo de Uso

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

### Exemplos de Requisições API

<details>
<summary>Listar Adaptadores</summary>

```bash
curl -X GET "http://localhost:8000/api/v1/adapters" \
     -H "X-API-Key: sua_api_key"
```
</details>

<details>
<summary>Executar Comando em um Adaptador</summary>

```bash
curl -X POST "http://localhost:8000/api/v1/commands" \
     -H "X-API-Key: sua_api_key" \
     -H "Content-Type: application/json" \
     -d '{
           "adapter": "default-netbox",
           "capability": "list_devices",
           "parameters": {
             "limit": 10
           }
         }'
```
</details>

<details>
<summary>Criar Dispositivo no NetBox</summary>

```bash
curl -X POST "http://localhost:8000/api/v1/commands" \
     -H "X-API-Key: sua_api_key" \
     -H "Content-Type: application/json" \
     -d '{
           "adapter": "default-netbox",
           "capability": "create_device",
           "parameters": {
             "name": "router-core-03",
             "device_type": "Cisco ASR 9922",
             "manufacturer": "Cisco",
             "site_name": "Data Center 1",
             "status": "active"
           }
         }'
```
</details>

## 🧪 Modo de Simulação

Para testes ou demonstração sem instâncias reais das ferramentas, configure as variáveis de ambiente correspondentes para o modo de simulação. Por exemplo:

```
NETBOX_SIMULATION_MODE=true
```

Isso permite testar as funcionalidades sem dependências externas.

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