import logging
from math import ceil
from typing import Any, Dict

import discord

from ..core import config as settings
from ..core.contracts import GlassfishServiceContract
from .service_forms import GlassfishAddModal, GlassfishEditModal

OPTIONS_PER_PAGE = 25


class GlassfishSelectView(discord.ui.View):
    def __init__(
        self,
        service: GlassfishServiceContract,
        servicos_config: Dict[str, Any],
        action_type: str,
        page: int = 0,
    ):
        super().__init__(timeout=180)
        self.service = service
        self.servicos_config = servicos_config
        self.action_type = action_type
        self.page = page

        page_count = max(1, ceil(len(servicos_config) / OPTIONS_PER_PAGE))
        self.page = min(max(page, 0), page_count - 1)
        self.add_item(GlassfishSelect(service, servicos_config, action_type, self.page))
        if page_count > 1:
            previous_page = GlassfishSelectPageButton(self, self.page - 1, "Anterior", "glassfish:admin:previous")
            next_page = GlassfishSelectPageButton(self, self.page + 1, "Próxima", "glassfish:admin:next")
            previous_page.disabled = self.page == 0
            next_page.disabled = self.page == page_count - 1
            self.add_item(previous_page)
            self.add_item(next_page)

class GlassfishSelect(discord.ui.Select):
    def __init__(
        self,
        service: GlassfishServiceContract,
        servicos_config: Dict[str, Any],
        action_type: str,
        page: int = 0,
    ):
        self.service = service
        self.servicos_config = servicos_config
        self.action_type = action_type

        options = []
        page_start = page * OPTIONS_PER_PAGE
        services_on_page = list(servicos_config.items())[page_start:page_start + OPTIONS_PER_PAGE]
        for key, config in services_on_page:
            if config["status"] == "em uso":
                desc = f"Em uso por: {config['usuario']}"
                emoji = "🔴"
            else:
                desc = "Disponível"
                emoji = "🟢"

            options.append(
                discord.SelectOption(
                    label=f"{key}: {config['nome'][:40]}"[:100],
                    value=str(key)[:100],
                    description=desc[:100],
                    emoji=emoji
                )
            )

        super().__init__(
            placeholder="Selecione um serviço",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        servico_id = self.values[0]

        try:
            if self.action_type == "editar":
                await interaction.response.send_modal(
                    GlassfishEditModal(servico_id, self.servicos_config, self.service)
                )
            elif self.action_type == "remover":
                await interaction.response.defer(ephemeral=True, thinking=True)

                def remove_available_service(services):
                    service_info = services.get(servico_id)
                    if service_info is None:
                        return False, ("not_found", None)
                    current_info = dict(service_info)
                    if service_info.get("status") == "em uso":
                        return False, ("in_use", current_info)
                    del services[servico_id]
                    return True, ("removed", current_info)

                saved, result = await self.service.update_services(remove_available_service)
                if not saved:
                    await interaction.followup.send(
                        "Não foi possível salvar a remoção. Tente novamente.",
                        ephemeral=True,
                    )
                    return

                result_type, servico_info = result
                if result_type == "not_found":
                    await interaction.followup.send(
                        "Este serviço não está mais cadastrado.",
                        ephemeral=True,
                    )
                elif result_type == "in_use":
                    view = ConfirmRemoveView(servico_id, self.service)
                    await interaction.followup.send(
                        f"⚠️ **ATENÇÃO**: O serviço **{servico_info['nome']}** está atualmente em uso por **{servico_info['usuario']}**.\n\n"
                        f"Tem certeza que deseja remover este serviço?",
                        view=view,
                        ephemeral=True
                    )
                else:
                    glassfish_cog = interaction.client.get_cog("GlassfishCog")
                    if glassfish_cog:
                        await glassfish_cog.refresh_persistent_message()
                        logging.info(f"Mensagem persistente do Glassfish atualizada após remoção do serviço {servico_id}")

                    try:
                        channel = interaction.guild.get_channel(settings.LOGS_CHANNEL_ID)
                        if channel:
                            await channel.send(
                                f"🗑️ O serviço **{servico_info['nome']}** foi removido por <@{interaction.user.id}>"
                            )
                    except Exception as log_err:
                        logging.error(f"Erro ao enviar log de remoção: {str(log_err)}")

                    await interaction.followup.send(
                        f"✅ Serviço **{servico_info['nome']}** removido com sucesso!",
                        ephemeral=True
                    )

                    logging.info(f"Serviço {servico_id} ({servico_info['nome']}) removido por {interaction.user.name}")
        except Exception as e:
            logging.error(f"Erro ao processar seleção de serviço: {str(e)}")
            try:
                error_message = f"❌ Ocorreu um erro ao processar o serviço: {str(e)}"
                if interaction.response.is_done():
                    await interaction.followup.send(error_message, ephemeral=True)
                else:
                    await interaction.response.send_message(error_message, ephemeral=True)
            except Exception as final_err:
                logging.error(f"Erro fatal ao responder interação de seleção: {str(final_err)}")


class GlassfishSelectPageButton(discord.ui.Button):
    def __init__(self, source_view, page: int, label: str, custom_id: str):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, custom_id=custom_id)
        self.source_view = source_view
        self.page = page

    async def callback(self, interaction: discord.Interaction):
        view = GlassfishSelectView(
            self.source_view.service,
            self.source_view.servicos_config,
            self.source_view.action_type,
            self.page,
        )
        await interaction.response.edit_message(view=view)

class ConfirmRemoveView(discord.ui.View):
    def __init__(self, servico_id: str, service: GlassfishServiceContract):
        super().__init__(timeout=60)
        self.servico_id = servico_id
        self.service = service

    @discord.ui.button(label="Sim, remover mesmo em uso", style=discord.ButtonStyle.danger)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            def remove_service(services):
                service_info = services.pop(self.servico_id, None)
                if service_info is None:
                    return False, ("not_found", None)
                return True, ("removed", dict(service_info))

            saved, result = await self.service.update_services(remove_service)
            if not saved:
                await interaction.followup.send(
                    "Não foi possível salvar a remoção. Tente novamente.",
                    ephemeral=True,
                )
                return
            result_type, service_info = result
            if result_type == "not_found":
                await interaction.followup.send(
                    "Este serviço não está mais cadastrado.",
                    ephemeral=True,
                )
                return

            servico_nome = service_info["nome"]
            usuario = service_info["usuario"]

            glassfish_cog = interaction.client.get_cog("GlassfishCog")
            if glassfish_cog:
                await glassfish_cog.refresh_persistent_message()

            channel = interaction.guild.get_channel(settings.LOGS_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"⚠️ **ATENÇÃO**: O serviço **{servico_nome}** foi removido por <@{interaction.user.id}> "
                    f"enquanto estava em uso por **{usuario}**."
                )

            for item in self.children:
                item.disabled = True

            await interaction.message.edit(
                content=f"✅ Serviço **{servico_nome}** removido com sucesso!",
                view=self
            )
            await interaction.followup.send(
                f"Serviço **{servico_nome}** removido com sucesso.",
                ephemeral=True,
            )

            logging.info(f"Serviço {self.servico_id} ({servico_nome}) removido por {interaction.user.name} enquanto em uso por {usuario}")

        except Exception as e:
            logging.error(f"Erro ao remover serviço: {str(e)}")
            await interaction.followup.send(
                f"Ocorreu um erro ao remover o serviço: {str(e)}",
                ephemeral=True
            )

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            content="Operação cancelada!",
            view=self
        )
