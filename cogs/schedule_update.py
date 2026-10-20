import logging

import discord
from discord.ext import commands

from .schedule_ui import (
    CANAL_NOTIFICACOES,
    EMOJI_CLIENTE_AGEND,
    EMOJI_CHAMADO_AGEND,
    EMOJI_DATA_AGEND,
    EMOJI_OBS_AGEND,
    EMOJI_STATUS_AGEND,
    EMOJI_USER_AGEND,
    EMOJI_VERSAO_AGEND,
    EMOJI_CLIENTE_ATUALIZACAO,
    EMOJI_VERS_CORP_ATUALIZACAO,
    EMOJI_VERS_WEB_ATUALIZACAO,
    EMOJI_VERS_CONT_ATUALIZACAO,
    EMOJI_DATA_ATUALIZACAO,
    EMOJI_CHAMADOS_ATUALIZACAO,
    EMOJI_OBS_ATUALIZACAO,
    EMOJI_USER_ATUALIZACAO,
    EMOJI_VERSAO_ATUALIZACAO,
    EMOJI_CLIENTE_99,
    EMOJI_VERSAO_99,
    EMOJI_DATA_99,
    EMOJI_CHAMADOS_99,
    EMOJI_USER_99,
    StatusButton,
    EditButton,
    DeleteButton,
    ConfirmarButton,
    ConfirmarAgendamentoModal,
    CustomView,
    Beta99Modal,
    AgendamentoModal,
    RoleSelect,
    ConfirmarAgendamentoButton,
    PularButton,
    RoleSelectorView,
    AtualizacaoModal,
    ConfirmButton,
    ResponsaveisSelect,
    AtualizacaoView,
    NaoButton,
    SimButton,
    InicialView,
)


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
            except discord.HTTPException as followup_error:
                logging.warning(f"Não foi possível enviar a resposta de agendamento: {followup_error}")
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
            except discord.HTTPException as followup_error:
                logging.warning(f"Não foi possível enviar a resposta de atualização: {followup_error}")
        except Exception as e:
            logging.error(f"Erro ao abrir modal de atualização: {str(e)}")
            await interaction.response.send_message(
                "Ocorreu um erro ao abrir o formulário. Tente novamente mais tarde.",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(ScheduleUpdateCog(bot))
    logging.info("ScheduleUpdateCog adicionado via setup()")
