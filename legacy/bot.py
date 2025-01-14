import discord
from discord import app_commands
import json

# Carregar o arquivo de configuração dos serviços (fora de qualquer função)
try:
    with open("config.json", "r") as file:
        SERVICOS_CONFIG = json.load(file)
    print("Configuração dos serviços carregada com sucesso.")
except FileNotFoundError:
    print("Erro: arquivo config.json não encontrado!")
except Exception as e:
    print(f"Erro ao carregar o config.json: {e}")

class ServiceSelect(discord.ui.Select):
    def __init__(self, user_roles):
        # Filtra serviços permitidos baseado nos roles do usuário
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
            options=options
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
            ephemeral=True
        )

class ServiceView(discord.ui.View):
    def __init__(self, user_roles):
        super().__init__()
        self.add_item(ServiceSelect(user_roles))

class ActionButtons(discord.ui.View):
    def __init__(self, servico):
        super().__init__()
        self.servico = servico

    @discord.ui.button(label="Usar", style=discord.ButtonStyle.primary)
    async def usar(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = SERVICOS_CONFIG[self.servico]
        if config["status"] == "em uso":
            await interaction.response.send_message(
                f"O serviço **{config['nome']}** já está em uso por {config['usuario']}.",
                ephemeral=True
            )
        else:
            config["status"] = "em uso"
            config["usuario"] = interaction.user.name
            await interaction.response.send_message(
                f"O serviço **{config['nome']}** está sendo usado por {interaction.user.name}",
                ephemeral=False
            )

    @discord.ui.button(label="Liberar", style=discord.ButtonStyle.success)
    async def liberar(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = SERVICOS_CONFIG[self.servico]
        if config["status"] == "disponível":
            await interaction.response.send_message(
                f"O serviço **{config['nome']}** já está disponível.",
                ephemeral=True
            )
        elif config["usuario"] != interaction.user.name:
            await interaction.response.send_message(
                f"Apenas {config['usuario']} pode liberar este serviço.",
                ephemeral=True
            )
        else:
            config["status"] = "disponível"
            config["usuario"] = None
            await interaction.response.send_message(
                f"O serviço **{config['nome']}** foi liberado por {interaction.user.name}",
                ephemeral=False
            )

class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = Bot()

@client.event
async def on_ready():
    print(f"{client.user} está pronto!")
    print("Comandos sincronizados globalmente")

@client.tree.command(name="glassfish", description="Gerenciar instâncias do Glassfish")
async def glassfish(interaction: discord.Interaction):
    # Pega os cargos do usuário
    user_roles = [role.id for role in interaction.user.roles]
    print("Cargos do usuário:", user_roles)  # Adiciona essa linha para depuração
    
    # Verifica se o usuário tem permissão para acessar algum serviço
    tem_permissao = any(
        any(role in config["grupos_permitidos"] for role in user_roles)
        for config in SERVICOS_CONFIG.values()
    )

    if not tem_permissao:
        await interaction.response.send_message(
            "Você não tem permissão para acessar nenhum serviço.",
            ephemeral=True
        )
        return

    view = ServiceView(user_roles)
    await interaction.response.send_message(
        "**Serviços disponíveis:** Selecione uma opção abaixo:",
        view=view,
        ephemeral=True
    )

# Carregar o token a partir do arquivo token.txt
try:
    with open("token.txt", "r") as file:
        token = file.read().strip()
    client.run(token)
except FileNotFoundError:
    print("Erro: arquivo token.txt não encontrado!")
except Exception as e:
    print(f"Erro ao carregar o token: {e}")
