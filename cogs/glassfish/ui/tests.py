import datetime
import logging
from math import ceil
from typing import Any, Dict, List, Tuple

import discord

from ..core.contracts import GlassfishServiceContract

OPTIONS_PER_PAGE = 25


def _get_services_in_use(services: Dict[str, Any]) -> List[Tuple[str, Any]]:
    return [
        (service_id, config)
        for service_id, config in services.items()
        if config.get("status") == "em uso"
    ]


class TestarLembreteView(discord.ui.View):
    def __init__(
        self,
        service: GlassfishServiceContract,
        servicos_config: Dict[str, Any],
        simular_tempo: int,
        page: int = 0,
    ):
        super().__init__(timeout=180)
        self.service = service
        self.servicos_config = servicos_config
        self.simular_tempo = simular_tempo

        in_use_services = _get_services_in_use(self.servicos_config)
        page_count = max(1, ceil(len(in_use_services) / OPTIONS_PER_PAGE))
        self.page = min(max(page, 0), page_count - 1)
        self.add_item(TestarLembreteSelect(service, servicos_config, simular_tempo, self.page))

        if page_count > 1:
            previous_page = TestarLembretePageButton(self, self.page - 1, "Anterior")
            next_page = TestarLembretePageButton(self, self.page + 1, "Próxima")
            previous_page.disabled = self.page == 0
            next_page.disabled = self.page == page_count - 1
            self.add_item(previous_page)
            self.add_item(next_page)

class TestarLembreteSelect(discord.ui.Select):
    def __init__(
        self,
        service: GlassfishServiceContract,
        servicos_config: Dict[str, Any],
        simular_tempo: int,
        page: int = 0,
    ):
        self.service = service
        self.simular_tempo = simular_tempo

        in_use_services = _get_services_in_use(servicos_config)
        page_start = page * OPTIONS_PER_PAGE
        services_on_page = in_use_services[page_start:page_start + OPTIONS_PER_PAGE]
        options = [
            discord.SelectOption(
                label=f"{service_id}: {config.get('nome', service_id)}"[:100],
                value=service_id,
                description=f"Em uso por: {config.get('usuario') or 'usuário desconhecido'}"[:100],
            )
            for service_id, config in services_on_page
        ]

        if not options:
            options.append(discord.SelectOption(label="Nenhum serviço em uso", value="none"))

        super().__init__(
            placeholder="Selecione um serviço para testar",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message(
                "Não há serviços em uso para testar.",
                ephemeral=True,
            )
            return

        service_id = self.values[0]
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            simulated_start = datetime.datetime.now() - datetime.timedelta(hours=self.simular_tempo)

            def simulate_usage(config):
                if config.get("status") != "em uso":
                    return False, ("not_in_use", dict(config))

                usage_data = dict(config.get("usage_data", {}))
                usage_data.update({
                    "usuario": config["usuario"],
                    "user_id": usage_data.get("user_id", interaction.user.id),
                    "timestamp": simulated_start.isoformat(),
                    "last_check": None,
                    "last_reminder": None,
                    "extension_count": 0,
                })
                config["usage_data"] = usage_data
                return True, ("simulated", dict(config))

            saved, result, config = await self.service.update_service(service_id, simulate_usage)
            if result == "not_found" or not config:
                await interaction.followup.send(
                    "Este serviço não está mais cadastrado.",
                    ephemeral=True,
                )
                return
            if not saved:
                await interaction.followup.send(
                    "Não foi possível salvar a simulação. Tente novamente.",
                    ephemeral=True,
                )
                return

            result_type, config = result
            if result_type == "not_in_use":
                await interaction.followup.send(
                    f"O serviço '{service_id}' não está em uso.",
                    ephemeral=True,
                )
                return

            await interaction.followup.send(
                f"✅ Tempo simulado para o serviço **{config['nome']}**.\n" +
                f"Simulando uso de {self.simular_tempo} horas atrás.",
                ephemeral=True
            )

        except Exception as e:
            logging.exception("Erro ao simular tempo para o serviço %s", service_id)
            await interaction.followup.send(
                f"❌ Ocorreu um erro ao simular o tempo: {str(e)}",
                ephemeral=True
            )


class TestarLembretePageButton(discord.ui.Button):
    def __init__(self, source_view: TestarLembreteView, page: int, label: str):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.source_view = source_view
        self.page = page

    async def callback(self, interaction: discord.Interaction):
        view = TestarLembreteView(
            self.source_view.service,
            self.source_view.servicos_config,
            self.source_view.simular_tempo,
            self.page,
        )
        await interaction.response.edit_message(view=view)
