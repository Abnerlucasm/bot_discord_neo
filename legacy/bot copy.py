import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True  # Habilitando a permissão de conteúdo de mensagens
bot = commands.Bot(command_prefix="/", intents=intents)

# Estrutura unificada de serviços
SERVICOS_CONFIG = {
    "247 - 1": {
        "nome": "Glassfish 247 - Instância 1",
        "status": "disponível",
        "usuario": None,
        "grupos_permitidos": [994300483348996176]
    },
    "247 - 2": {
        "nome": "Glassfish 247 - Instância 2",
        "status": "disponível",
        "usuario": None,
        "grupos_permitidos": [994300483348996176]
    },
    "247 - 3": {
        "nome": "Glassfish 247 - Instância 3",
        "status": "disponível",
        "usuario": None,
        "grupos_permitidos": [994300483348996176]
    },
    "248 - 1": {
        "nome": "Glassfish 248 - Instância 1",
        "status": "disponível",
        "usuario": None,
        "grupos_permitidos": [994341371634782279]
    },
    "248 - 2": {
        "nome": "Glassfish 248 - Instância 2",
        "status": "disponível",
        "usuario": None,
        "grupos_permitidos": [994341371634782279]
    },
    "248 - 3": {
        "nome": "Glassfish 248 - Instância 3",
        "status": "disponível",
        "usuario": None,
        "grupos_permitidos": [994341371634782279]
    },
    "40 - 1": {
        "nome": "Glassfish 40 - Instância 1",
        "status": "disponível",
        "usuario": None,
        "grupos_permitidos": [994341371634782279]
    },
    "40 - 2": {
        "nome": "Glassfish 40 - Instância 2",
        "status": "disponível",
        "usuario": None,
        "grupos_permitidos": [994341371634782279]
    },
    "40 - 3": {
        "nome": "Glassfish 40 - Instância 3",
        "status": "disponível",
        "usuario": None,
        "grupos_permitidos": [994341371634782279]
    },
    "249 - 1": {
        "nome": "Glassfish 249 - Instância 1",
        "status": "disponível",
        "usuario": None,
        "grupos_permitidos": [994341371634782279]
    },
    "249 - 2": {
        "nome": "Glassfish 249 - Instância 2",
        "status": "disponível",
        "usuario": None,
        "grupos_permitidos": [994341371634782279]
    },
    "249 - 3": {
        "nome": "Glassfish 249 - Instância 3",
        "status": "disponível",
        "usuario": None,
        "grupos_permitidos": [994341371634782279]
    }
}

# Usar uma variável global para mapear usuários
usuario_servico = {}

# Defina os IDs dos cargos e seus serviços permitidos
PERMISSOES_SERVICOS = {
    994300483348996176: ["247 - 1", "247 - 2", "247 - 3", "248 - 1", "248 - 2", "248 - 3", "249 - 1", "249 - 2", "249 - 3"],
    994341371634782279: ["40 - 1", "40 - 2", "40 - 3"]
}

class ServiceDropdown(discord.ui.View):
    def __init__(self, user_roles):
        super().__init__(timeout=None)
        self.add_item(ServiceSelect(user_roles))

class ServiceSelect(discord.ui.Select):
    def __init__(self, user_roles):
        servicos_permitidos = {
            key: config for key, config in SERVICOS_CONFIG.items()
            if any(role in config["grupos_permitidos"] for role in user_roles)
        }

        options = [
            discord.SelectOption(
                label=config["nome"],
                value=key,
                description=(
                    f"Em uso por: {config['usuario']}" 
                    if config["status"] == "em uso" 
                    else "Disponível"
                ),
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
                f"O serviço **{config['nome']}** está sendo usado por {interaction.user.name}",
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
                f"O serviço **{config['nome']}** foi liberado por {interaction.user.name}",
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
    
    # Verifica se o usuário tem algum cargo com permissão
    tem_permissao = any(role_id in PERMISSOES_SERVICOS for role_id in user_roles)
    
    if not tem_permissao:
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
