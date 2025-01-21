from discord.ext import commands
from discord import app_commands
import discord
from datetime import datetime
import logging

CANAL_NOTIFICACOES = 997291234643148811

# Constantes para os emojis do servidor
EMOJI_CLIENTE_AGEND = "<:agendamento3:1327339980753735702>"  
EMOJI_CHAMADO_AGEND = "<:agendamento5:1327339984583397503>"  
EMOJI_DATA_AGEND = "<:agendamento2:1327339979420209273>"  
EMOJI_OBS_AGEND = "<:agendamento4:1327339982767263836>"          
EMOJI_STATUS_AGEND = ""    
EMOJI_USER_AGEND = "<:agendamento3:1327339980753735702>"       
EMOJI_VERSAO_AGEND = "📦"    

EMOJI_CLIENTE_ATUALIZACAO = "<:atualizacao2:1327339988299415552>"  
EMOJI_VERS_CORP_ATUALIZACAO = "<:atualzicao6:1327341654751051868>"  
EMOJI_VERS_WEB_ATUALIZACAO = "<:atualzicao6:1327341654751051868>"  
EMOJI_VERS_CONT_ATUALIZACAO = "<:atualzicao6:1327341654751051868>"  
EMOJI_DATA_ATUALIZACAO = "<:atualizacao1:1327339986173038602>"  
EMOJI_CHAMADOS_ATUALIZACAO = "<:atualizacao3:1327339990350303243>"  
EMOJI_OBS_ATUALIZACAO = "💬"          
EMOJI_STATUS_ATUALIZACAO = ""    
EMOJI_USER_ATUALIZACAO = "<:atualizacao2:1327339988299415552>"       
EMOJI_VERSAO_ATUALIZACAO = "<:atualzicao6:1327341654751051868>"  


class StatusButton(discord.ui.Button):
    def __init__(self, author_id: int):
        super().__init__(
            label="Status: Pendente",
            style=discord.ButtonStyle.danger,
            emoji="⏳"
        )
        self.status = "Pendente"
        self.author_id = author_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Apenas o autor original pode alterar o status.",
                ephemeral=True
            )
            return

        if self.status == "Pendente":
            self.status = "Recebido"
            self.style = discord.ButtonStyle.success
            self.label = "Status: Recebido"
            self.emoji = "✅"
        else:
            self.status = "Pendente"
            self.style = discord.ButtonStyle.danger
            self.label = "Status: Pendente"
            self.emoji = "⏳"

        content_lines = interaction.message.content.split('\n')
        status_line = f"**{EMOJI_STATUS_AGEND} • Status:** {self.status}"
        status_found = False
        
        for i, line in enumerate(content_lines):
            if "**• Status:**" in line:
                content_lines[i] = status_line
                status_found = True
                break
                
        if not status_found:
            content_lines.insert(-1, status_line)

        await interaction.message.edit(content='\n'.join(content_lines), view=self.view)
        await interaction.response.defer()

class EditButton(discord.ui.Button):
    def __init__(self, modal_type: str, original_data: dict, author_id: int):
        super().__init__(label="Editar", style=discord.ButtonStyle.primary, emoji="✏️")
        self.modal_type = modal_type
        self.original_data = original_data
        self.author_id = author_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Apenas o autor original pode editar esta mensagem.",
                ephemeral=True
            )
            return

        if self.modal_type == "agendamento":
            modal = AgendamentoModal()
            modal.cliente.default = self.original_data.get("cliente", "")
            modal.chamado.default = self.original_data.get("chamado", "")
            modal.data_agendamento.default = self.original_data.get("data_agendamento", "")
            modal.observacao.default = self.original_data.get("observacao", "")
        else:
            modal = AtualizacaoModal()
            modal.cliente.default = self.original_data.get("cliente", "")
            modal.versao_neocorp.default = self.original_data.get("versao_neocorp", "")
            modal.versao_neoweb.default = self.original_data.get("versao_neoweb", "")
            modal.versao_neocontabil.default = self.original_data.get("versao_neocontabil", "")
            modal.chamados.default = self.original_data.get("chamados", "")

        modal.message_to_edit = interaction.message
        modal.author_id = self.author_id
        await interaction.response.send_modal(modal)

class CustomView(discord.ui.View):
    def __init__(self, modal_type: str, original_data: dict, author_id: int):
        super().__init__(timeout=None)
        self.add_item(StatusButton(author_id))
        self.add_item(EditButton(modal_type, original_data, author_id))

