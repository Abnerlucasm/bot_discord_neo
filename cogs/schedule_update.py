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
            label="⚠️ Aguardando Recebimento",
            style=discord.ButtonStyle.danger,
            emoji="📋"
        )
        self.status = "Pendente"

    async def callback(self, interaction: discord.Interaction):
        if self.status == "Pendente":
            self.status = "Recebido"
            self.style = discord.ButtonStyle.success
            self.label = "✅ Solicitação Recebida"
            self.emoji = "📋"
        else:
            self.status = "Pendente"
            self.style = discord.ButtonStyle.danger
            self.label = "⚠️ Aguardando Recebimento"
            self.emoji = "📋"

        content_lines = interaction.message.content.split('\n')
        new_lines = []
        
        # Verifica se já está agendado
        is_agendado = any("Data Confirmada:" in line for line in content_lines)
        status_complement = "Agendado" if is_agendado else (
            "Aguardando Agendamento" if self.status == "Recebido" else "Aguardando Recebimento"
        )
        
        # Adiciona informação de quem recebeu
        recebido_por = f"<@{interaction.user.id}>" if self.status == "Recebido" else ""
        confirmado_por = None
        
        # Processa as linhas de conteúdo
        instrucoes_encontradas = False
        usuario_solicitante = None
        
        for line in content_lines:
            # Ignora linhas de instruções e histórico anteriores, serão recriadas
            if line.startswith("**INSTRUÇÕES PARA OS RESPONSÁVEIS") or \
               line.startswith("**Histórico de Ações") or \
               line.startswith("1️⃣") or line.startswith("2️⃣") or \
               line.startswith("✅ **Status Atual") or \
               line.startswith("📋 Solicitação recebida") or \
               line.startswith("🗓️ Data confirmada") or \
               line == "":
                instrucoes_encontradas = True
                continue
                
            # Captura informação de quem foi o solicitante
            if "Solicitado por:" in line:
                usuario_solicitante = line.split("Solicitado por:")[1].strip()
                new_lines.append(line)
                continue
                
            # Captura informação de quem confirmou a data, se existir
            if "Data Confirmada:" in line:
                if "por" in line:
                    confirmado_por = line.split("por")[1].strip()
                
            # Outras linhas são mantidas normalmente
            if "**• Status:**" in line:
                status_line = f"**{EMOJI_STATUS_AGEND} • Status: **{self.status}{' por ' + recebido_por if recebido_por else ''} | {status_complement}"
                new_lines.append(status_line)
            else:
                new_lines.append(line)
        
        # Adiciona instruções e histórico após todas as outras informações
        if self.status == "Recebido":
            # Adiciona quebra de linha antes das instruções
            new_lines.append("")
            new_lines.append("**INSTRUÇÕES PARA OS RESPONSÁVEIS:**")
            if is_agendado:
                new_lines.append("✅ **Status Atual**: Agendamento confirmado")
            else:
                new_lines.append("✅ **Status Atual**: Solicitação recebida, aguardando confirmação da data")
                new_lines.append("2️⃣ Clique em \"🗓️ Confirmar Data do Agendamento\" para definir a data confirmada")
                
            # Adiciona o histórico de ações
            new_lines.append("")
            new_lines.append("**Histórico de Ações:**")
            new_lines.append(f"📋 Solicitação recebida por {recebido_por}")
            if confirmado_por:
                new_lines.append(f"🗓️ Data confirmada por {confirmado_por}")
        else:
            # Se o status voltou para Pendente, restaura as instruções originais
            new_lines.append("")
            new_lines.append("**INSTRUÇÕES PARA OS RESPONSÁVEIS:**")
            new_lines.append("1️⃣ Clique em \"📋 Aguardando Recebimento\" para indicar que você recebeu a solicitação")
            new_lines.append("2️⃣ Clique em \"🗓️ Confirmar Data do Agendamento\" para definir a data confirmada")

        await interaction.message.edit(content='\n'.join(new_lines), view=self.view)
        await interaction.response.send_message(f"Você alterou o status para: **{self.status}**", ephemeral=True)

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
            label="📅 Confirmar Data do Agendamento",
            style=discord.ButtonStyle.primary,
            emoji="🗓️"
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
            self.label = "📅 Confirmar Data do Agendamento"
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
            
            data_line = f"**{EMOJI_DATA_AGEND} • Data Confirmada:** {self.data_hora.value} por <@{interaction.user.id}>"
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
                elif line.startswith("**INSTRUÇÕES PARA OS RESPONSÁVEIS"):
                    # Pula as linhas de instruções, serão adicionadas depois
                    pass
                elif line.startswith("1️⃣") or line.startswith("2️⃣"):
                    # Pula as linhas de instruções, serão adicionadas depois
                    pass
                else:
                    new_lines.append(line)
            
            if not data_found:
                new_lines.insert(-1, data_line)

            # Adiciona observação da confirmação se não existir observação anterior
            if not obs_found and self.observacao.value and self.observacao.value.strip():
                new_lines.insert(-1, f"**{EMOJI_OBS_AGEND} • Observação da Confirmação:** {self.observacao.value}")

            # Adiciona instruções atualizadas com espaçamento melhorado
            new_lines.append("\n**INSTRUÇÕES PARA OS RESPONSÁVEIS:**")
            new_lines.append("✅ **Status Atual**: Agendamento confirmado")
            new_lines.append("\n**Histórico de Ações:**")
            if recebido_por:
                new_lines.append(f"📋 Solicitação recebida por {recebido_por}")
            else:
                new_lines.append(f"📋 Solicitação recebida por <@{interaction.user.id}>")
            new_lines.append(f"🗓️ Data confirmada por <@{interaction.user.id}>")

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
        self.author_id = author_id
        
        # Botões que todos podem ver
        if modal_type == "agendamento":
            self.add_item(StatusButton())
            self.add_item(ConfirmarButton())
            
        # Botões que só o autor pode ver - eles serão filtrados no método interaction_check
        self.edit_button = EditButton(modal_type, original_data, author_id)
        self.delete_button = DeleteButton(author_id)
        self.add_item(self.edit_button)
        self.add_item(self.delete_button)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Se for o botão de editar ou excluir e não for o autor, esconde o botão
        component_id = interaction.data.get('custom_id', '')
        
        # Botões são referencidados por índice no children
        edit_custom_id = self.edit_button.custom_id
        delete_custom_id = self.delete_button.custom_id
        
        # Se o componente interagido é um dos botões restritos e o usuário não é o autor
        if (component_id in [edit_custom_id, delete_custom_id] and 
            interaction.user.id != self.author_id):
            await interaction.response.send_message(
                "Apenas o autor original pode usar este botão.",
                ephemeral=True
            )
            return False
        
        return True

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
        self.selected_role = None

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

    async def on_submit(self, interaction: discord.Interaction):
        # Armazena os dados do modal para uso posterior
        self.interaction = interaction
        self.author_id = interaction.user.id
        
        # Verifica se a data é válida
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
            
        # Após validar o modal, mostra o seletor de cargo
        view = RoleSelectorView(self)
        await interaction.response.send_message(
            "**2ª Etapa: Selecione o cargo para notificar**\n\n"
            "Escolha qual cargo deve ser notificado sobre este agendamento:",
            view=view,
            ephemeral=True
        )
        logging.info(f"{interaction.user.name} preencheu o modal de agendamento e está selecionando o cargo")

