# cogs/schedule_update.py
from discord.ext import commands
from discord import app_commands
import discord
from datetime import datetime
import logging

CANAL_NOTIFICACOES = 997291234643148811

class EditButtons(discord.ui.View):
    def __init__(self, modal_type: str, original_data: dict):
        super().__init__(timeout=None)
        self.modal_type = modal_type
        self.original_data = original_data

    @discord.ui.button(label="Editar", style=discord.ButtonStyle.primary, emoji="✏️")
    async def edit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.modal_type == "agendamento":
            modal = AgendamentoModal()
            # Preenche o modal com os dados originais
            modal.cliente.default = self.original_data.get("cliente", "")
            modal.chamado.default = self.original_data.get("chamado", "")
            modal.data_agendamento.default = self.original_data.get("data_agendamento", "")
            modal.observacao.default = self.original_data.get("observacao", "")
        else:
            modal = AtualizacaoModal()
            # Preenche o modal com os dados originais
            modal.cliente.default = self.original_data.get("cliente", "")
            modal.versao_neocorp.default = self.original_data.get("versao_neocorp", "")
            modal.versao_neoweb.default = self.original_data.get("versao_neoweb", "")
            modal.versao_neocontabil.default = self.original_data.get("versao_neocontabil", "")
            modal.chamados.default = self.original_data.get("chamados", "")

        # Armazena a mensagem original para atualização
        modal.message_to_edit = interaction.message
        await interaction.response.send_modal(modal)

