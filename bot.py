import discord
from discord.ext import commands
import asyncio
import json
import logging
import uuid

# Configuração do sistema de log
logging.basicConfig(
    filename="glassfish.log",  # Nome do arquivo de log
    level=logging.INFO,        # Nível do log
    format="%(asctime)s - %(levelname)s - %(message)s",  # Formato das mensagens
)

# Carregar configurações do arquivo JSON
with open("services.json", "r", encoding="utf-8") as file:
    SERVICOS_CONFIG = json.load(file)

intents = discord.Intents.default()
intents.message_content = True  # Habilitando a permissão de conteúdo de mensagens
bot = commands.Bot(command_prefix="/", intents=intents)

# ID do cargo do setor de TI que receberá as notificações
CARGO_TI_ID = 1327312138573713449  

# Usar uma variável global para mapear usuários
usuario_servico = {}

class ServiceDropdown(discord.ui.View):
    def __init__(self, user_roles):
        super().__init__(timeout=None)
        self.add_item(ServiceSelect(user_roles))

class ServiceSelect(discord.ui.Select):
    def __init__(self, user_roles):
        servicos_permitidos = {}
        for key, config in SERVICOS_CONFIG.items():
            for role in user_roles:
                if int(role) in [int(x) for x in config["grupos_permitidos"]]:
                    servicos_permitidos[key] = config
                    break
        
        options = [
            discord.SelectOption(
                label=config["nome"],
                value=key,
                description=(f"Em uso por: {config['usuario']}" if config["status"] == "em uso" else "Disponível"),
                emoji="🔴" if config["status"] == "em uso" else "🟢"
            )
            for key, config in servicos_permitidos.items()
        ]
        
        super().__init__(
            placeholder="Selecione um serviço...",
            min_values=1,
            max_values=1,
            options=options,
        )
        
    async def callback(self, interaction: discord.Interaction):
        servico_selecionado = self.values[0]
        config = SERVICOS_CONFIG[servico_selecionado]
        status_emoji = "🔴" if config["status"] == "em uso" else "🟢"
        usuario_atual = (
            f" (Em uso por: {config['usuario']})" 
            if config["status"] == "em uso" 
            else ""
        )
        logging.info(f"{interaction.user.name} selecionou o serviço: {config['nome']} (Status: {config['status']})")
        view = ActionButtons(servico_selecionado)
        await interaction.response.send_message(
            f"{status_emoji} Você selecionou o serviço **{config['nome']}**. Status atual: **{config['status']}**{usuario_atual}. Escolha uma ação:",
            view=view,
            ephemeral=True,
        )

