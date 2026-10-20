import logging
from datetime import datetime

import discord

from .components import CustomView
from .constants import (
    CANAL_NOTIFICACOES, EMOJI_CHAMADO_AGEND, EMOJI_CLIENTE_AGEND, EMOJI_DATA_AGEND,
    EMOJI_OBS_AGEND, EMOJI_STATUS_AGEND, EMOJI_USER_AGEND, EMOJI_VERSAO_AGEND,
)

class AgendamentoModal(discord.ui.Modal, title='Agendamento'):
    def __init__(self, original_data=None):
        super().__init__(custom_id=f"agendamento_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        self.message_to_edit = None
        self.author_id = None
        self.selected_role = None
        self.original_data = original_data or {}

        self.cliente = discord.ui.TextInput(
            placeholder='Nome do cliente...',
            required=True,
            default=self.original_data.get('cliente', '')
        )

        self.chamado = discord.ui.TextInput(
            placeholder='Número do chamado...',
            required=False,
            default=self.original_data.get('chamado', '')
        )

        self.data_agendamento = discord.ui.TextInput(
            placeholder='DD/MM/AAAA HH:MM',
            default=self.original_data.get('data_agendamento',
                   (datetime.now().replace(hour=12, minute=0)).strftime('%d/%m/%Y %H:%M')),
            required=False,
        )

        self.observacao = discord.ui.TextInput(
            placeholder='Observações adicionais...',
            style=discord.TextStyle.paragraph,
            required=False,
            default=self.original_data.get('observacao', '')
        )

        self.add_item(discord.ui.Label(text='Cliente', component=self.cliente))
        self.add_item(discord.ui.Label(text='Chamado', component=self.chamado))
        self.add_item(
            discord.ui.Label(
                text='Data prevista',
                description='Use o formato DD/MM/AAAA HH:MM.',
                component=self.data_agendamento,
            )
        )
        self.add_item(discord.ui.Label(text='Observação', component=self.observacao))

    async def on_submit(self, interaction: discord.Interaction):
        self.author_id = interaction.user.id

        if self.data_agendamento.value and self.data_agendamento.value.strip():
            try:
                datetime.strptime(self.data_agendamento.value.strip(), '%d/%m/%Y %H:%M')
            except ValueError:
                await interaction.response.send_message(
                    "Formato de data inválido. Use DD/MM/AAAA HH:MM.",
                    ephemeral=True
                )
                return

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
        if self.values:
            self.modal.selected_role = self.values[0]
            role_text = self.values[0].mention
        else:
            self.modal.selected_role = None
            role_text = "Nenhum cargo selecionado"

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
            style=discord.ButtonStyle.success,
            emoji="✅",
            custom_id=f"confirm_role_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        self.modal = modal

    async def callback(self, interaction: discord.Interaction):
        if self.modal.author_id:
            author_id = self.modal.author_id
        else:
            author_id = interaction.user.id

        mensagem = [
            "**AGENDAMENTO**",
        ]

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

        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            if self.modal.message_to_edit:
                await self.modal.message_to_edit.edit(content=mensagem_final, view=view)
                success_message = "Agendamento atualizado com sucesso!"
                action = "atualizou"
            else:
                channel = interaction.client.get_channel(CANAL_NOTIFICACOES)
                if channel is None:
                    await interaction.followup.send(
                        "O canal de notificações não está disponível.",
                        ephemeral=True,
                    )
                    return

                message = await channel.send(content=mensagem_final, view=view)
                bot = interaction.client
                if hasattr(bot, "save_interactive_message"):
                    bot.save_interactive_message(
                        message.id,
                        channel.id,
                        "agendamento",
                        author_id,
                        original_data,
                    )
                success_message = "Agendamento registrado com sucesso!"
                action = "registrou"

            await interaction.followup.send(success_message, ephemeral=True)
            logging.info(
                "%s %s um agendamento para %s",
                interaction.user.name,
                action,
                self.modal.cliente.value,
            )
        except discord.HTTPException as error:
            logging.exception("Erro ao publicar agendamento: %s", error)
            await interaction.followup.send(
                "Não foi possível publicar o agendamento. Tente novamente mais tarde.",
                ephemeral=True,
            )

class PularButton(discord.ui.Button):
    def __init__(self, modal: AgendamentoModal):
        super().__init__(
            label="Pular (Sem notificação)",
            style=discord.ButtonStyle.secondary,
            emoji="⏭️",
            custom_id=f"skip_role_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        self.modal = modal

    async def callback(self, interaction: discord.Interaction):
        self.modal.selected_role = None
        confirmar = ConfirmarAgendamentoButton(self.modal)
        await confirmar.callback(interaction)

class RoleSelectorView(discord.ui.View):
    def __init__(self, modal: AgendamentoModal):
        super().__init__(timeout=None)
        self.modal = modal
        self.add_item(RoleSelect(modal))
        self.add_item(ConfirmarAgendamentoButton(modal))
        self.add_item(PularButton(modal))