class AgendamentoModal(discord.ui.Modal, title='Agendamento'):
    def __init__(self):
        super().__init__()
        self.message_to_edit = None

    cliente = discord.ui.TextInput(
        label='Cliente',
        placeholder='Nome do cliente...',
        required=True,
    )
    
    chamado = discord.ui.TextInput(
        label='Chamado',
        placeholder='Número do chamado...',
        required=False,
    )
    
    data_agendamento = discord.ui.TextInput(
        label='Data Agendamento',
        placeholder='DD/MM/YYYY HH:MM',
        required=True,
    )
    
    observacao = discord.ui.TextInput(
        label='Observação',
        placeholder='Observações adicionais...',
        style=discord.TextStyle.paragraph,
        required=False,
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            try:
                datetime.strptime(str(self.data_agendamento), '%d/%m/%Y %H:%M')
            except ValueError:
                await interaction.response.send_message(
                    "Formato de data inválido. Use DD/MM/YYYY HH:MM",
                    ephemeral=True
                )
                return
            
            mensagem = (
                "**AGENDAMENTO**\n"
                f"**• Cliente:** {self.cliente}\n"
                f"**• Chamado:** {self.chamado}\n"
                f"**• Data Agendamento:** {self.data_agendamento}\n"
            )
            
            if self.observacao.value:
                mensagem += f"**• Observação:** {self.observacao}\n"

            # Dados originais para o botão de edição
            original_data = {
                "cliente": str(self.cliente),
                "chamado": str(self.chamado),
                "data_agendamento": str(self.data_agendamento),
                "observacao": str(self.observacao),
            }
            
            view = EditButtons("agendamento", original_data)
            
            if self.message_to_edit:
                # Se estiver editando, atualiza a mensagem existente
                await self.message_to_edit.edit(content=mensagem, view=view)
                await interaction.response.send_message(
                    "Agendamento atualizado com sucesso!",
                    ephemeral=True
                )
                logging.info(f"{interaction.user.name} atualizou um agendamento para {self.cliente}")
            else:
                # Se for nova mensagem, envia para o canal
                channel = interaction.client.get_channel(CANAL_NOTIFICACOES)
                if channel:
                    await channel.send(mensagem, view=view)
                    await interaction.response.send_message(
                        "Agendamento registrado com sucesso!",
                        ephemeral=True
                    )
                    logging.info(f"{interaction.user.name} registrou um agendamento para {self.cliente}")
                else:
                    raise Exception("Canal não encontrado")
                
        except Exception as e:
            logging.error(f"Erro ao registrar agendamento: {str(e)}")
            await interaction.response.send_message(
                "Ocorreu um erro ao registrar o agendamento. Tente novamente mais tarde.",
                ephemeral=True
            )

class AtualizacaoModal(discord.ui.Modal, title='Atualização'):
    def __init__(self):
        super().__init__()
        self.message_to_edit = None

    cliente = discord.ui.TextInput(
        label='Cliente',
        placeholder='Nome do cliente...',
        required=True,
    )
    
    versao_neocorp = discord.ui.TextInput(
        label='Versão NeoCorp',
        placeholder='Ex: X.XX.XX',
        required=True,
    )
    
    versao_neoweb = discord.ui.TextInput(
        label='Versão NeoWeb',
        placeholder='Ex: X.XX.XX',
        required=False,
    )
    
    versao_neocontabil = discord.ui.TextInput(
        label='Versão NeoContabil',
        placeholder='Ex: X.XX.XX',
        required=False,
    )
    
    chamados = discord.ui.TextInput(
        label='Chamados',
        placeholder='Liste os chamados separados por vírgula...',
        style=discord.TextStyle.paragraph,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            data_atual = datetime.now().strftime('%d/%m/%Y')
            
            mensagem = (
                "**ATUALIZAÇÃO**\n"
                f"**• Cliente:** {self.cliente}\n"
                f"**• Versão NeoCorp:** {self.versao_neocorp}\n"
                f"**• Versão NeoWeb:** {self.versao_neoweb}\n"
                f"**• Versão NeoContabil:** {self.versao_neocontabil}\n"
                f"**• Data:** {data_atual}\n"
                f"**• Chamados:** {self.chamados}\n"
            )

            # Dados originais para o botão de edição
            original_data = {
                "cliente": str(self.cliente),
                "versao_neocorp": str(self.versao_neocorp),
                "versao_neoweb": str(self.versao_neoweb),
                "versao_neocontabil": str(self.versao_neocontabil),
                "chamados": str(self.chamados),
            }
            
            view = EditButtons("atualizacao", original_data)
            
            if self.message_to_edit:
                # Se estiver editando, atualiza a mensagem existente
                await self.message_to_edit.edit(content=mensagem, view=view)
                await interaction.response.send_message(
                    "Atualização modificada com sucesso!",
                    ephemeral=True
                )
                logging.info(f"{interaction.user.name} modificou uma atualização para {self.cliente}")
            else:
                # Se for nova mensagem, envia para o canal
                channel = interaction.client.get_channel(CANAL_NOTIFICACOES)
                if channel:
                    await channel.send(mensagem, view=view)
                    await interaction.response.send_message(
                        "Atualização registrada com sucesso!",
                        ephemeral=True
                    )
                    logging.info(f"{interaction.user.name} registrou uma atualização para {self.cliente}")
                else:
                    raise Exception("Canal não encontrado")
                
        except Exception as e:
            logging.error(f"Erro ao registrar atualização: {str(e)}")
            await interaction.response.send_message(
                "Ocorreu um erro ao registrar a atualização. Tente novamente mais tarde.",
                ephemeral=True
            )

class ScheduleUpdateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="agendamento",
        description="Registra um novo agendamento"
    )
    async def agendamento(self, interaction: discord.Interaction):
        try:
            await interaction.response.send_modal(AgendamentoModal())
            logging.info(f"{interaction.user.name} abriu o modal de agendamento")
        except Exception as e:
            logging.error(f"Erro ao abrir modal de agendamento: {str(e)}")
            await interaction.response.send_message(
                "Ocorreu um erro ao abrir o formulário. Tente novamente mais tarde.",
                ephemeral=True
            )

    @app_commands.command(
        name="atualizacao",
        description="Registra uma nova atualização"
    )
    async def atualizacao(self, interaction: discord.Interaction):
        try:
            await interaction.response.send_modal(AtualizacaoModal())
            logging.info(f"{interaction.user.name} abriu o modal de atualização")
        except Exception as e:
            logging.error(f"Erro ao abrir modal de atualização: {str(e)}")
            await interaction.response.send_message(
                "Ocorreu um erro ao abrir o formulário. Tente novamente mais tarde.",
                ephemeral=True
            )