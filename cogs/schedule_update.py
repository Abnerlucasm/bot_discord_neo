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
EMOJI_STATUS_AGEND = "<:discotoolsxyzicon1:1331628487202705554>"    
EMOJI_USER_AGEND = "<:agendamento3:1327339980753735702>"       
EMOJI_VERSAO_AGEND = "📦"    


EMOJI_CLIENTE_ATUALIZACAO = "<:atualizacao2:1327339988299415552>"  
EMOJI_VERS_CORP_ATUALIZACAO = "<:atualzicao6:1327341654751051868>"  
EMOJI_VERS_WEB_ATUALIZACAO = "<:atualzicao6:1327341654751051868>"  
EMOJI_VERS_CONT_ATUALIZACAO = "<:atualzicao6:1327341654751051868>"  
EMOJI_DATA_ATUALIZACAO = "<:atualizacao1:1327339986173038602>"  
EMOJI_CHAMADOS_ATUALIZACAO = "<:atualizacao3:1327339990350303243>"  
EMOJI_OBS_ATUALIZACAO = "💬"          
# EMOJI_STATUS_ATUALIZACAO = "<:discotoolsxyzicon:1331628490419736657>"    
EMOJI_USER_ATUALIZACAO = "<:atualizacao2:1327339988299415552>"       
EMOJI_VERSAO_ATUALIZACAO = "<:atualzicao6:1327341654751051868>"  


EMOJI_CLIENTE_99 = "<:discotoolsxyzicon1:1327343125928087622>"
EMOJI_VERSAO_99 = "<:ver99:1327343131166900275>"
EMOJI_DATA_99 = "<:discotoolsxyzicon3:1327343409148592188>"
EMOJI_CHAMADOS_99 = "<:discotoolsxyzicon:1327343129753554944>"
EMOJI_USER_99 = "<:discotoolsxyzicon1:1327343125928087622>"

class StatusButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Pendente",
            style=discord.ButtonStyle.danger,
            emoji="⏳"
        )
        self.status = "Pendente"

    async def callback(self, interaction: discord.Interaction):
        if self.status == "Pendente":
            self.status = "Recebido"
            self.style = discord.ButtonStyle.success
            self.label = "Recebido"
            self.emoji = "✅"
        else:
            self.status = "Pendente"
            self.style = discord.ButtonStyle.danger
            self.label = "Pendente"
            self.emoji = "⏳"

        content_lines = interaction.message.content.split('\n')
        
        # Verifica se já está agendado
        is_agendado = any("Data Confirmada:" in line for line in content_lines)
        status_complement = "Agendado" if is_agendado else (
            "Aguardando Agendamento" if self.status == "Recebido" else "Aguardando Recebimento"
        )
        
        # Adiciona informação de quem recebeu
        recebido_por = f" por <@{interaction.user.id}>" if self.status == "Recebido" else ""
        status_line = f"**{EMOJI_STATUS_AGEND} • Status: **{self.status}{recebido_por} | {status_complement}"
        
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
            modal.cargo.default = self.original_data.get("cargo", "")
        else:
            modal = AtualizacaoModal()
            modal.cliente.default = self.original_data.get("cliente", "")
            modal.versoes.default = self.original_data.get("versoes", "")
            modal.chamados.default = self.original_data.get("chamados", "")
            modal.data_atualizacao.default = self.original_data.get("data_atualizacao", "")

        modal.message_to_edit = interaction.message
        modal.author_id = self.author_id
        await interaction.response.send_modal(modal)

class DeleteButton(discord.ui.Button):
    def __init__(self, author_id: int):
        super().__init__(label="Excluir", style=discord.ButtonStyle.danger, emoji="🗑️")
        self.author_id = author_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Apenas o autor original pode excluir esta mensagem.",
                ephemeral=True
            )
            return
        
        await interaction.message.delete()
        await interaction.response.send_message(
            "Mensagem excluída com sucesso!",
            ephemeral=True
        )

class ConfirmarButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Confirmar Agendamento",
            style=discord.ButtonStyle.primary,
            emoji="📅"
        )
        self.is_confirmed = False

    async def callback(self, interaction: discord.Interaction):
        if not self.is_confirmed:
            modal = ConfirmarAgendamentoModal()
            modal.message = interaction.message  # Passa a mensagem para o modal
            modal.view = self.view  # Passa a view para o modal
            await interaction.response.send_modal(modal)
        else:
            # Cancelar confirmação
            content_lines = interaction.message.content.split('\n')
            new_lines = []
            
            for line in content_lines:
                if "• Data Confirmada:" in line:
                    # Converte data confirmada para prevista
                    data = line.split("Data Confirmada:")[1].strip()
                    new_lines.append(f"**{EMOJI_DATA_AGEND} • Data Prevista:** {data}")
                elif "**• Status:**" in line:
                    # Mantém o status de recebimento mas remove o "Agendado"
                    if "Recebido" in line:
                        new_lines.append(f"**{EMOJI_STATUS_AGEND} • Status:** Recebido por <@{interaction.user.id}> | Aguardando Agendamento")
                    else:
                        new_lines.append(f"**{EMOJI_STATUS_AGEND} • Status:** Pendente | Aguardando Recebimento")
                elif "🎯 **AGENDAMENTO CONFIRMADO**" in line:
                    continue  # Remove a linha de destaque
                else:
                    new_lines.append(line)

            self.is_confirmed = False
            self.label = "Confirmar Agendamento"
            self.style = discord.ButtonStyle.primary
            
            await interaction.message.edit(content='\n'.join(new_lines), view=self.view)
            await interaction.response.send_message("Confirmação de agendamento cancelada!", ephemeral=True)

