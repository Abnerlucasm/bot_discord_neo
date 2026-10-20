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
- **Dependência de execução**: `discord.py` (versão `2.7.1`)
  
Os módulos `json`, `asyncio` e `logging` fazem parte da biblioteca padrão do Python. Instale a dependência do bot em um ambiente virtual:

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
bot_discord_neo/
│
├── main.py
├── cogs/
│   ├── glassfish/
│   │   ├── __init__.py
│   │   ├── cog.py
│   │   ├── commands/
│   │   │   ├── admin.py
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── user.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── contracts.py
│   │   │   ├── models.py
│   │   │   ├── monitoring.py
│   │   │   ├── ownership.py
│   │   │   ├── permissions.py
│   │   │   ├── repository.py
│   │   │   └── service.py
│   │   └── ui/
│   │       ├── problem_report.py
│   │       ├── role_permissions.py
│   │       ├── service_actions.py
│   │       ├── service_admin.py
│   │       ├── service_forms.py
│   │       ├── service_select.py
│   │       └── tests.py
│   ├── help.py
│   ├── help_topics/
│   │   ├── __init__.py
│   │   ├── agendamentos.py
│   │   ├── glassfish_admin.py
│   │   ├── glassfish_development.py
│   │   ├── glassfish_user.py
│   │   ├── geral.py
│   │   └── overview.py
│   ├── interaction_handler.py
│   ├── persistence.py
│   ├── schedule_update.py
│   ├── schedule_ui/
│   │   ├── __init__.py
│   │   ├── agendamento_confirm.py
│   │   ├── agendamento.py
│   │   ├── atualizacao.py
│   │   ├── beta99.py
│   │   ├── components.py
│   │   └── constants.py
│   └── utils.py
├── docs/
│   └── desenvolvimento.md
├── examples/
│   └── novo_comando.py
├── assets/
│   └── logo.jpg
├── requirements.txt
├── .gitignore
└── README.md
```

Os arquivos `config.json`, `services.json` e `token.txt`, além das pastas `data/` e `logs/`, são usados em execução e não fazem parte do código versionado.
O diretório `examples/` contém um modelo para adicionar comandos ao bot.

### Camadas do Glassfish

- **`glassfish/cog.py`** integra os comandos ao Discord e controla o ciclo de vida do serviço.
- **`glassfish/commands/`** separa comandos de usuário, administração e desenvolvimento.
- **`glassfish/core/`** define contratos, configuração, modelos, permissões e repositório. `service.py` coordena o serviço e `monitoring.py` processa timeouts e lembretes.
- **`glassfish/ui/`** concentra os formulários, seletores e botões dos fluxos de serviço.
- **`help_topics/`** separa o conteúdo do comando `/ajuda` por assunto.
- **`schedule_ui/`** separa componentes compartilhados dos fluxos de agendamento, atualização e versão beta.
- **`persistence.py`** restaura as views das mensagens. **`interaction_handler.py`** registra essa restauração uma vez no ciclo de vida do bot.

Os comandos de serviço mantêm os nomes atuais. Os seletores com opções dinâmicas mostram até 25 itens por página e os autocompletes respeitam o limite de 25 opções. A lista pública valida novamente os cargos antes de permitir o uso, e a configuração administrativa usa o seletor nativo de cargos do Discord. A autorização de quem reservou um serviço usa o ID do Discord, com compatibilidade para registros antigos que ainda não armazenam esse ID. Os formulários usam `Label` e anexos opcionais com `FileUpload`, disponíveis na versão fixada de `discord.py`.

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

- Tempo máximo reduzido (1 hora vs 24 horas)
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
- Liberação automática após timeout configurável
- Logs completos de todas as ações
- Interface administrativa para gestão

## Considerações

- **Permissões do Bot**: O bot precisa ter permissões adequadas para enviar mensagens e DMs
- **IDs de Cargos e Canal**: Configuráveis nos arquivos de configuração
- **Backup**: Recomenda-se backup regular dos arquivos JSON
- **Logs**: Sistema gera logs detalhados para auditoria

## Documentação Adicional

- **[Guia de Desenvolvimento e Testes](docs/desenvolvimento.md)** - Configuração do modo de desenvolvimento e cenários operacionais.

## Contribuindo

Sinta-se à vontade para fazer contribuições! Abra uma issue ou envie um pull request para adicionar novas funcionalidades ou corrigir problemas.

Para desenvolvedores, consulte o [Guia de Desenvolvimento](docs/desenvolvimento.md) antes de alterar as configurações de execução.