class RoleSelect(discord.ui.RoleSelect):
    def __init__(self, modal: AgendamentoModal):
        super().__init__(
            placeholder="Selecione o cargo para notificar...",
            min_values=0,
            max_values=1
        )
        self.modal = modal

    async def callback(self, interaction: discord.Interaction):
        # Armazena o cargo selecionado no modal
        self.modal.selected_role = self.values[0] if self.values else None
        
        # Atualiza a mensagem com o cargo selecionado
        role_text = self.values[0].mention if self.values else "Nenhum cargo selecionado"
        await interaction.response.edit_message(
            content=f"**2ª Etapa: Selecione o cargo para notificar**\n\n"
                   f"Cargo selecionado: {role_text}\n\n"
                   f"Clique em 'Confirmar' para finalizar o agendamento.",
            view=self.view
        )

class ConfirmarAgendamentoButton(discord.ui.Button):
    def __init__(self, modal: AgendamentoModal):
        super().__init__(
            label="Confirmar",
            style=discord.ButtonStyle.green,
            emoji="✅"
        )
        self.modal = modal

    async def callback(self, interaction: discord.Interaction):
        # Obtém os dados do modal
        author_id = self.modal.author_id if self.modal.author_id else interaction.user.id
        
        # Formatação da mensagem
        mensagem = [
            "**AGENDAMENTO**",
        ]

        # Adiciona menção do cargo se foi selecionado
        if self.modal.selected_role:
            mensagem.append(f"{self.modal.selected_role.mention}")
        
        mensagem.extend([
            f"**{EMOJI_CLIENTE_AGEND} • Cliente:** {self.modal.cliente.value}",
        ])

        if self.modal.chamado.value and self.modal.chamado.value.strip():
            mensagem.append(f"**{EMOJI_CHAMADO_AGEND} • Chamado:** {self.modal.chamado.value}")

        if self.modal.data_agendamento.value and self.modal.data_agendamento.value.strip():
            mensagem.append(f"**{EMOJI_DATA_AGEND} • Data Prevista:** {self.modal.data_agendamento.value}")
        
        if self.modal.observacao.value and self.modal.observacao.value.strip():
            mensagem.append(f"**{EMOJI_OBS_AGEND} • Observação:** {self.modal.observacao.value}")

        mensagem.append(f"**{EMOJI_STATUS_AGEND} • Status: **Pendente | Aguardando Recebimento")
        mensagem.append(f"**{EMOJI_USER_AGEND} • Solicitado por: **<@{author_id}>")
        
        # Adiciona instruções claras para os responsáveis com espaçamento melhorado
        mensagem.append("\n**INSTRUÇÕES PARA OS RESPONSÁVEIS:**")
        mensagem.append("1️⃣ Clique em \"📋 Aguardando Recebimento\" para indicar que você recebeu a solicitação")
        mensagem.append("2️⃣ Clique em \"🗓️ Confirmar Data do Agendamento\" para definir a data confirmada")

        mensagem_final = '\n'.join(mensagem)

        original_data = {
            "cliente": self.modal.cliente.value,
            "chamado": self.modal.chamado.value,
            "data_agendamento": self.modal.data_agendamento.value,
            "observacao": self.modal.observacao.value,
        }
        
        view = CustomView("agendamento", original_data, author_id)
        
        if self.modal.message_to_edit:
            await self.modal.message_to_edit.edit(content=mensagem_final, view=view)
            await interaction.response.send_message(
                "Agendamento atualizado com sucesso!",
                ephemeral=True
            )
            logging.info(f"{interaction.user.name} atualizou um agendamento para {self.modal.cliente.value}")
        else:
            channel = interaction.client.get_channel(CANAL_NOTIFICACOES)
            if channel:
                await channel.send(content=mensagem_final, view=view)
                await interaction.response.send_message(
                    "Agendamento registrado com sucesso!",
                    ephemeral=True
                )
                logging.info(f"{interaction.user.name} registrou um agendamento para {self.modal.cliente.value}")
            else:
                raise Exception("Canal não encontrado")