class ActionButtons(discord.ui.View):
    def __init__(self, servico):
        super().__init__(timeout=None)
        self.servico = servico
        self.add_item(self.create_button("Usar", "❎", discord.ButtonStyle.primary, f"usar_{servico}"))
        self.add_item(self.create_button("Liberar", "✅", discord.ButtonStyle.success, f"liberar_{servico}"))
        self.add_item(self.create_button("Reportar problema", "⚠️", discord.ButtonStyle.danger, f"reportar_{servico}"))

    def create_button(self, label, emoji, style, custom_id):
        # Criação do botão com ID único e associação automática ao callback
        button = discord.ui.Button(label=label, emoji=emoji, style=style, custom_id=custom_id)
        button.callback = self.handle_callback  # Associar o método de callback
        return button

    async def handle_callback(self, interaction: discord.Interaction):
        # Defina a lógica do que fazer ao clicar em um botão
        custom_id = interaction.data["custom_id"]
        if "usar" in custom_id:
            await self.usar(interaction)
        elif "liberar" in custom_id:
            await self.liberar(interaction)
        elif "reportar" in custom_id:
            await self.reportar_problema(interaction)

    async def usar(self, interaction: discord.Interaction):
        config = SERVICOS_CONFIG[self.servico]
        if config["status"] == "em uso":
            await interaction.response.send_message(
                f"O serviço **{config['nome']}** já está em uso por {config['usuario']}.",
                ephemeral=True,
            )
        else:
            config["status"] = "em uso"
            config["usuario"] = interaction.user.name
            salvar_em_json()
            channel = bot.get_channel(1328462406996725913)
            if channel:
                await channel.send(
                    f"O serviço **{config['nome']}** está sendo usado por <@{interaction.user.id}> <:stop:1328441358188417025>"
                )
            await interaction.response.send_message(
                f"O serviço **{config['nome']}** está sendo usado por <@{interaction.user.id}> <:stop:1328441358188417025>",
                ephemeral=True,
            )

    async def liberar(self, interaction: discord.Interaction):
        config = SERVICOS_CONFIG[self.servico]
        if config["status"] == "disponível":
            await interaction.response.send_message(
                f"O serviço **{config['nome']}** já está disponível.",
                ephemeral=True,
            )
        elif config["usuario"] != interaction.user.name:
            await interaction.response.send_message(
                f"Apenas {config['usuario']} pode liberar este serviço.",
                ephemeral=True,
            )
        else:
            config["status"] = "disponível"
            config["usuario"] = None
            salvar_em_json()
            channel = bot.get_channel(1328462406996725913)
            if channel:
                await channel.send(
                    f"O serviço **{config['nome']}** foi liberado por <@{interaction.user.id}> <:start:1328441356682793062>"
                )
            await interaction.response.send_message(
                f"O serviço **{config['nome']}** foi liberado por <@{interaction.user.id}> <:start:1328441356682793062>",
                ephemeral=True,
            )

    async def reportar_problema(self, interaction: discord.Interaction):
        config = SERVICOS_CONFIG[self.servico]

        # Enviar notificação para os membros com o cargo de TI
        guild = interaction.guild
        role = guild.get_role(CARGO_TI_ID)

        if role:
            mensagem = (
                f"⚠️ Problema reportado no serviço **{config['nome']}** "
                f"por <@{interaction.user.id}>. Verificar o sistema! "
                f"Setor: <@&{role.id}>"
            )
            for member in role.members:
                try:
                    await member.send(mensagem)
                except discord.Forbidden:
                    print(f"Não foi possível enviar mensagem para {member}.")

            # Enviar a mesma mensagem para o canal específico
            channel = bot.get_channel(1328462406996725913)  # Substitua pelo ID do canal desejado
            if channel:
                await channel.send(mensagem)

                # Responder ao usuário que o problema foi reportado
        await interaction.response.send_message(
            f"O problema foi reportado ao setor responsável: **{role.name}**. ⚠️",
            ephemeral=True,
        )    

# Registrar o comando ao iniciar o bot
@bot.event
async def on_ready():
    print(f'{bot.user} está pronto!')

    # Aguarda alguns segundos para garantir que o bot tenha a permissão e os dados necessários
    await asyncio.sleep(2)  # Espera 2 segundos antes de registrar os comandos

    try:
        # Sincronizar globalmente os comandos
        await bot.tree.sync()
        print("Comandos sincronizados globalmente.")
    except discord.errors.Forbidden:
        print("O bot não tem permissão para acessar informações globais.")

# Definir o comando 'glassfish' com o app_commands
@bot.tree.command(name="glassfish", description="Lista os serviços disponíveis")
async def glassfish(interaction: discord.Interaction):
    # Obtém os IDs dos cargos do usuário
    user_roles = [role.id for role in interaction.user.roles]
    
    # Verifica os cargos do usuário
    print(f"Cargos do usuário: {user_roles}")
    
    # Filtra os serviços que o usuário tem permissão para acessar
    servicos_permitidos = {
        key: config for key, config in SERVICOS_CONFIG.items()
        if any(int(role) in [int(x) for x in config["grupos_permitidos"]] for role in user_roles)
    }
    
    # Debug: Verificando os cargos permitidos
    print(f"Serviços permitidos: {servicos_permitidos}")

    # Verifica se o usuário tem permissão
    if not servicos_permitidos:
        await interaction.response.send_message(
            "Você não tem permissão para acessar nenhum serviço.",
            ephemeral=True
        )
        return

    view = ServiceDropdown(user_roles)
    await interaction.response.send_message(
        "**Serviços disponíveis:** Selecione uma opção abaixo:", 
        view=view,
        ephemeral=True
    )

# Carregar o token a partir do arquivo token.txt
with open("token.txt", "r") as file:
    token = file.read().strip()  # Remove qualquer espaço extra

# Função para persistir as mudanças no arquivo JSON
def salvar_em_json():
    with open("services.json", "w", encoding="utf-8") as file:
        json.dump(SERVICOS_CONFIG, file, indent=4, ensure_ascii=False)

bot.run(token)
