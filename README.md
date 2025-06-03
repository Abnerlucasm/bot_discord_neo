# Bot Discord Neo

Este é um bot do Discord para gerenciar e otimizar rotinas internas da Neo Sistemas.

## Funcionalidades

- 🔧 **Gerenciamento inteligente de serviços Glassfish**
  - Sistema de timeout automático com verificação periódica
  - Lembretes automáticos para usuários
  - Sistema de extensões de tempo controlado
  - Liberação automática por inatividade
- 👥 **Sistema avançado de permissões por cargo**
- 🔔 **Notificações em tempo real via DM**
- ⚠️ **Sistema de reporte de problemas**
- 📅 **Gerenciamento de Agendamentos**
- 🔄 **Controle de Atualizações**
- 🧪 **Modo de desenvolvimento para testes**
  - Simulação de tempo de uso
  - Testes de lembretes
  - Verificação de status detalhado
  - Configurações reduzidas para agilizar testes

## Requisitos

- **Python 3.8 ou superior**
- **Bibliotecas necessárias**:
  - `discord.py`
  - `json`
  - `asyncio`
  - `logging`
  
Você pode instalar as dependências necessárias criando um ambiente virtual (recomendado) e utilizando o `pip`:

```bash
# Criação do ambiente virtual
python3 -m venv venv

# Ativação do ambiente virtual
# Linux/MacOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instalação das dependências
pip install -r requirements.txt
```

## Estrutura do Projeto

```plaintext
/bot_Discord_Neo
│
├── main.py                        # Código principal do bot
├── cogs/                          # Diretório que contém a lógica modular do bot
│   ├── glassfish.py              # Cog principal do Glassfish
│   ├── glassfish_commands.py     # Comandos slash do Glassfish
│   ├── glassfish_service.py      # Lógica de serviços e verificações
│   ├── glassfish_config.py       # Configurações e constantes
│   ├── glassfish_models.py       # Modelos de dados (UsageData)
│   ├── glassfish_ui.py           # Componentes de interface (botões, dropdowns)
│   ├── glassfish_admin_ui.py     # Interface administrativa
│   ├── test_glassfish.py         # Componentes para testes
│   ├── help.py                   # Sistema de ajuda
│   └── outros_cogs.py            # Outros comandos do bot
├── config.json                   # Configurações gerais (cargos, canais, timeouts)
├── services.json                 # Configuração dos serviços Glassfish
├── token.txt                     # Token do bot
├── requirements.txt              # Dependências do projeto
├── logs/                         # Logs do sistema
├── data/                         # Dados persistentes
├── assets/                       # Recursos (imagens, etc.)
└── venv/                         # Ambiente virtual
```

### Arquitetura Modular

O sistema Glassfish foi completamente refatorado em uma arquitetura modular:

- **`glassfish.py`**: Cog principal que orquestra todas as funcionalidades
- **`glassfish_commands.py`**: Implementa todos os comandos slash
- **`glassfish_service.py`**: Gerencia a lógica de negócio dos serviços
- **`glassfish_config.py`**: Centraliza configurações e constantes
- **`glassfish_models.py`**: Define modelos de dados como UsageData
- **`glassfish_ui.py`**: Componentes básicos de interface
- **`glassfish_admin_ui.py`**: Interface para administração
- **`test_glassfish.py`**: Ferramentas para desenvolvimento e testes

## Comandos Disponíveis

### 👥 Comandos para Usuários

- **`/glassfish`** - Interface principal para gerenciar serviços
- **`/obter_timeout_glassfish`** - Visualiza configurações de timeout
- **`/ajuda`** - Sistema de ajuda completo
- **`/sobre`** - Informações sobre o bot

### 🔧 Comandos Administrativos (apenas TI)

- **`/recarregar_config_glassfish`** - Recarrega configurações do arquivo
- **`/verificacao_forcada_glassfish`** - Força verificação de timeout
- **`/configurar_timeout_glassfish`** - Configura tempos de uso e lembretes
- **`/liberar_todos_glassfish`** - Libera todos os serviços em uso
- **`/adicionar_glassfish`** - Adiciona novo serviço
- **`/editar_glassfish`** - Edita serviço existente
- **`/remover_glassfish`** - Remove serviço
- **`/relatorio_glassfish`** - Gera relatório de uso detalhado

### 🧪 Comandos de Desenvolvimento (apenas TI)

- **`/modo_desenvolvimento_glassfish`** - Ativa/desativa modo de desenvolvimento
- **`/simular_tempo_glassfish`** - Simula tempo de uso para testes
- **`/status_servico_glassfish`** - Status detalhado de um serviço específico
- **`/testar_lembrete_glassfish`** - Testa sistema de lembretes
- **`/testar_envio_lembrete_glassfish`** - Teste direto de envio de lembrete

