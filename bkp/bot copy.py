import discord
from discord.ext import commands
import asyncio
import json

# Carregar configurações do arquivo JSON
with open("services.json", "r", encoding="utf-8") as file:
    SERVICOS_CONFIG = json.load(file)

intents = discord.Intents.default()
intents.message_content = True  # Habilitando a permissão de conteúdo de mensagens
bot = commands.Bot(command_prefix="/", intents=intents)

# Usar uma variável global para mapear usuários
usuario_servico = {}

class ServiceDropdown(discord.ui.View):
    def __init__(self, user_roles):
        super().__init__(timeout=None)
        self.add_item(ServiceSelect(user_roles))

class ServiceSelect(discord.ui.Select):
    def __init__(self, user_roles):
        # Filtra os serviços que o usuário tem permissão para acessar
        servicos_permitidos = {}
        for key, config in SERVICOS_CONFIG.items():
            for role in user_roles:
                # Convertendo as IDs de cargos para inteiro, caso elas sejam strings no arquivo JSON
                if int(role) in [int(x) for x in config["grupos_permitidos"]]:
                    servicos_permitidos[key] = config
                    break  # Se um cargo permitido for encontrado, adiciona o serviço
        
        # Debug: Verificando os cargos permitidos e cargos do usuário
        print(f"Serviços disponíveis para os cargos: {user_roles}")  # IDs dos cargos do usuário
        for key, config in SERVICOS_CONFIG.items():
            print(f"Serviço: {config['nome']}")
            print(f"Cargos permitidos: {config['grupos_permitidos']}")  # Mostrar os IDs dos cargos permitidos
            print(f"Cargos do usuário: {user_roles}")  # Mostrar os IDs dos cargos do usuário

        print(f"Serviços permitidos: {servicos_permitidos}")  # Mostrar os serviços permitidos após o filtro

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

    @discord.ui.button(label="Usar", style=discord.ButtonStyle.primary)
    async def usar(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = SERVICOS_CONFIG[self.servico]
        if config["status"] == "em uso":
            await interaction.response.send_message(
                f"O serviço **{config['nome']}** já está em uso por {config['usuario']}.",
                ephemeral=True,
            )
        else:
            config["status"] = "em uso"
            config["usuario"] = interaction.user.name
            await interaction.response.send_message(
                f"O serviço **{config['nome']}** está sendo usado por <@{interaction.user.id}> <:stop:1328441358188417025>",
                ephemeral=False,
            )

    @discord.ui.button(label="Liberar", style=discord.ButtonStyle.success)
    async def liberar(self, interaction: discord.Interaction, button: discord.ui.Button):
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
            await interaction.response.send_message(
                f"O serviço **{config['nome']}** foi liberado por <@{interaction.user.id}> <:start:1328441356682793062>",
                ephemeral=False,
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

bot.run(token)
