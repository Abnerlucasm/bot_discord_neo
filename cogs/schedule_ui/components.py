import logging
import re
from datetime import datetime

import discord

from .agendamento_confirm import ConfirmarButton
from .constants import EMOJI_DATA_AGEND, EMOJI_OBS_AGEND, EMOJI_STATUS_AGEND

class StatusButton(discord.ui.Button):
    def __init__(self, status="Pendente", label=None, style=None):
        if style is None:
            if status == "Pendente":
                style = discord.ButtonStyle.danger
            else:
                style = discord.ButtonStyle.success

        if label is None:
            if status == "Pendente":
                label = "⚠️ Aguardando Recebimento"
            else:
                label = "✅ Solicitação Recebida"

        super().__init__(
            label=label,
            style=style,
            emoji="📋",
            custom_id=f"rcv_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        self.status = status

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
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

        is_agendado = any("Data Confirmada:" in line for line in content_lines)
        if is_agendado:
            status_complement = "Agendado"
        elif self.status == "Recebido":
            status_complement = "Aguardando Agendamento"
        else:
            status_complement = "Aguardando Recebimento"

        if self.status == "Recebido":
            recebido_por = f"<@{interaction.user.id}>"
        else:
            recebido_por = ""
        if recebido_por:
            autor_status = f" por {recebido_por}"
        else:
            autor_status = ""
        confirmado_por = None

        for line in content_lines:
            if line.startswith("**INSTRUÇÕES PARA OS RESPONSÁVEIS") or \
               line.startswith("**Histórico de Ações") or \
               line.startswith("1️⃣") or line.startswith("2️⃣") or \
               line.startswith("✅ **Status Atual") or \
               line.startswith("📋 Solicitação recebida") or \
               line.startswith("🗓️ Data confirmada") or \
               line == "":
                continue

            if "Solicitado por:" in line:
                new_lines.append(line)
                continue

            if "Data Confirmada:" in line:
                if "por" in line:
                    confirmado_por = line.split("por")[1].strip()

            if "**• Status:**" in line:
                status_line = f"**{EMOJI_STATUS_AGEND} • Status: **{self.status}{autor_status} | {status_complement}"
                new_lines.append(status_line)
            else:
                new_lines.append(line)

        if self.status == "Recebido":
            new_lines.append("")
            new_lines.append("**INSTRUÇÕES PARA OS RESPONSÁVEIS:**")
            if is_agendado:
                new_lines.append("✅ **Status Atual**: Agendamento confirmado")
            else:
                new_lines.append("✅ **Status Atual**: Solicitação recebida, aguardando confirmação da data")
                new_lines.append("2️⃣ Clique em \"🗓️ Confirmar Data do Agendamento\" para definir a data confirmada")

            new_lines.append("")
            new_lines.append("**Histórico de Ações:**")
            new_lines.append(f"📋 Solicitação recebida por {recebido_por}")
            if confirmado_por:
                new_lines.append(f"🗓️ Data confirmada por {confirmado_por}")
        else:
            new_lines.append("")
            new_lines.append("**INSTRUÇÕES PARA OS RESPONSÁVEIS:**")
            new_lines.append("1️⃣ Clique em \"📋 Aguardando Recebimento\" para indicar que você recebeu a solicitação")
            new_lines.append("2️⃣ Clique em \"🗓️ Confirmar Data do Agendamento\" para definir a data confirmada")

        try:
            from cogs.utils import get_instance_persistence
            persistence = get_instance_persistence()
            message_data = await persistence.get_message_data(str(interaction.message.id))

            if message_data:
                view_type = message_data.get('view_type', 'agendamento')
                original_data = message_data.get('original_data', {})
                author_id = message_data.get('author_id', str(interaction.user.id))

                view = CustomView(view_type, original_data, int(author_id))

                for child in view.children:
                    if isinstance(child, StatusButton):
                        child.status = self.status
                        child.style = self.style
                        child.label = self.label
                        child.emoji = self.emoji

                await interaction.message.edit(content='\n'.join(new_lines), view=view)
            else:
                components = interaction.message.components
                if components:
                    view_type = "agendamento"
                    if "ATUALIZAÇÃO" in interaction.message.content:
                        view_type = "atualizacao"
                    elif "VERSÃO BETA 99" in interaction.message.content:
                        view_type = "beta99"

                    author_id = None
                    author_pattern = r"Solicitado por: <@(\d+)>"
                    author_match = re.search(author_pattern, interaction.message.content)
                    if author_match:
                        author_id = author_match.group(1)
                    else:
                        author_id = str(interaction.user.id)

                    view = CustomView(view_type, {}, int(author_id))
                    await interaction.message.edit(content='\n'.join(new_lines), view=view)
                else:
                    await interaction.message.edit(content='\n'.join(new_lines))
        except Exception as e:
            logging.error(f"Erro ao atualizar view após alteração de status: {str(e)}")
            try:
                await interaction.message.edit(content='\n'.join(new_lines))
            except discord.HTTPException as edit_error:
                logging.warning(f"Não foi possível atualizar a mensagem: {edit_error}")

        await interaction.followup.send(f"Você alterou o status para: **{self.status}**", ephemeral=True)

class EditButton(discord.ui.Button):
    def __init__(self, modal_type: str, original_data: dict, author_id: int):
        super().__init__(
            label="Editar",
            style=discord.ButtonStyle.primary,
            emoji="✏️",
            custom_id=f"edt_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
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
            from .agendamento import AgendamentoModal

            modal = AgendamentoModal()
            modal.cliente.default = self.original_data.get("cliente", "")
            modal.chamado.default = self.original_data.get("chamado", "")
            modal.data_agendamento.default = self.original_data.get("data_agendamento", "")
            modal.observacao.default = self.original_data.get("observacao", "")
        else:
            from .atualizacao import AtualizacaoModal

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
        super().__init__(
            label="Excluir",
            style=discord.ButtonStyle.danger,
            emoji="🗑️",
            custom_id=f"del_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        self.author_id = author_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Apenas o autor original pode excluir esta mensagem.",
                ephemeral=True
            )
            return

        bot = interaction.client
        if hasattr(bot, 'remove_interactive_message'):
            bot.remove_interactive_message(interaction.message.id)

        await interaction.response.defer(ephemeral=True, thinking=True)
        await interaction.message.delete()
        await interaction.followup.send(
            "Mensagem excluída com sucesso!",
            ephemeral=True
        )

class CustomView(discord.ui.View):
    def __init__(self, modal_type: str, original_data: dict, author_id: int):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.modal_type = modal_type
        self.original_data = original_data

        view_id = datetime.now().strftime('%Y%m%d%H%M%S')

        if modal_type == "agendamento":
            status_button = StatusButton()
            status_button.custom_id = f"rcv_{view_id}_{modal_type}"
            self.add_item(status_button)

            confirmar_button = ConfirmarButton()
            confirmar_button.custom_id = f"dat_{view_id}_{modal_type}"
            self.add_item(confirmar_button)

        self.edit_button = EditButton(modal_type, original_data, author_id)
        self.edit_button.custom_id = f"edt_{view_id}_{modal_type}"

        self.delete_button = DeleteButton(author_id)
        self.delete_button.custom_id = f"del_{view_id}_{modal_type}"

        self.add_item(self.edit_button)
        self.add_item(self.delete_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        component_id = interaction.data.get('custom_id', '')

        edit_custom_id = self.edit_button.custom_id
        delete_custom_id = self.delete_button.custom_id

        if (component_id in [edit_custom_id, delete_custom_id] and
            interaction.user.id != self.author_id):
            await interaction.response.send_message(
                "Apenas o autor original pode usar este botão.",
                ephemeral=True
            )
            return False

        return True