## Configurações

### config.json

```json
{
  "cargos": {
    "ti_id": 994300483348996176
  },
  "canais": {
    "logs_id": 994341371634782279,
    "persistent_id": 994299965323091968
  },
  "timeout": {
    "tempo_maximo_uso": 24,
    "verificar_intervalo": 15,
    "lembrete_intervalo": 2,
    "max_extensoes": 3
  }
}
```

### services.json

```json
{
  "97-1": {
    "nome": "Glassfish 97 - Domain: Neosistemas - Porta: 4848",
    "status": "disponível",
    "usuario": null,
    "grupos_permitidos": ["994300483348996176", "1234567890123456789"]
  }
}
```

## Sistema de Timeout e Lembretes

O sistema implementa um controle inteligente de uso dos serviços:

1. **Verificação Automática**: A cada 15 minutos (configurável)
2. **Lembretes Periódicos**: A cada 2 horas (configurável)
3. **Liberação Automática**: Após 24 horas sem confirmação (configurável)
4. **Sistema de Extensões**: Até 3 extensões permitidas por padrão
5. **Notificações por DM**: Usuários recebem lembretes e avisos

### Modo de Desenvolvimento

Para facilitar testes, o sistema inclui um modo de desenvolvimento:

- Tempos reduzidos (1-2 horas vs 24 horas)
- Verificações mais frequentes (1 minuto vs 15 minutos)
- Comandos de simulação de tempo
- Testes diretos de funcionalidades

## Como Rodar o Bot

### 1. Clone o Repositório

```bash
git clone git@github.com:Abnerlucasm/bot_discord_neo.git
cd bot_discord_neo
```

### 2. Configure o Ambiente

1. **Crie um ambiente virtual**:
   ```bash
   python3 -m venv venv
   ```

2. **Ative o ambiente virtual**:
   ```bash
   # Linux/MacOS:
   source venv/bin/activate
   # Windows:
   venv\Scripts\activate
   ```

3. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Configure os Arquivos

1. **Configure `config.json`** com os IDs dos seus cargos e canais
2. **Configure `services.json`** com seus serviços Glassfish
3. **Crie `token.txt`** com o token do seu bot

### 4. Execute o Bot

```bash
python main.py
```

## Como Criar um Serviço para o Bot no Linux

1. Crie um arquivo de serviço:

```bash
sudo nano /etc/systemd/system/bot_discord_neo.service
```

2. Adicione o conteúdo:

```ini
[Unit]
Description=Bot Discord Neo
After=network.target

[Service]
ExecStart=/usr/bin/python3 /caminho/para/seu/bot/main.py
WorkingDirectory=/caminho/para/seu/bot
Restart=always
User=seu_usuario
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

3. Ative e inicie o serviço:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bot_discord_neo
sudo systemctl start bot_discord_neo
sudo systemctl status bot_discord_neo
```

## Desenvolvimento e Testes

Para desenvolvedores e administradores:

1. **Ative o modo de desenvolvimento**:
   ```
   /modo_desenvolvimento_glassfish ativar:True
   ```

2. **Simule tempo de uso**:
   ```
   /simular_tempo_glassfish servico_id:97-1 horas_atras:3
   ```

3. **Force verificação**:
   ```
   /verificacao_forcada_glassfish
   ```

4. **Teste lembretes**:
   ```
   /testar_envio_lembrete_glassfish
   ```

## Como Funciona

Utilize o comando **`/ajuda`** ou **`/sobre`** para mais detalhes e explicações de cada comando.

O sistema funciona de forma totalmente automatizada:
- Usuários solicitam serviços via interface visual
- Sistema monitora uso e envia lembretes automáticos
- Liberação automática após timeout configúravel
- Logs completos de todas as ações
- Interface administrativa para gestão

## Considerações

- **Permissões do Bot**: O bot precisa ter permissões adequadas para enviar mensagens e DMs
- **IDs de Cargos e Canal**: Configuráveis nos arquivos de configuração
- **Backup**: Recomenda-se backup regular dos arquivos JSON
- **Logs**: Sistema gera logs detalhados para auditoria

## Documentação Adicional

- **[Guia de Desenvolvimento e Testes](DESENVOLVIMENTO.md)** - Documentação completa para desenvolvimento, testes e debugging do sistema Glassfish

## Contribuindo

Sinta-se à vontade para fazer contribuições! Abra uma issue ou envie um pull request para adicionar novas funcionalidades ou corrigir problemas.

Para desenvolvedores, consulte o [Guia de Desenvolvimento](DESENVOLVIMENTO.md) para informações sobre testes e debugging.

## Licença

Este projeto está sob a [Licença MIT](LICENSE).
