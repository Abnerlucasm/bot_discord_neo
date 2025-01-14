import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
import logging

# Configuração do sistema de log
logging.basicConfig(
    filename="glassfish.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Carregar configurações do arquivo JSON
try:
    with open("services.json", "r", encoding="utf-8") as file:
        SERVICOS_CONFIG = json.load(file)
    logging.info("Arquivo services.json carregado com sucesso")
except Exception as e:
    logging.error(f"Erro ao carregar services.json: {str(e)}")
    SERVICOS_CONFIG = {}

# Inicializando os intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
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
        
        if not options:
            options = [discord.SelectOption(label="Sem serviços disponíveis", value="none")]
        
        super().__init__(
            placeholder="Selecione um serviço...",
            min_values=1,
            max_values=1,
            options=options,
        )
    
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("Não há serviços disponíveis para você.", ephemeral=True)
            return
            
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
        button = discord.ui.Button(label=label, emoji=emoji, style=style, custom_id=custom_id)
        button.callback = self.handle_callback
        return button

    async def handle_callback(self, interaction: discord.Interaction):
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
            logging.info(f"{interaction.user.name} tentou usar {config['nome']}, mas já está em uso")
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
            logging.info(f"{interaction.user.name} começou a usar o serviço {config['nome']}")

    async def liberar(self, interaction: discord.Interaction):
        config = SERVICOS_CONFIG[self.servico]
        if config["status"] == "disponível":
            await interaction.response.send_message(
                f"O serviço **{config['nome']}** já está disponível.",
                ephemeral=True,
            )
            logging.info(f"{interaction.user.name} tentou liberar {config['nome']}, mas já está disponível")
        elif config["usuario"] != interaction.user.name:
            await interaction.response.send_message(
                f"Apenas {config['usuario']} pode liberar este serviço.",
                ephemeral=True,
            )
            logging.warning(f"{interaction.user.name} tentou liberar {config['nome']}, mas não tem permissão")
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
            logging.info(f"{interaction.user.name} liberou o serviço {config['nome']}")

    async def reportar_problema(self, interaction: discord.Interaction):
        config = SERVICOS_CONFIG[self.servico]
        try:
            guild = interaction.guild
            role = guild.get_role(CARGO_TI_ID)
            if role:
                mensagem = f"⚠️ Problema reportado no serviço **{config['nome']}** por <@{interaction.user.id}>."
                channel = bot.get_channel(1328462406996725913)
                if channel:
                    await channel.send(mensagem)
                await interaction.response.send_message(
                    f"Problema reportado para o setor de TI.",
                    ephemeral=True
                )
                logging.info(f"{interaction.user.name} reportou um problema com {config['nome']}")
        except Exception as e:
            logging.error(f"Erro ao reportar problema: {str(e)}")
            await interaction.response.send_message(
                "Ocorreu um erro ao reportar o problema. Tente novamente mais tarde.",
                ephemeral=True
            )

@bot.event
async def on_ready():
    try:
        print(f'{bot.user} está pronto!')
        logging.info(f'Bot iniciado como {bot.user}')
        
        # Registrar o comando glassfish
        comando_glassfish = app_commands.Command(
            name="glassfish",
            description="Lista os serviços disponíveis",
            callback=glassfish
        )
        bot.tree.add_command(comando_glassfish)
        
        await bot.tree.sync()
        print("Comandos sincronizados globalmente.")
        logging.info("Comandos sincronizados globalmente com sucesso")
        
    except Exception as e:
        print(f"Erro durante a inicialização: {str(e)}")
        logging.error(f"Erro durante a inicialização: {str(e)}")

async def glassfish(interaction: discord.Interaction):
    try:
        logging.info(f"{interaction.user.name} executou o comando /glassfish")
        
        # Verificar se o usuário tem algum cargo
        if not interaction.user.roles:
            await interaction.response.send_message(
                "Você precisa ter um cargo para acessar os serviços.",
                ephemeral=True
            )
            return
            
        user_roles = [role.id for role in interaction.user.roles]
        servicos_permitidos = {
            key: config for key, config in SERVICOS_CONFIG.items()
            if any(int(role) in [int(x) for x in config["grupos_permitidos"]] for role in user_roles)
        }
        
        if not servicos_permitidos:
            await interaction.response.send_message(
                "Você não tem permissão para acessar nenhum serviço.",
                ephemeral=True
            )
            logging.info(f"{interaction.user.name} tentou acessar serviços sem permissão")
            return
        
        view = ServiceDropdown(user_roles)
        await interaction.response.send_message(
            "**Serviços disponíveis:** Selecione uma opção abaixo:", 
            view=view,
            ephemeral=True
        )
        
    except Exception as e:
        logging.error(f"Erro ao executar comando glassfish: {str(e)}")
        await interaction.response.send_message(
            "Ocorreu um erro ao listar os serviços. Tente novamente mais tarde.",
            ephemeral=True
        )

def salvar_em_json():
    try:
        with open("services.json", "w", encoding="utf-8") as file:
            json.dump(SERVICOS_CONFIG, file, indent=4)
        logging.info("Configurações salvas com sucesso em services.json")
    except Exception as e:
        logging.error(f"Erro ao salvar em services.json: {str(e)}")

# Carregar e executar o bot
try:
    with open("token.txt", "r") as file:
        token = file.read().strip()
    logging.info("Token carregado com sucesso")
    bot.run(token)
except Exception as e:
    logging.error(f"Erro ao carregar/executar o bot: {str(e)}")