class AgendamentoModal(discord.ui.Modal, title='Agendamento'):
    def __init__(self):
        super().__init__()
        self.message_to_edit = None
        self.author_id = None

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
        required=False,
    )
    
    observacao = discord.ui.TextInput(
        label='Observação',
        placeholder='Observações adicionais...',
        style=discord.TextStyle.paragraph,
        required=False,
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            data_valida = True
            if self.data_agendamento.value and self.data_agendamento.value.strip():
                try:
                    datetime.strptime(self.data_agendamento.value.strip(), '%d/%m/%Y %H:%M')
                except ValueError:
                    data_valida = False
                    await interaction.response.send_message(
                        "Formato de data inválido. Use DD/MM/YYYY HH:MM",
                        ephemeral=True
                    )
                    return

            if not data_valida:
                return

            author_id = self.author_id if self.author_id else interaction.user.id
            
            # Formatação da mensagem usando as constantes de emoji
            mensagem = [
                "**AGENDAMENTO**",
                f"**{EMOJI_CLIENTE_AGEND} • Cliente:** {self.cliente.value}",
            ]

            if self.chamado.value and self.chamado.value.strip():
                mensagem.append(f"**{EMOJI_CHAMADO_AGEND} • Chamado:** {self.chamado.value}")

            if self.data_agendamento.value and self.data_agendamento.value.strip():
                mensagem.append(f"**{EMOJI_DATA_AGEND} • Data Agendamento:** {self.data_agendamento.value}")
            
            if self.observacao.value and self.observacao.value.strip():
                mensagem.append(f"**{EMOJI_OBS_AGEND} • Observação:** {self.observacao.value}")

            mensagem.append(f"**{EMOJI_STATUS_AGEND} • Status:** Pendente")
            mensagem.append(f"**{EMOJI_USER_AGEND} • Solicitado por:** <@{author_id}>")

            mensagem_final = '\n'.join(mensagem)

            original_data = {
                "cliente": self.cliente.value,
                "chamado": self.chamado.value,
                "data_agendamento": self.data_agendamento.value,
                "observacao": self.observacao.value,
            }
            
            view = CustomView("agendamento", original_data, author_id)
            
            if self.message_to_edit:
                await self.message_to_edit.edit(content=mensagem_final, view=view)
                await interaction.response.send_message(
                    "Agendamento atualizado com sucesso!",
                    ephemeral=True
                )
                logging.info(f"{interaction.user.name} atualizou um agendamento para {self.cliente.value}")
            else:
                channel = interaction.client.get_channel(CANAL_NOTIFICACOES)
                if channel:
                    await channel.send(content=mensagem_final, view=view)
                    await interaction.response.send_message(
                        "Agendamento registrado com sucesso!",
                        ephemeral=True
                    )
                    logging.info(f"{interaction.user.name} registrou um agendamento para {self.cliente.value}")
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
        self.author_id = None

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

            mensagem = [
                "**ATUALIZAÇÃO**",
                f"**{EMOJI_CLIENTE_ATUALIZACAO} • Cliente:** {self.cliente}",
                f"**{EMOJI_VERS_CORP_ATUALIZACAO} • Versão NeoCorp:** {self.versao_neocorp}"
            ]

            if self.versao_neoweb.value and self.versao_neoweb.value.strip():
                mensagem.append(f"**{EMOJI_VERS_WEB_ATUALIZACAO} •Versão NeoWeb:** {self.versao_neoweb}")

            if self.versao_neocontabil.value and self.versao_neocontabil.value.strip():
                mensagem.append(f"**{EMOJI_VERS_CONT_ATUALIZACAO} • Versão NeoContabil:** {self.versao_neocontabil}")

            mensagem.append(f"**{EMOJI_DATA_ATUALIZACAO} • Data:** {data_atual}")
            mensagem.append(f"**{EMOJI_CHAMADOS_ATUALIZACAO} • Chamados:** {self.chamados}")
            mensagem.append(f"**{EMOJI_STATUS_ATUALIZACAO} • Status:** Pendente")
            mensagem.append(f"**{EMOJI_USER_ATUALIZACAO} • Lançado por:** <@{interaction.user.id}>")

            mensagem_final = '\n'.join(mensagem)

            original_data = {
                "cliente": str(self.cliente),
                "versao_neocorp": str(self.versao_neocorp),
                "versao_neoweb": str(self.versao_neoweb),
                "versao_neocontabil": str(self.versao_neocontabil),
                "chamados": str(self.chamados),
            }

            view = CustomView("atualizacao", original_data, interaction.user.id)

            if self.message_to_edit:
                await self.message_to_edit.edit(content=mensagem_final, view=view)
                await interaction.response.send_message(
                    "Atualização modificada com sucesso!",
                    ephemeral=True
                )
                logging.info(f"{interaction.user.name} modificou uma atualização para {self.cliente}")
            else:
                channel = interaction.client.get_channel(CANAL_NOTIFICACOES)
                if channel:
                    await channel.send(content=mensagem_final, view=view)
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
        except discord.NotFound:
            try:
                await interaction.followup.send(
                    "Por favor, tente novamente.",
                    ephemeral=True
                )
            except:
                pass
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
        except discord.NotFound:
            try:
                await interaction.followup.send(
                    "Por favor, tente novamente.",
                    ephemeral=True
                )
            except:
                pass
        except Exception as e:
            logging.error(f"Erro ao abrir modal de atualização: {str(e)}")
            await interaction.response.send_message(
                "Ocorreu um erro ao abrir o formulário. Tente novamente mais tarde.",
                ephemeral=True
            )