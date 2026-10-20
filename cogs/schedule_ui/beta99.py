import logging
from datetime import datetime

import discord

from .constants import (
    CANAL_NOTIFICACOES, EMOJI_CLIENTE_99, EMOJI_CHAMADOS_99, EMOJI_DATA_99,
    EMOJI_USER_99, EMOJI_VERSAO_99,
)

class Beta99Modal(discord.ui.Modal, title='Versão Beta 99'):
    def __init__(self, original_data=None):
        super().__init__(custom_id=f"beta99_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        self.original_data = original_data or {}

        self.cliente = discord.ui.TextInput(
            placeholder='Nome do cliente...',
            required=True,
            default=self.original_data.get('cliente', ''),
        )
        self.versao = discord.ui.TextInput(
            placeholder='Ex: X.X.X.99XX',
            required=True,
            default=self.original_data.get('versao', ''),
        )
        self.data = discord.ui.TextInput(
            placeholder='DD/MM/AAAA',
            required=True,
            default=self.original_data.get('data', datetime.now().strftime('%d/%m/%Y')),
        )
        self.chamados = discord.ui.TextInput(
            placeholder='Liste os chamados separados por vírgula...',
            style=discord.TextStyle.paragraph,
            required=True,
            default=self.original_data.get('chamados', ''),
        )

        self.add_item(discord.ui.Label(text='Cliente', component=self.cliente))
        self.add_item(
            discord.ui.Label(
                text='Versão beta',
                description='Informe a versão no formato X.X.X.99XX.',
                component=self.versao,
            )
        )
        self.add_item(
            discord.ui.Label(
                text='Data',
                description='Use o formato DD/MM/AAAA.',
                component=self.data,
            )
        )
        self.add_item(discord.ui.Label(text='Chamados', component=self.chamados))

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            try:
                datetime.strptime(self.data.value.strip(), '%d/%m/%Y')
            except ValueError:
                await interaction.followup.send(
                    "Data inválida. Use o formato DD/MM/AAAA.",
                    ephemeral=True,
                )
                return

            mensagem = [
                "**VERSÃO BETA 99**",
                f"**{EMOJI_CLIENTE_99} • Cliente:** {self.cliente.value}",
                f"**{EMOJI_VERSAO_99} • Versão:** {self.versao.value}",
                f"**{EMOJI_DATA_99} • Data:** {self.data.value}",
                f"**{EMOJI_CHAMADOS_99} • Chamados:** {self.chamados.value}",
                f"**{EMOJI_USER_99} • Lançado por:** <@{interaction.user.id}>"
            ]

            mensagem_final = '\n'.join(mensagem)

            channel = interaction.client.get_channel(CANAL_NOTIFICACOES)
            if channel is None:
                await interaction.followup.send(
                    "O canal de notificações não está disponível.",
                    ephemeral=True,
                )
                return

            await channel.send(content=mensagem_final)
            await interaction.followup.send(
                "Versão beta registrada com sucesso!",
                ephemeral=True,
            )

        except Exception as e:
            logging.exception("Erro ao registrar versão beta: %s", e)
            await interaction.followup.send(
                "Ocorreu um erro ao registrar a versão beta. Tente novamente mais tarde.",
                ephemeral=True,
            )
