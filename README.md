# NetBox GPT

![GitHub License](https://img.shields.io/github/license/reinaldosaraiva/netbox-gpt?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![Last Commit](https://img.shields.io/github/last-commit/reinaldosaraiva/netbox-gpt?style=for-the-badge)

Uma interface em linguagem natural para NetBox que utiliza os modelos GPT da OpenAI. Consulte e gerencie sua infraestrutura de rede usando comandos simples em inglês ou português.

> NetBox GPT transforma a maneira como você interage com o NetBox, permitindo consultas em linguagem natural e automatizando tarefas comuns de gerenciamento de rede sem a necessidade de aprender APIs complexas.

## 🚀 Funcionalidades

- ✅ Consulta ao inventário do NetBox usando linguagem natural
- ✅ Busca de dispositivos por tipo, nome, site e status
- ✅ Criação de novos dispositivos usando comandos conversacionais
- ✅ Suporte para consultas em inglês e português
- ✅ Modo alternativo com regex quando a API da OpenAI não está disponível
- ✅ Modo de simulação para testes sem uma instância do NetBox

## 📋 Status do Projeto

O projeto está em desenvolvimento ativo. Próximas melhorias incluem:

- [x] Suporte a consultas básicas de dispositivos
- [x] Modo de simulação para testes sem NetBox
- [x] Suporte a múltiplos idiomas
- [ ] Integração com novas entidades do NetBox (VLANs, IPs, etc.)
- [ ] Integração com outros LLMs além do OpenAI GPT

## ⚙️ Pré-requisitos

Antes de começar, você vai precisar ter instalado:

- Python 3.8+
- Uma instância do NetBox acessível (ou usar o modo de simulação)
- Chave de API da OpenAI (opcional)

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
# Configuração da API do NetBox
NETBOX_API_URL=http://your-netbox-instance/api
NETBOX_API_TOKEN=your_netbox_api_token
NETBOX_SIMULATION_MODE=false  # Defina como true para usar dados simulados

# Configuração da OpenAI (ChatGPT)
OPENAI_API_KEY=sk-your-openai-api-key
```

## 🔍 Modo de Uso

### Interface de Linha de Comando

```bash
# Executar com uma consulta direta
netbox-gpt "list all routers"
netbox-gpt "find device switch-core-01"
netbox-gpt "create new firewall named fw-edge-02 from Fortinet in Data Center 2"

# Iniciar o modo interativo
netbox-gpt
```

### Exemplos de Consultas

<details>
<summary>Listagem de Dispositivos</summary>

- "List all devices"
- "Show me the routers"
- "What load balancers do we have?"
- "Mostrar todos os switches" (Portuguese)
</details>

<details>
<summary>Busca de Dispositivos Específicos</summary>

- "Find device router-core-01"
- "Show details for switch-access-02"
- "Encontrar dispositivo firewall-edge-01" (Portuguese)
</details>

<details>
<summary>Criação de Dispositivos</summary>

- "Create a new switch named switch-core-03 from Cisco in Data Center 1"
- "Add firewall Fortinet FortiGate 3700F in site Data Center 2"
- "Criar um novo servidor HP DL380 chamado server-db-01" (Portuguese)
</details>

## 🧪 Modo de Simulação

> [!TIP]
> Para testes ou demonstração sem uma instância do NetBox, configure `NETBOX_SIMULATION_MODE=true` no seu arquivo `.env`. Isso usa dados simulados predefinidos.

## 🔌 Modo Offline

Se a API da OpenAI não estiver disponível ou você não tiver uma chave de API, o assistente automaticamente utilizará pattern matching baseado em regex para consultas básicas.

## 👨‍💻 Contribuindo

Contribuições são bem-vindas! Consulte o arquivo [CONTRIBUTING.md](CONTRIBUTING.md) para obter mais informações sobre como contribuir para este projeto.

## 📄 Licença

Este projeto está sob a licença MIT - veja o arquivo [LICENSE](LICENSE.md) para mais detalhes.

---

Feito com ❤️ por [Reinaldo Saraiva](https://github.com/reinaldosaraiva)