class PularButton(discord.ui.Button):
    def __init__(self, modal: AgendamentoModal):
        super().__init__(
            label="Pular (Sem notificação)",
            style=discord.ButtonStyle.secondary,
            emoji="⏭️"
        )
        self.modal = modal

    async def callback(self, interaction: discord.Interaction):
        # Define que não há cargo para notificar
        self.modal.selected_role = None
        # Chama a mesma lógica do botão Confirmar
        confirmar = ConfirmarAgendamentoButton(self.modal)
        await confirmar.callback(interaction)

class RoleSelectorView(discord.ui.View):
    def __init__(self, modal: AgendamentoModal):
        super().__init__(timeout=None)
        self.modal = modal
        self.add_item(RoleSelect(modal))
        self.add_item(ConfirmarAgendamentoButton(modal))
        self.add_item(PularButton(modal))

class AtualizacaoModal(discord.ui.Modal, title='Atualização'):
    def __init__(self):
        super().__init__()
        self.message_to_edit = None
        self.author_id = None
        self.selected_users = []  # Lista para armazenar os usuários selecionados

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

            # Processa os responsáveis
            responsaveis_texto = f"<@{interaction.user.id}>"  # Sempre inclui o usuário atual
            
            # Adiciona os usuários selecionados
            for user in self.selected_users:
                if user.id != interaction.user.id:  # Evita duplicar o usuário atual
                    responsaveis_texto += f", <@{user.id}>"

            mensagem.append(f"**{EMOJI_USER_ATUALIZACAO} • Atualizado por:** {responsaveis_texto}")

            mensagem_final = '\n'.join(mensagem)

            original_data = {
                "cliente": self.cliente.value,
                "versoes": self.versoes.value,
                "chamados": self.chamados.value,
                "data_atualizacao": data,
                "responsaveis": [user.id for user in self.selected_users],
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

# Definindo os componentes para o comando /atualizacao
class ConfirmButton(discord.ui.Button):
    def __init__(self, modal: AtualizacaoModal):
        super().__init__(
            label="Continuar",
            style=discord.ButtonStyle.green,
            emoji="➡️"
        )
        self.modal = modal

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.modal)

