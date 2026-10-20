import logging
from datetime import datetime

import discord

from .constants import EMOJI_DATA_AGEND, EMOJI_OBS_AGEND, EMOJI_STATUS_AGEND

class ConfirmarButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="📅 Confirmar Data do Agendamento",
            style=discord.ButtonStyle.primary,
            emoji="🗓️",
            custom_id=f"dat_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        self.is_confirmed = False

    async def callback(self, interaction: discord.Interaction):
        if not self.is_confirmed:
            modal = ConfirmarAgendamentoModal()
            modal.message = interaction.message
            modal.view = self.view
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            content_lines = interaction.message.content.split('\n')
            new_lines = []

            for line in content_lines:
                if "• Data Confirmada:" in line:
                    data = line.split("Data Confirmada:")[1].strip()
                    new_lines.append(f"**{EMOJI_DATA_AGEND} • Data Prevista:** {data}")
                elif "**• Status:**" in line:
                    if "Recebido" in line:
                        new_lines.append(f"**{EMOJI_STATUS_AGEND} • Status:** Recebido por <@{interaction.user.id}> | Aguardando Agendamento")
                    else:
                        new_lines.append(f"**{EMOJI_STATUS_AGEND} • Status:** Pendente | Aguardando Recebimento")
                elif "🎯 **AGENDAMENTO CONFIRMADO**" in line:
                    continue
                else:
                    new_lines.append(line)

            self.is_confirmed = False
            self.label = "📅 Confirmar Data do Agendamento"
            self.style = discord.ButtonStyle.primary

            await interaction.message.edit(content='\n'.join(new_lines), view=self.view)
            await interaction.followup.send("Confirmação de agendamento cancelada!", ephemeral=True)

class ConfirmarAgendamentoModal(discord.ui.Modal, title='Confirmar Agendamento'):
    def __init__(self, original_data=None):
        super().__init__(custom_id=f"confirm_agendamento_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        self.message = None
        self.view = None
        self.original_data = original_data or {}

        self.data_hora = discord.ui.TextInput(
            placeholder='DD/MM/AAAA HH:MM',
            default=self.original_data.get(
                'data_agendamento',
                datetime.now().replace(hour=12, minute=0).strftime('%d/%m/%Y %H:%M'),
            ),
            required=True,
        )

        self.observacao = discord.ui.TextInput(
            placeholder='Observação opcional sobre a confirmação...',
            style=discord.TextStyle.paragraph,
            required=False,
            default=self.original_data.get('observacao', ''),
        )

        self.add_item(
            discord.ui.Label(
                text='Data e hora do agendamento',
                description='Use o formato DD/MM/AAAA HH:MM.',
                component=self.data_hora,
            )
        )
        self.add_item(discord.ui.Label(text='Observação', component=self.observacao))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            datetime.strptime(self.data_hora.value.strip(), '%d/%m/%Y %H:%M')
            await interaction.response.defer(ephemeral=True, thinking=True)

            content_lines = self.message.content.split('\n')
            new_lines = []

            new_lines.append("**AGENDAMENTO**")
            new_lines.append("🎯 **AGENDAMENTO CONFIRMADO** 🎯")

            data_line = f"**{EMOJI_DATA_AGEND} • Data Confirmada:** {self.data_hora.value} por <@{interaction.user.id}>"
            data_found = False
            recebido_por = None
            obs_found = False

            for line in content_lines[1:]:
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
                    pass
                elif line.startswith("1️⃣") or line.startswith("2️⃣"):
                    pass
                else:
                    new_lines.append(line)

            if not data_found:
                new_lines.insert(-1, data_line)

            if not obs_found and self.observacao.value and self.observacao.value.strip():
                new_lines.insert(-1, f"**{EMOJI_OBS_AGEND} • Observação da Confirmação:** {self.observacao.value}")

            new_lines.append("\n**INSTRUÇÕES PARA OS RESPONSÁVEIS:**")
            new_lines.append("✅ **Status Atual**: Agendamento confirmado")
            new_lines.append("\n**Histórico de Ações:**")
            if recebido_por:
                new_lines.append(f"📋 Solicitação recebida por {recebido_por}")
            else:
                new_lines.append(f"📋 Solicitação recebida por <@{interaction.user.id}>")
            new_lines.append(f"🗓️ Data confirmada por <@{interaction.user.id}>")

            for item in self.view.children:
                if isinstance(item, ConfirmarButton):
                    item.is_confirmed = True
                    item.label = "Cancelar Confirmação"
                    item.style = discord.ButtonStyle.danger

            await self.message.edit(content='\n'.join(new_lines), view=self.view)
            await interaction.followup.send("Agendamento confirmado com sucesso!", ephemeral=True)

        except ValueError:
            error_message = "Formato de data inválido. Use DD/MM/AAAA HH:MM."
            if interaction.response.is_done():
                await interaction.followup.send(error_message, ephemeral=True)
            else:
                await interaction.response.send_message(error_message, ephemeral=True)
        except Exception as e:
            logging.error(f"Erro ao confirmar agendamento: {str(e)}")
            error_message = "Ocorreu um erro ao confirmar o agendamento. Tente novamente mais tarde."
            if interaction.response.is_done():
                await interaction.followup.send(error_message, ephemeral=True)
            else:
                await interaction.response.send_message(error_message, ephemeral=True)

