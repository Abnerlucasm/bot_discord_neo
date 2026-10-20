import datetime
import logging

import discord

from ..core import config as settings
from ..core.contracts import GlassfishServiceContract
from ..core.models import UsageData
from ..core.ownership import is_service_owner
from ..core.permissions import user_can_access_service, user_has_ti_role
from .problem_report import ProblemReportModal

class ActionButtons(discord.ui.View):
    def __init__(
        self,
        service_id: str,
        service: GlassfishServiceContract,
    ):
        super().__init__(timeout=None)
        self.service_id = service_id
        self.service = service
        self.add_item(self.create_button("Usar", "❎", discord.ButtonStyle.primary, f"usar_{service_id}"))
        self.add_item(self.create_button("Liberar", "✅", discord.ButtonStyle.success, f"liberar_{service_id}"))
        self.add_item(self.create_button("Reportar problema", "⚠️", discord.ButtonStyle.danger, f"reportar_{service_id}"))

    def create_button(self, label: str, emoji: str, style: discord.ButtonStyle, custom_id: str):
        button = discord.ui.Button(label=label, emoji=emoji, style=style, custom_id=custom_id)
        button.callback = self.handle_callback
        return button

    async def handle_callback(self, interaction: discord.Interaction):
        custom_id = interaction.data["custom_id"]
        action_type = custom_id.split("_")[0]

        service_config = self.service.load_services().get(self.service_id)
        if not service_config:
            await interaction.response.send_message(
                "Este serviço não está mais cadastrado.",
                ephemeral=True,
            )
            return

        if interaction.guild is None:
            await interaction.response.send_message(
                "Esta ação só pode ser usada no servidor.",
                ephemeral=True,
            )
            return

        if action_type in {"usar", "reportar"} and not user_can_access_service(interaction.user, service_config):
            await interaction.response.send_message(
                "Você não tem permissão para acessar este serviço.",
                ephemeral=True,
            )
            return

        if action_type == "usar":
            result = await self.usar(interaction)
        elif action_type == "liberar":
            result = await self.liberar(interaction)
        elif action_type == "reportar":
            await self.reportar_problema(interaction)
            return
        else:
            await interaction.response.send_message("Ação inválida.", ephemeral=True)
            return

        if result:
            await self.service.refresh_persistent_message()

    async def usar(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        def claim_service(config):
            if not user_can_access_service(interaction.user, config):
                return False, ("forbidden", dict(config))

            if config.get("status") == "em uso":
                return False, ("in_use", dict(config))

            config["status"] = "em uso"
            config["usuario"] = interaction.user.name
            config["usage_data"] = UsageData(
                interaction.user.name,
                interaction.user.id,
            ).to_dict()
            config.pop("notificacao_timeout", None)
            return True, ("claimed", dict(config))

        saved, result, config = await self.service.update_service(self.service_id, claim_service)
        if result == "not_found" or not config:
            await interaction.followup.send(
                "Este serviço não está mais cadastrado.",
                ephemeral=True,
            )
            return False
        if not saved:
            await interaction.followup.send(
                "Não foi possível salvar a alteração. Tente novamente.",
                ephemeral=True,
            )
            return False
        if result[0] == "forbidden":
            await interaction.followup.send(
                "Você não tem mais permissão para usar este serviço.",
                ephemeral=True,
            )
            return False
        if result[0] == "in_use":
            await interaction.followup.send(
                f"O serviço **{config['nome']}** já está em uso por {config['usuario']}.",
                ephemeral=True,
            )
            logging.info(f"{interaction.user.name} tentou usar {config['nome']}, mas já está em uso")
            return False

        channel = interaction.guild.get_channel(settings.LOGS_CHANNEL_ID)
        if channel:
            await channel.send(
                f"O serviço **{config['nome']}** está sendo usado por <@{interaction.user.id}> <:stop:1328441358188417025>"
            )

        await interaction.followup.send(
            f"O serviço **{config['nome']}** está sendo usado por <@{interaction.user.id}> <:stop:1328441358188417025>\n\n" +
            f"⚠️ **Importante**:\n" +
            f"- Você receberá lembretes a cada {self.service.lembrete_intervalo} horas para confirmar que ainda está usando o serviço\n" +
            f"- Se não houver confirmação por {self.service.tempo_maximo_uso} horas, o serviço será liberado automaticamente\n" +
            f"- Por favor, libere o serviço quando terminar de usá-lo",
            ephemeral=True,
        )
        logging.info(f"{interaction.user.name} começou a usar o serviço {config['nome']}")
        return True

    async def liberar(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        is_admin = user_has_ti_role(interaction.user)

        def release_service(config):
            if config.get("status") == "disponível":
                return False, ("available", dict(config), config.get("usuario"))
            if not is_service_owner(config, interaction.user) and not is_admin:
                return False, ("forbidden", dict(config), config.get("usuario"))

            previous_owner = config.get("usuario")
            config.pop("usage_data", None)
            config.pop("notificacao_timeout", None)
            config["status"] = "disponível"
            config["usuario"] = None
            return True, ("released", dict(config), previous_owner)

        saved, result, config = await self.service.update_service(self.service_id, release_service)
        if result == "not_found" or not config:
            await interaction.followup.send(
                "Este serviço não está mais cadastrado.",
                ephemeral=True,
            )
            return False
        if not saved:
            await interaction.followup.send(
                "Não foi possível salvar a alteração. Tente novamente.",
                ephemeral=True,
            )
            return False

        result_type, config, previous_owner = result
        if result_type == "available":
            await interaction.followup.send(
                f"O serviço **{config['nome']}** já está disponível.",
                ephemeral=True,
            )
            logging.info(f"{interaction.user.name} tentou liberar {config['nome']}, mas já está disponível")
            return False
        if result_type == "forbidden":
            await interaction.followup.send(
                f"Apenas {config['usuario']} pode liberar este serviço. Se precisar de ajuda, contate o setor de TI.",
                ephemeral=True,
            )
            logging.warning(f"{interaction.user.name} tentou liberar {config['nome']}, mas não tem permissão")
            return False
        if previous_owner != interaction.user.name:
            logging.info(f"Admin {interaction.user.name} liberou {config['nome']} que estava em uso por outro usuário")

        channel = interaction.guild.get_channel(settings.LOGS_CHANNEL_ID)
        if channel:
            await channel.send(
                f"O serviço **{config['nome']}** foi liberado por <@{interaction.user.id}> <:start:1328441356682793062>"
            )
        await interaction.followup.send(
            f"O serviço **{config['nome']}** foi liberado por <@{interaction.user.id}> <:start:1328441356682793062>",
            ephemeral=True,
        )
        logging.info(f"{interaction.user.name} liberou o serviço {config['nome']}")
        return True

    async def reportar_problema(self, interaction: discord.Interaction):
        modal = ProblemReportModal(self.service_id, self.service)
        await interaction.response.send_modal(modal)

class ConfirmUseButton(discord.ui.Button):
    def __init__(self, service_id: str, service: GlassfishServiceContract):
        super().__init__(
            label="Continuar usando o serviço",
            style=discord.ButtonStyle.primary,
            emoji="✅",
            custom_id=f"glassfish:confirm:{service_id}",
        )
        self.service_id = service_id
        self.service = service

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        service = self.service
        max_extensoes = service.max_extensoes

        def confirm_usage(config):
            if config.get("status") != "em uso" or not is_service_owner(config, interaction.user):
                return False, ("not_owner", 0)

            try:
                usage_data = UsageData.from_dict(config["usage_data"])
            except (AttributeError, KeyError, TypeError, ValueError) as error:
                logging.error(f"Erro ao processar dados de uso: {error}")
                usage_data = UsageData(interaction.user.name, interaction.user.id)

            extension_count = usage_data.extension_count
            if usage_data.last_check:
                elapsed_hours = (datetime.datetime.now() - usage_data.last_check).total_seconds() / 3600
                if elapsed_hours > service.tempo_maximo_uso:
                    extension_count = usage_data.increment_extension()
                    if extension_count > max_extensoes:
                        return False, ("limit_reached", extension_count)
                    result = "extended"
                else:
                    result = "confirmed"
            else:
                result = "confirmed"

            usage_data.update_check()
            config["usage_data"] = usage_data.to_dict()
            return True, (result, extension_count)

        saved, result, config = await service.update_service(self.service_id, confirm_usage)
        if result == "not_found" or not config:
            await interaction.followup.send(
                "Este serviço não está mais cadastrado.",
                ephemeral=True,
            )
            return
        if not saved:
            await interaction.followup.send(
                "Não foi possível salvar a confirmação. Tente novamente.",
                ephemeral=True,
            )
            return

        result_type, extension_count = result
        if result_type == "not_owner":
            await interaction.followup.send(
                "Este serviço não está mais associado ao seu usuário.",
                ephemeral=True,
            )
            return
        if result_type == "limit_reached":
            await interaction.followup.send(
                f"❌ Você já utilizou {extension_count - 1}/{max_extensoes} extensões permitidas e não pode mais estender o tempo de uso.\n"
                "O serviço será liberado automaticamente em breve.\n"
                "Por favor, libere o serviço manualmente ou solicite uma exceção ao setor de TI.",
                ephemeral=True,
            )
            return
        if result_type == "extended":
            await interaction.followup.send(
                f"✅ Tempo de uso estendido! Você utilizou {extension_count}/{max_extensoes} extensões permitidas.\n"
                f"O prazo para uso do serviço **{config['nome']}** foi renovado. Obrigado!",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                f"✅ Você confirmou que ainda está usando o serviço **{config['nome']}**. Obrigado!",
                ephemeral=True,
            )

        try:
            channel = interaction.client.get_channel(settings.LOGS_CHANNEL_ID)
            if channel:
                if extension_count > 0:
                    await channel.send(
                        f"🔄 **Extensão de Uso**: <@{interaction.user.id}> confirmou o uso do serviço **{config['nome']}** "
                        f"({extension_count}/{max_extensoes} extensões utilizadas)"
                    )
                else:
                    await channel.send(
                        f"✅ **Confirmação de Uso**: <@{interaction.user.id}> confirmou que ainda está usando o serviço **{config['nome']}**"
                    )
        except Exception as error:
            logging.error(f"Erro ao enviar mensagem para o canal de logs: {error}")

        logging.info(f"Uso confirmado para o serviço {self.service_id} por {interaction.user.name}")

class LiberarButton(discord.ui.Button):
    def __init__(self, service_id: str, service: GlassfishServiceContract):
        super().__init__(
            label="Liberar o serviço",
            style=discord.ButtonStyle.danger,
            emoji="🔄",
            custom_id=f"glassfish:release:{service_id}",
        )
        self.service_id = service_id
        self.service = service

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        def release_service(config):
            if config.get("status") != "em uso":
                return False, ("available", dict(config))
            if not is_service_owner(config, interaction.user):
                return False, ("forbidden", dict(config))

            config.pop("usage_data", None)
            config.pop("notificacao_timeout", None)
            config["status"] = "disponível"
            config["usuario"] = None
            return True, ("released", dict(config))

        saved, result, config = await self.service.update_service(self.service_id, release_service)
        if result == "not_found" or not config:
            await interaction.followup.send(
                "Este serviço não está mais cadastrado.",
                ephemeral=True,
            )
            return
        if not saved:
            await interaction.followup.send(
                "Não foi possível salvar a liberação. Tente novamente.",
                ephemeral=True,
            )
            return

        result_type, config = result
        if result_type == "available":
            await interaction.followup.send("Este serviço já está disponível.", ephemeral=True)
            return
        if result_type == "forbidden":
            await interaction.followup.send(
                f"Apenas {config['usuario']} pode liberar este serviço.",
                ephemeral=True,
            )
            return

        try:
            channel = interaction.client.get_channel(settings.LOGS_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"O serviço **{config['nome']}** foi liberado por <@{interaction.user.id}> <:start:1328441356682793062>"
                )
        except Exception as error:
            logging.error(f"Erro ao enviar mensagem para o canal de logs: {error}")

        await interaction.followup.send(
            f"✅ Você liberou o serviço **{config['nome']}**.",
            ephemeral=True,
        )
        await self.service.refresh_persistent_message()

class CheckView(discord.ui.View):
    def __init__(self, service_id: str, service: GlassfishServiceContract):
        super().__init__(timeout=None)
        self.add_item(ConfirmUseButton(service_id, service))
        self.add_item(LiberarButton(service_id, service))