class ConfirmarAgendamentoModal(discord.ui.Modal, title='Confirmar Agendamento'):
    def __init__(self):
        super().__init__()
        self.message = None
        self.view = None
        
    data_hora = discord.ui.TextInput(
        label='Data e Hora do Agendamento',
        placeholder='DD/MM/YYYY HH:MM',
        default=(datetime.now().replace(hour=12, minute=0)).strftime('%d/%m/%Y %H:%M'),
        required=True,
    )

    observacao = discord.ui.TextInput(
        label='Observação',
        placeholder='Observação opcional sobre a confirmação...',
        style=discord.TextStyle.paragraph,
        required=False,
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            datetime.strptime(self.data_hora.value.strip(), '%d/%m/%Y %H:%M')
            
            content_lines = self.message.content.split('\n')
            new_lines = []
            
            # Adiciona destaque do agendamento confirmado
            new_lines.append("**AGENDAMENTO**")
            new_lines.append("🎯 **AGENDAMENTO CONFIRMADO** 🎯")
            
            data_line = f"**{EMOJI_DATA_AGEND} • Data Confirmada:** {self.data_hora.value}"
            data_found = False
            recebido_por = None
            obs_found = False
            
            for line in content_lines[1:]:  # Pula o título
                if "• Data Prevista:" in line or "• Data Confirmada:" in line:
                    new_lines.append(data_line)
                    data_found = True
                elif "**• Status:**" in line:
                    if "Recebido por" in line:
                        recebido_por = line.split("Recebido por")[1].split("|")[0].strip()
                    
                    if recebido_por:
                        new_lines.append(f"**{EMOJI_STATUS_AGEND} • Status:** Recebido por {recebido_por} | Agendado")
                    else:
                        new_lines.append(f"**{EMOJI_STATUS_AGEND} • Status:** Recebido por <@{interaction.user.id}> | Agendado")
                elif "• Observação:" in line:
                    if self.observacao.value and self.observacao.value.strip():
                        new_lines.append(f"**{EMOJI_OBS_AGEND} • Observação:** {line.split('Observação:')[1].strip()}\n**{EMOJI_OBS_AGEND} • Observação da Confirmação:** {self.observacao.value}")
                    else:
                        new_lines.append(line)
                    obs_found = True
                else:
                    new_lines.append(line)
            
            if not data_found:
                new_lines.insert(-1, data_line)

            # Adiciona observação da confirmação se não existir observação anterior
            if not obs_found and self.observacao.value and self.observacao.value.strip():
                new_lines.insert(-1, f"**{EMOJI_OBS_AGEND} • Observação da Confirmação:** Confirmado por {self.observacao.value}")

            # Atualiza o botão
            for item in self.view.children:
                if isinstance(item, ConfirmarButton):
                    item.is_confirmed = True
                    item.label = "Cancelar Confirmação"
                    item.style = discord.ButtonStyle.danger

            await self.message.edit(content='\n'.join(new_lines), view=self.view)
            await interaction.response.send_message("Agendamento confirmado com sucesso!", ephemeral=True)
            
        except ValueError:
            await interaction.response.send_message(
                "Formato de data inválido. Use DD/MM/YYYY HH:MM",
                ephemeral=True
            )
        except Exception as e:
            logging.error(f"Erro ao confirmar agendamento: {str(e)}")
            await interaction.response.send_message(
                "Ocorreu um erro ao confirmar o agendamento. Tente novamente mais tarde.",
                ephemeral=True
            )

class CustomView(discord.ui.View):
    def __init__(self, modal_type: str, original_data: dict, author_id: int):
        super().__init__(timeout=None)
        if modal_type == "agendamento":
            self.add_item(StatusButton())
            self.add_item(ConfirmarButton())  # Adicionar o novo botão
        self.add_item(EditButton(modal_type, original_data, author_id))
        self.add_item(DeleteButton(author_id))
        

class Beta99Modal(discord.ui.Modal, title='Versão Beta 99'):
    def __init__(self):
        super().__init__()
        self.message_to_edit = None

    cliente = discord.ui.TextInput(
        label='Cliente',
        placeholder='Nome do cliente...',
        required=True,
    )
    
    versao = discord.ui.TextInput(
        label='Versão',
        placeholder='Ex: X.X.X.99XX',
        required=True,
    )

    data = discord.ui.TextInput(
        label='Data',
        placeholder='DD/MM/YYYY',
        required=True,
    )
    
    chamados = discord.ui.TextInput(
        label='Chamados',
        placeholder='Liste os chamados separados por vírgula...',
        style=discord.TextStyle.paragraph,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            mensagem = [
                "**VERSÃO BETA 99**",
                f"**{EMOJI_CLIENTE_99} • Cliente:** {self.cliente}",
                f"**{EMOJI_VERSAO_99} • Versão:** {self.versao}",
                f"**{EMOJI_DATA_99} • Data:** {self.data}",
                f"**{EMOJI_CHAMADOS_99} • Chamados:** {self.chamados}",
                f"**{EMOJI_USER_99} • Lançado por:** <@{interaction.user.id}>"
            ]

            mensagem_final = '\n'.join(mensagem)
            
            channel = interaction.client.get_channel(CANAL_NOTIFICACOES)
            if channel:
                await channel.send(content=mensagem_final)
                await interaction.response.send_message(
                    "Versão beta registrada com sucesso!",
                    ephemeral=True
                )
            else:
                raise Exception("Canal não encontrado")

        except Exception as e:
            logging.error(f"Erro ao registrar versão beta: {str(e)}")
            await interaction.response.send_message(
                "Ocorreu um erro ao registrar a versão beta. Tente novamente mais tarde.",
                ephemeral=True
            )

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
        label='Data Prevista',
        placeholder='DD/MM/YYYY HH:MM',
        default=(datetime.now().replace(hour=12, minute=0)).strftime('%d/%m/%Y %H:%M'),
        required=False,
    )
    
    observacao = discord.ui.TextInput(
        label='Observação',
        placeholder='Observações adicionais...',
        style=discord.TextStyle.paragraph,
        required=False,
    )
    
    cargo = discord.ui.TextInput(
        label='Cargo para Notificar',
        placeholder='Digite @ ou ID do cargo (opcional)',
        default='@Suporte',
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
            ]

            # Adiciona menção do cargo se foi fornecido
            if self.cargo.value and self.cargo.value.strip():
                # Tenta encontrar o cargo pelo ID ou nome
                cargo_valor = self.cargo.value.strip()
                if cargo_valor.isdigit():
                    cargo = interaction.guild.get_role(int(cargo_valor))
                else:
                    # Remove @ e espaços se houver
                    cargo_nome = cargo_valor.replace('@', '').strip()
                    cargo = discord.utils.get(interaction.guild.roles, name=cargo_nome)
                
                if cargo:
                    mensagem.append(f"{cargo.mention}")
                
            mensagem.extend([
                f"**{EMOJI_CLIENTE_AGEND} • Cliente:** {self.cliente.value}",
            ])

            if self.chamado.value and self.chamado.value.strip():
                mensagem.append(f"**{EMOJI_CHAMADO_AGEND} • Chamado:** {self.chamado.value}")

            if self.data_agendamento.value and self.data_agendamento.value.strip():
                mensagem.append(f"**{EMOJI_DATA_AGEND} • Data Prevista:** {self.data_agendamento.value}")
            
            if self.observacao.value and self.observacao.value.strip():
                mensagem.append(f"**{EMOJI_OBS_AGEND} • Observação:** {self.observacao.value}")

            mensagem.append(f"**{EMOJI_STATUS_AGEND} • Status: **Pendente | Aguardando Recebimento")
            mensagem.append(f"**{EMOJI_USER_AGEND} • Solicitado por: **<@{author_id}>")

            mensagem_final = '\n'.join(mensagem)

            original_data = {
                "cliente": self.cliente.value,
                "chamado": self.chamado.value,
                "data_agendamento": self.data_agendamento.value,
                "observacao": self.observacao.value,
                "cargo": self.cargo.value,  # Adiciona cargo aos dados originais
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

    versoes = discord.ui.TextInput(
        label='Versões',
        placeholder='Preencha as versões após cada título',
        default='NeoCorp: \nNeoWeb: \nNeoContábil: ',
        required=True,
        style=discord.TextStyle.paragraph,
    )

    chamados = discord.ui.TextInput(
        label='Chamados',
        placeholder='Números dos chamados...',
        required=False,
        style=discord.TextStyle.paragraph,
    )

    data_atualizacao = discord.ui.TextInput(
        label='Data',
        placeholder='DD/MM/YYYY',
        default=datetime.now().strftime('%d/%m/%Y'),
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Verifica se a data é válida, se fornecida
            data_valida = True
            if self.data_atualizacao.value and self.data_atualizacao.value.strip():
                try:
                    datetime.strptime(self.data_atualizacao.value.strip(), '%d/%m/%Y')
                except ValueError:
                    data_valida = False
                    await interaction.response.send_message(
                        "Formato de data inválido. Use DD/MM/YYYY",
                        ephemeral=True
                    )
                    return

            if not data_valida:
                return

            # Processa o campo de versões (atualizado para lidar com quebras de linha)
            versoes_texto = self.versoes.value.strip()
            versao_neocorp = ""
            versao_neoweb = ""
            versao_neocontabil = ""

            # Tenta extrair as versões do texto (agora suporta tanto | quanto quebras de linha)
            for linha in versoes_texto.replace('|', '\n').split('\n'):
                linha = linha.strip()
                if "NeoCorp:" in linha:
                    versao_neocorp = linha.split("NeoCorp:")[1].strip()
                elif "NeoWeb:" in linha:
                    versao_neoweb = linha.split("NeoWeb:")[1].strip()
                elif "NeoContábil:" in linha:
                    versao_neocontabil = linha.split("NeoContábil:")[1].strip()

            # Usa a data fornecida ou a data atual
            data = self.data_atualizacao.value.strip() if self.data_atualizacao.value and self.data_atualizacao.value.strip() else datetime.now().strftime('%d/%m/%Y')

            mensagem = [
                "**ATUALIZAÇÃO**",
                f"**{EMOJI_CLIENTE_ATUALIZACAO} • Cliente:** {self.cliente.value}",
                f"**{EMOJI_VERS_CORP_ATUALIZACAO} • Versão NeoCorp:** {versao_neocorp}",
            ]

            if versao_neoweb:
                mensagem.append(f"**{EMOJI_VERS_WEB_ATUALIZACAO} • Versão NeoWeb:** {versao_neoweb}")
            if versao_neocontabil:
                mensagem.append(f"**{EMOJI_VERS_CONT_ATUALIZACAO} • Versão NeoContábil:** {versao_neocontabil}")
            if self.chamados.value and self.chamados.value.strip():
                mensagem.append(f"**{EMOJI_CHAMADOS_ATUALIZACAO} • Chamados:** {self.chamados.value}")

            mensagem.append(f"**{EMOJI_DATA_ATUALIZACAO} • Data:** {data}")
            mensagem.append(f"**{EMOJI_USER_ATUALIZACAO} • Atualizado por:** <@{interaction.user.id}>")

            mensagem_final = '\n'.join(mensagem)

            original_data = {
                "cliente": self.cliente.value,
                "versoes": self.versoes.value,
                "chamados": self.chamados.value,
                "data_atualizacao": data,
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
    name="beta99",
    description="Registra uma nova versão beta 99"
)
    async def beta99(self, interaction: discord.Interaction):
        try:
            await interaction.response.send_modal(Beta99Modal())
            logging.info(f"{interaction.user.name} abriu o modal de versão beta")
        except Exception as e:
            logging.error(f"Erro ao abrir modal de versão beta: {str(e)}")
            await interaction.response.send_message(
                "Ocorreu um erro ao abrir o formulário. Tente novamente mais tarde.",
                ephemeral=True
            )

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