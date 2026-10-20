import logging

import discord

from .base import GlassfishCommandBase
from ..core.permissions import roles_can_access_service
from ..ui.services import ServiceDropdown

class GlassfishUserCommands(GlassfishCommandBase):
    async def cmd_glassfish(self, interaction: discord.Interaction):
        """Lista os serviços disponíveis"""
        try:
            logging.info(f"{interaction.user.name} executou o comando /glassfish")

            if not interaction.user.roles:
                await interaction.response.send_message(
                    "Você precisa ter um cargo para acessar os serviços.",
                    ephemeral=True
                )
                return

            user_roles = [role.id for role in interaction.user.roles]
            logging.info(f"Cargos do usuário {interaction.user.name}: {user_roles}")

            servicos_config = self.service.load_services()
            role_ids = set(user_roles)
            servicos_permitidos = {
                service_id: config
                for service_id, config in servicos_config.items()
                if roles_can_access_service(role_ids, config)
            }

            if not servicos_permitidos:
                await interaction.response.send_message(
                    "Você não tem permissão para acessar nenhum serviço.",
                    ephemeral=True
                )
                logging.info(f"{interaction.user.name} tentou acessar serviços sem permissão")
                return

            view = ServiceDropdown(user_roles, servicos_permitidos, self.service)
            await interaction.response.send_message(
                "**Serviços disponíveis:** Selecione uma opção abaixo:",
                view=view,
                ephemeral=True
            )

        except Exception as e:
            logging.error(f"Erro ao executar comando glassfish: {str(e)}")
            await interaction.response.send_message(
                "Ocorreu um erro ao listar os serviços. Tente novamente mais tarde.",
                ephemeral=True
            )

    async def cmd_obter_timeout_glassfish(self, interaction: discord.Interaction):
        """Mostra as configurações atuais de timeout"""
        config = self.service.get_config()["timeout"]
        await interaction.response.send_message(
            f"**Configurações atuais de timeout dos serviços Glassfish:**\n" +
            f"- Tempo máximo sem confirmação: {config['tempo_maximo_uso']} horas\n" +
            f"- Intervalo de lembretes: {config['lembrete_intervalo']} horas\n" +
            f"- Verificação de serviços: a cada {config['verificar_intervalo']} minutos\n" +
            f"- Limite de extensões permitidas: {config['max_extensoes']} vezes",
            ephemeral=True
        )