class ResponsaveisSelect(discord.ui.UserSelect):
    def __init__(self, modal: AtualizacaoModal, current_user: discord.User):
        super().__init__(
            placeholder="Selecione os responsáveis adicionais...",
            min_values=0,
            max_values=25
        )
        self.modal = modal
        self.current_user = current_user

    async def callback(self, interaction: discord.Interaction):
        # Filtra o usuário atual da lista de selecionados
        selected_users = [user for user in self.values if user.id != self.current_user.id]
        self.modal.selected_users = selected_users
        
        # Atualiza a mensagem com os usuários selecionados
        selected_users_text = "\n".join([f"- {user.mention}" for user in selected_users]) if selected_users else "Nenhum responsável adicional selecionado"
        await interaction.response.edit_message(
            content=f"**1ª Etapa: Selecione os responsáveis adicionais:**\n\n"
                   f"**⚠️ IMPORTANTE ⚠️**\n"
                   f"**Você já está listado como responsável principal desta atualização!**\n\n"
                   f"Responsáveis adicionais selecionados:\n{selected_users_text}\n\n"
                   f"Clique no botão 'Continuar' quando terminar a seleção.",
            view=self.view
        )

class AtualizacaoView(discord.ui.View):
    def __init__(self, modal: AtualizacaoModal, current_user: discord.User):
        super().__init__(timeout=None)
        self.modal = modal
        self.add_item(ResponsaveisSelect(modal, current_user))
        self.add_item(ConfirmButton(modal))

class NaoButton(discord.ui.Button):
    def __init__(self, modal: AtualizacaoModal):
        super().__init__(
            label="Não",
            style=discord.ButtonStyle.red,
            emoji="❌"
        )
        self.modal = modal

    async def callback(self, interaction: discord.Interaction):
        # Define apenas o usuário atual como responsável
        self.modal.selected_users = [interaction.user]
        await interaction.response.send_modal(self.modal)

class SimButton(discord.ui.Button):
    def __init__(self, modal: AtualizacaoModal, current_user: discord.User):
        super().__init__(
            label="Sim",
            style=discord.ButtonStyle.green,
            emoji="✅"
        )
        self.modal = modal
        self.current_user = current_user

    async def callback(self, interaction: discord.Interaction):
        view = AtualizacaoView(self.modal, self.current_user)
        await interaction.response.edit_message(
            content="**1ª Etapa: Selecione os responsáveis adicionais:**\n\n"
                   "**⚠️ IMPORTANTE ⚠️**\n"
                   "**Você já está listado como responsável principal desta atualização!**\n\n"
                   "Use o menu abaixo para selecionar **outros responsáveis** pela atualização.\n"
                   "Após selecionar, clique no botão 'Continuar' para abrir o formulário de atualização.",
            view=view
        )

class InicialView(discord.ui.View):
    def __init__(self, modal: AtualizacaoModal, current_user: discord.User):
        super().__init__(timeout=None)
        self.modal = modal
        self.add_item(SimButton(modal, current_user))
        self.add_item(NaoButton(modal))

class ScheduleUpdateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def beta99(self, interaction: discord.Interaction):
        """Comando para registrar uma nova versão beta 99"""
        try:
            await interaction.response.send_modal(Beta99Modal())
            logging.info(f"{interaction.user.name} abriu o modal de versão beta")
        except Exception as e:
            logging.error(f"Erro ao abrir modal de versão beta: {str(e)}")
            await interaction.response.send_message(
                "Ocorreu um erro ao abrir o formulário. Tente novamente mais tarde.",
                ephemeral=True
            )

    async def agendamento(self, interaction: discord.Interaction):
        """Comando para registrar um novo agendamento"""
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

    async def atualizacao(self, interaction: discord.Interaction):
        """Comando para registrar uma nova atualização"""
        try:
            modal = AtualizacaoModal()
            view = InicialView(modal, interaction.user)
            
            await interaction.response.send_message(
                "**1ª Etapa: Seleção de Responsáveis**\n"
                "A atualização possui mais de um responsável?",
                view=view,
                ephemeral=True
            )
            
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

async def setup(bot):
    await bot.add_cog(ScheduleUpdateCog(bot))
    logging.info("ScheduleUpdateCog adicionado via setup()")