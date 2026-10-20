import logging
from typing import Any, Dict

import discord

from ..core import config as settings
from ..core.contracts import GlassfishServiceContract

class RolePermissionView(discord.ui.View):
    def __init__(
        self,
        service_data: Dict[str, Any],
        serv_id: str,
        bot,
        service: GlassfishServiceContract,
    ):
        super().__init__(timeout=180)
        self.selected_roles = []
        self.service_data = service_data
        self.serv_id = serv_id
        self.bot = bot
        self.service = service

        self.add_item(RolePermissionSelect(self))

    @discord.ui.button(label="Confirmar", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.selected_roles:
            await interaction.response.send_message("⚠️ Por favor, selecione pelo menos um cargo antes de confirmar.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            def add_service(services):
                if self.serv_id in services:
                    return False, "already_exists"
                services[self.serv_id] = {
                    "nome": self.service_data["nome"],
                    "status": "disponível",
                    "usuario": None,
                    "grupos_permitidos": list(self.selected_roles),
                }
                return True, "added"

            saved, result = await self.service.update_services(add_service)
            if not saved:
                await interaction.followup.send(
                    "Não foi possível salvar o serviço. Tente novamente.",
                    ephemeral=True,
                )
                return
            if result == "already_exists":
                await interaction.followup.send(
                    f"Já existe um serviço com o ID '{self.serv_id}'.",
                    ephemeral=True,
                )
                return

            if self.bot:
                glassfish_cog = self.bot.get_cog("GlassfishCog")
                if glassfish_cog:
                    await glassfish_cog.refresh_persistent_message()
            else:
                glassfish_cog = interaction.client.get_cog("GlassfishCog")
                if glassfish_cog:
                    await glassfish_cog.refresh_persistent_message()

            cargo_mentions = []
            cargo_names = []
            for role_id in self.selected_roles:
                role = interaction.guild.get_role(int(role_id))
                if role:
                    cargo_mentions.append(role.mention)
                    cargo_names.append(role.name)

            if cargo_mentions:
                cargos_texto = ", ".join(cargo_mentions)
            else:
                cargos_texto = "Nenhum"
            if cargo_names:
                cargos_nomes = ", ".join(cargo_names)
            else:
                cargos_nomes = "Nenhum"

            try:
                for child in self.children:
                    child.disabled = True

                await interaction.message.edit(
                    content=f"✅ **Configuração Concluída**\nServiço **{self.service_data['nome']}** configurado com sucesso!",
                    view=self
                )
            except discord.NotFound:
                logging.warning("Não foi possível editar a mensagem de configuração do serviço")
            except Exception as edit_error:
                logging.error(f"Erro ao editar mensagem: {str(edit_error)}")

            await interaction.followup.send(
                f"✅ Serviço **{self.service_data['nome']}** adicionado com sucesso!\n"
                f"**Cargos permitidos:** {cargos_nomes}",
                ephemeral=True,
            )

            try:
                log_channel = interaction.guild.get_channel(settings.LOGS_CHANNEL_ID)
                if log_channel is None:
                    log_channel = await interaction.guild.fetch_channel(settings.LOGS_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(
                        f"🆕 **Novo serviço Glassfish adicionado**\n"
                        f"**ID:** {self.serv_id}\n"
                        f"**Nome:** {self.service_data['nome']}\n"
                        f"**Cargos permitidos:** {cargos_texto}\n"
                        f"**Adicionado por:** {interaction.user.mention}"
                    )

                    logging.info(f"Novo serviço {self.serv_id} ({self.service_data['nome']}) adicionado por {interaction.user.name} com cargos: {cargos_nomes}")
            except Exception as e:
                logging.error(f"Erro ao enviar log de novo serviço: {str(e)}")

            self.stop()

        except Exception as e:
            logging.exception("Erro ao adicionar serviço: %s", e)
            await interaction.followup.send(
                "❌ Ocorreu um erro ao adicionar o serviço.",
                ephemeral=True,
            )

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            for item in self.children:
                item.disabled = True

            try:
                await interaction.response.edit_message(
                    content="🚫 Operação cancelada!",
                    view=self
                )
            except discord.NotFound:
                logging.warning("Não foi possível editar a mensagem de cancelamento - ela pode ter sido excluída")
            except Exception as edit_error:
                logging.error(f"Erro ao editar mensagem de cancelamento: {str(edit_error)}")

            try:
                await interaction.followup.send(
                    "Operação cancelada. Nenhum serviço foi adicionado.",
                    ephemeral=True
                )
            except Exception as followup_error:
                logging.error(f"Erro ao enviar followup de cancelamento: {str(followup_error)}")

            self.stop()
        except Exception as e:
            logging.error(f"Erro ao processar cancelamento: {str(e)}")
            try:
                await interaction.response.send_message("Erro ao cancelar operação.", ephemeral=True)
            except (discord.HTTPException, discord.InteractionResponded) as response_error:
                logging.warning(f"Não foi possível responder ao cancelamento: {response_error}")

class RolePermissionSelect(discord.ui.RoleSelect):
    def __init__(self, parent_view: RolePermissionView):
        self.parent_view = parent_view
        super().__init__(
            placeholder="Selecione os cargos permitidos",
            min_values=0,
            max_values=10,
        )

    async def callback(self, interaction: discord.Interaction):
        invalid_roles = [
            role
            for role in self.values
            if role.is_default() or role.is_integration() or role.is_bot_managed()
        ]
        if invalid_roles:
            await interaction.response.send_message(
                "Não selecione @everyone, cargos de integração ou cargos gerenciados por bots.",
                ephemeral=True,
            )
            return

        self.parent_view.selected_roles = [str(role.id) for role in self.values]
        if self.values:
            selected_roles = ", ".join(role.name for role in self.values)
        else:
            selected_roles = "nenhum"

        await interaction.response.send_message(
            f"{len(self.parent_view.selected_roles)} cargo(s) selecionado(s): {selected_roles}",
            ephemeral=True,
        )
