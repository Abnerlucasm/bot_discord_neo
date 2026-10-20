import datetime
import logging
from math import ceil
from typing import Any, Dict, List, Optional

import discord

from ..core.contracts import GlassfishServiceContract
from ..core.permissions import roles_can_access_service, user_can_access_service
from .service_actions import ActionButtons

OPTIONS_PER_PAGE = 25


class ServiceDropdown(discord.ui.View):
    def __init__(
        self,
        user_roles: Optional[List[int]],
        services: Dict[str, Any],
        service: GlassfishServiceContract,
        show_all_services: bool = False,
        page: int = 0,
    ):
        super().__init__(timeout=None)
        self.user_roles = set(user_roles or [])
        self.services = services
        self.service = service
        self.show_all_services = show_all_services
        self.page = page

        visible_services = self._visible_services()
        page_count = max(1, ceil(len(visible_services) / OPTIONS_PER_PAGE))
        self.page = min(max(page, 0), page_count - 1)
        page_start = self.page * OPTIONS_PER_PAGE
        page_services = visible_services[page_start:page_start + OPTIONS_PER_PAGE]

        self.add_item(ServiceSelect(page_services, service))
        if page_count > 1:
            previous_page = ServicePageButton(self, self.page - 1, "Anterior", "glassfish:services:previous")
            next_page = ServicePageButton(self, self.page + 1, "Próxima", "glassfish:services:next")
            previous_page.disabled = self.page == 0
            next_page.disabled = self.page == page_count - 1
            self.add_item(previous_page)
            self.add_item(next_page)

    def _visible_services(self):
        if self.show_all_services:
            return list(self.services.items())

        return [
            (service_id, config)
            for service_id, config in self.services.items()
            if roles_can_access_service(self.user_roles, config)
        ]


class ServiceSelect(discord.ui.Select):
    def __init__(self, services: List[tuple], service: GlassfishServiceContract):
        self.service = service
        options = []
        for service_id, config in services:
            if config.get("status") == "em uso":
                description = f"Em uso por: {config.get('usuario') or 'usuário desconhecido'}"
                emoji = "🔴"
            else:
                description = "Disponível"
                emoji = "🟢"

            options.append(
                discord.SelectOption(
                    label=(config.get("nome") or service_id)[:100],
                    value=str(service_id)[:100],
                    description=description[:100],
                    emoji=emoji,
                )
            )

        if not options:
            options.append(discord.SelectOption(label="Sem serviços disponíveis", value="none"))

        super().__init__(
            placeholder="Selecione um serviço...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        service_id = self.values[0]
        if service_id == "none":
            await interaction.response.send_message("Não há serviços disponíveis para você.", ephemeral=True)
            return

        if interaction.guild is None:
            await interaction.response.send_message("Este menu só pode ser usado no servidor.", ephemeral=True)
            return

        config = self.service.load_services().get(service_id)
        if not config:
            await interaction.response.send_message(
                "Este serviço não está mais cadastrado.",
                ephemeral=True,
            )
            return

        if not user_can_access_service(interaction.user, config):
            logging.warning(
                "Usuário %s (ID: %s) tentou acessar o serviço %s sem permissão",
                interaction.user.name,
                interaction.user.id,
                service_id,
            )
            await interaction.response.send_message(
                "Você não tem permissão para acessar este serviço.",
                ephemeral=True,
            )
            return

        if config.get("status") == "em uso":
            status_emoji = "🔴"
            usuario_atual = f" (Em uso por: {config.get('usuario') or 'usuário desconhecido'})"
            usage_data = config.get("usage_data", {})
            timestamp = usage_data.get("timestamp")
            if timestamp:
                try:
                    started_at = datetime.datetime.fromisoformat(timestamp)
                    elapsed_hours = (datetime.datetime.now() - started_at).total_seconds() / 3600
                    usuario_atual = f" (Em uso por: {config.get('usuario')} há {int(elapsed_hours)} horas)"
                except (TypeError, ValueError):
                    logging.warning("Data de início inválida para o serviço %s", service_id)
        else:
            status_emoji = "🟢"
            usuario_atual = ""

        view = ActionButtons(service_id, self.service)
        await interaction.response.send_message(
            f"{status_emoji} Você selecionou o serviço **{config['nome']}**. "
            f"Status atual: **{config['status']}**{usuario_atual}. Escolha uma ação:",
            view=view,
            ephemeral=True,
        )


class ServicePageButton(discord.ui.Button):
    def __init__(self, source_view, page: int, label: str, custom_id: str):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, custom_id=custom_id)
        self.source_view = source_view
        self.page = page

    async def callback(self, interaction: discord.Interaction):
        view = ServiceDropdown(
            list(self.source_view.user_roles),
            self.source_view.service.load_services(),
            self.source_view.service,
            show_all_services=self.source_view.show_all_services,
            page=self.page,
        )
        await interaction.response.edit_message(view=view)
