# cogs/glassfish.py
import discord
from discord.ext import commands
from discord import app_commands
import logging
import json

CARGO_TI_ID = 1327312138573713449

class ServiceDropdown(discord.ui.View):
    def __init__(self, user_roles, servicos_config):
        super().__init__(timeout=None)
        self.add_item(ServiceSelect(user_roles, servicos_config))

class ServiceSelect(discord.ui.Select):
    def __init__(self, user_roles, servicos_config):
        servicos_permitidos = {}
        for key, config in servicos_config.items():
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
        self.servicos_config = servicos_config
    
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("Não há serviços disponíveis para você.", ephemeral=True)
            return
            
        servico_selecionado = self.values[0]
        config = self.servicos_config[servico_selecionado]
        status_emoji = "🔴" if config["status"] == "em uso" else "🟢"
        usuario_atual = (
            f" (Em uso por: {config['usuario']})" 
            if config["status"] == "em uso" 
            else ""
        )
        logging.info(f"{interaction.user.name} selecionou o serviço: {config['nome']} (Status: {config['status']})")
        view = ActionButtons(servico_selecionado, self.servicos_config)
        await interaction.response.send_message(
            f"{status_emoji} Você selecionou o serviço **{config['nome']}**. Status atual: **{config['status']}**{usuario_atual}. Escolha uma ação:",
            view=view,
            ephemeral=True,
        )

class ActionButtons(discord.ui.View):
    def __init__(self, servico, servicos_config):
        super().__init__(timeout=None)
        self.servico = servico
        self.servicos_config = servicos_config
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
        config = self.servicos_config[self.servico]
        if config["status"] == "em uso":
            await interaction.response.send_message(
                f"O serviço **{config['nome']}** já está em uso por {config['usuario']}.",
                ephemeral=True,
            )
            logging.info(f"{interaction.user.name} tentou usar {config['nome']}, mas já está em uso")
        else:
            config["status"] = "em uso"
            config["usuario"] = interaction.user.name
            self.salvar_em_json()
            channel = interaction.guild.get_channel(1328462406996725913)
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
        config = self.servicos_config[self.servico]
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
            self.salvar_em_json()
            channel = interaction.guild.get_channel(1328462406996725913)
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
        config = self.servicos_config[self.servico]
        try:
            guild = interaction.guild
            role = guild.get_role(CARGO_TI_ID)
            if role:
                mensagem = f"⚠️ Problema reportado no serviço **{config['nome']}** por <@{interaction.user.id}>. Aviso para o setor de TI: <@&{CARGO_TI_ID}>"
                channel = guild.get_channel(1328462406996725913)
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

    def salvar_em_json(self):
        try:
            with open("services.json", "w", encoding="utf-8") as file:
                json.dump(self.servicos_config, file, indent=4)
            logging.info("Configurações salvas com sucesso em services.json")
        except Exception as e:
            logging.error(f"Erro ao salvar em services.json: {str(e)}")

class GlassfishCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="glassfish", description="Lista os serviços disponíveis")
    async def glassfish(self, interaction: discord.Interaction):
        try:
            logging.info(f"{interaction.user.name} executou o comando /glassfish")
            
            if not interaction.user.roles:
                await interaction.response.send_message(
                    "Você precisa ter um cargo para acessar os serviços.",
                    ephemeral=True
                )
                return
                
            user_roles = [role.id for role in interaction.user.roles]
            servicos_permitidos = {
                key: config for key, config in self.bot.servicos_config.items()
                if any(int(role) in [int(x) for x in config["grupos_permitidos"]] for role in user_roles)
            }
            
            if not servicos_permitidos:
                await interaction.response.send_message(
                    "Você não tem permissão para acessar nenhum serviço.",
                    ephemeral=True
                )
                logging.info(f"{interaction.user.name} tentou acessar serviços sem permissão")
                return
            
            view = ServiceDropdown(user_roles, self.bot.servicos_config)
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
