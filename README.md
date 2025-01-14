
<img src="./icons/Discord.svg" width="48"> # Bot Discord Neo

Este é um bot do Discord para gerenciar serviços em um servidor, permitindo que os usuários reservem e liberem serviços de acordo com suas permissões.

## Funcionalidades

- **Visualização e seleção de serviços**: Usuários podem visualizar serviços disponíveis com base nos cargos que possuem no Discord.
- **Reservar serviço**: Usuários podem reservar serviços disponíveis para usá-los.
- **Liberar serviço**: Usuários podem liberar serviços reservados, permitindo que outros os utilizem.
- **Notificações**: O bot envia notificações para um canal específico sempre que um serviço é reservado ou liberado.

## Requisitos

- **Python 3.8 ou superior**
- **Bibliotecas necessárias**:
  - `discord.py`
  - `json`
  - `asyncio`
  
Você pode instalar as dependências necessárias criando um ambiente virtual (recomendado) e utilizando o `pip`:

<img src="./icons/Bash-Dark.svg" width="48">

```bash
# Criação do ambiente virtual
python3 -m venv venv

# Ativação do ambiente virtual
# Linux/MacOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instalação das dependências
pip install discord.py
```

## Estrutura do Projeto

```plaintext
/bot_Discord_Neo
│
├── bot.py               # Código principal do bot
├── services.json        # Arquivo JSON com a configuração dos serviços
├── token.txt            # Arquivo contendo o token do bot
└── venv/                # Ambiente virtual
```

- **`bot.py`**: Contém o código do bot, que gerencia as interações com o Discord.
- **`services.json`**: Configurações dos serviços, incluindo nomes, status e permissões.
- **`token.txt`**: Contém o token do bot para autenticação no Discord.

## Como Rodar o Bot

### 1. Clone o Repositório

Clone o repositório para a sua máquina:

<img src="./icons/Bash-Dark.svg" width="48">

```bash
git clone git@github.com:Abnerlucasm/bot_discord_neo.git
cd bot_discord_neo
```

<img src="./icons/Bash-Dark.svg" width="48"> ### 2. Configure o Ambiente

1. **Crie um ambiente virtual** (caso não tenha feito):

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
   pip install discord.py
   ```

### 3. Configure o Arquivo de Serviços

Edite o arquivo `services.json` para incluir os serviços disponíveis e os cargos que podem acessá-los. Exemplo:

```json
{
  "service_1": {
    "nome": "Serviço 1",
    "status": "disponível",
    "usuario": null,
    "grupos_permitidos": [123456789012345678, 987654321098765432]
  },
  "service_2": {
    "nome": "Serviço 2",
    "status": "em uso",
    "usuario": "usuario_teste",
    "grupos_permitidos": [112233445566778899]
  }
}
```

### 4. Configure o Token do Bot

Crie um arquivo `token.txt` na raiz do projeto e adicione o **token** do seu bot (obtido ao registrar seu bot no [Portal de Desenvolvedor do Discord](https://discord.com/developers/applications)):

```plaintext
YOUR_BOT_TOKEN_HERE
```

### 5. Execute o Bot

Para rodar o bot, execute o seguinte comando no diretório onde o `bot.py` está localizado:

```bash
python bot.py
```

O bot estará em execução e aguardando interações no servidor do Discord.

## Como Criar um Serviço para o Bot no Linux

1. Crie um arquivo de serviço no diretório `/etc/systemd/system/`:

```bash
sudo nano /etc/systemd/system/bot_discord_neo.service
```

2. Adicione o seguinte conteúdo ao arquivo:

```ini
[Unit]
Description=Bot Discord Neo
After=network.target

[Service]
ExecStart=/usr/bin/python3 /caminho/para/seu/bot/bot.py
WorkingDirectory=/caminho/para/seu/bot
Restart=always
User=seu_usuario
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

Substitua `/caminho/para/seu/bot` pelo caminho completo do diretório onde está o bot e `seu_usuario` pelo nome do usuário que executará o bot.

3. Salve e feche o arquivo.

4. Recarregue o `systemd` para reconhecer o novo serviço:

```bash
sudo systemctl daemon-reload
```

5. Ative o serviço para que ele inicie automaticamente ao ligar o sistema:

```bash
sudo systemctl enable bot_discord_neo
```

6. Inicie o serviço:

```bash
sudo systemctl start bot_discord_neo
```

7. Verifique o status do serviço:

```bash
sudo systemctl status bot_discord_neo
```

Se configurado corretamente, o bot será executado automaticamente em segundo plano e reiniciará em caso de falha.

## Como Funciona

### Comando `/glassfish`

O comando `/glassfish` lista os serviços disponíveis para o usuário, baseado nos cargos que ele possui. O bot apresentará uma lista de serviços e permitirá ao usuário selecionar um.

### Ações de "Usar" e "Liberar"

- **Usar**: Se o serviço estiver disponível, o usuário pode "reservá-lo" para uso. Isso alterará o status do serviço para "em uso".
- **Liberar**: Caso o serviço esteja em uso, o usuário poderá liberá-lo, alterando seu status para "disponível".

### Redirecionamento de Notificações

Sempre que um serviço for utilizado ou liberado, o bot enviará uma notificação para um canal específico no servidor, informando a alteração no status do serviço.

## Comandos

- **`/glassfish`**: Lista os serviços disponíveis com base nos cargos do usuário.
- **Botões de Ação**:
  - **Usar**: Reserva o serviço.
  - **Liberar**: Libera o serviço para outros usuários.

## Considerações

- **Permissões do Bot**: O bot precisa ter permissões adequadas para enviar mensagens no canal de destino.
- **IDs de Cargos e Canal**: Os IDs de cargos e canais são configuráveis no arquivo `services.json`.

## Contribuindo

Sinta-se à vontade para fazer contribuições! Abra uma issue ou envie um pull request para adicionar novas funcionalidades ou corrigir problemas.

## Licença

Este projeto está sob a [Licença MIT](LICENSE).
