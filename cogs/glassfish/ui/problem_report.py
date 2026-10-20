import logging

import discord

from ..core import config as settings
from ..core.contracts import GlassfishServiceContract
from ..core.permissions import user_can_access_service

class ProblemReportModal(discord.ui.Modal, title="Reportar Problema"):
    def __init__(self, servico: str, service: GlassfishServiceContract):
        super().__init__()
        self.servico = servico
        self.service = service

        self.problema = discord.ui.TextInput(
            style=discord.TextStyle.paragraph,
            placeholder="Explique o que aconteceu e como reproduzir o problema.",
            required=True,
            max_length=1000,
        )
        self.anexos = discord.ui.FileUpload(required=False, min_values=0, max_values=3)
        self.add_item(
            discord.ui.Label(
                text="Descrição do problema",
                description="Inclua as etapas para reproduzir o problema, se possível.",
                component=self.problema,
            )
        )
        self.add_item(
            discord.ui.Label(
                text="Capturas de tela ou arquivos",
                description="Você pode anexar até três arquivos para ilustrar o problema.",
                component=self.anexos,
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        config = self.service.load_services().get(self.servico)
        if not config:
            await interaction.followup.send(
                "Este serviço não está mais cadastrado.",
                ephemeral=True,
            )
            return

        try:
            guild = interaction.guild
            if guild is None:
                await interaction.followup.send(
                    "Este formulário só pode ser enviado no servidor.",
                    ephemeral=True,
                )
                return

            if not user_can_access_service(interaction.user, config):
                await interaction.followup.send(
                    "Você não tem mais permissão para reportar problemas neste serviço.",
                    ephemeral=True,
                )
                return

            role = guild.get_role(settings.CARGO_TI_ID)
            if role is None:
                await interaction.followup.send(
                    "O cargo do setor de TI não está configurado neste servidor.",
                    ephemeral=True,
                )
                return

            channel = guild.get_channel(settings.LOGS_CHANNEL_ID)
            if channel is None:
                channel = await guild.fetch_channel(settings.LOGS_CHANNEL_ID)

            mensagem = (
                f"⚠️ Problema reportado no serviço **{config['nome']}** por <@{interaction.user.id}>\n"
                f"**Descrição:** {self.problema.value}\n"
                f"Aviso para o setor de TI: <@&{settings.CARGO_TI_ID}>"
            )
            files = [await attachment.to_file() for attachment in self.anexos.values]
            await channel.send(mensagem, files=files)
            await interaction.followup.send(
                "Problema reportado para o setor de TI.",
                ephemeral=True,
            )
            logging.info("%s reportou um problema com %s", interaction.user.name, config["nome"])
        except Exception as e:
            logging.exception("Erro ao reportar problema: %s", e)
            await interaction.followup.send(
                "Ocorreu um erro ao reportar o problema. Tente novamente mais tarde.",
                ephemeral=True,
            )
