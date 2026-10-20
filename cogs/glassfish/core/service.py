import logging
from typing import Dict, Any, Optional, Tuple

import discord

from ..ui.service_actions import CheckView
from ..ui.service_select import ServiceDropdown
from . import config as settings
from .contracts import ServiceMutation
from .monitoring import GlassfishUsageMonitor
from .repository import GlassfishServiceRepository


class GlassfishService:
    def __init__(self, bot):
        self.bot = bot
        self.tempo_maximo_uso = settings.TEMPO_MAXIMO_USO
        self.verificar_intervalo = settings.VERIFICAR_INTERVALO
        self.lembrete_intervalo = settings.LEMBRETE_INTERVALO
        self.max_extensoes = settings.MAX_EXTENSOES
        self.repository = GlassfishServiceRepository()
        self.services_file = self.repository.services_file
        self.persistent_message = None
        self.usage_monitor = GlassfishUsageMonitor()

        self._load_config_from_file()

    def register_persistent_views(self):
        for service_id, config in self.load_services().items():
            if config.get("status") == "em uso":
                self.bot.add_view(CheckView(service_id, self))

    def _load_config_from_file(self):
        """Carrega as configurações do arquivo config.json"""
        try:
            config = settings.load_config()

            if "timeout" in config:
                self.tempo_maximo_uso = config["timeout"].get("tempo_maximo_uso", self.tempo_maximo_uso)
                self.verificar_intervalo = config["timeout"].get("verificar_intervalo", self.verificar_intervalo)
                self.lembrete_intervalo = config["timeout"].get("lembrete_intervalo", self.lembrete_intervalo)
                self.max_extensoes = config["timeout"].get("max_extensoes", self.max_extensoes)

            logging.info("Configurações de serviço carregadas do arquivo config.json")
        except Exception as e:
            logging.error(f"Erro ao carregar configurações de serviço: {str(e)}")
            logging.info("Usando valores padrão para as configurações de serviço")

    def load_services(self) -> Dict[str, Any]:
        return self.repository.load_services()

    def save_services(self, services: Dict[str, Any]) -> bool:
        return self.repository.save_services(services)

    async def update_services(self, update: ServiceMutation) -> Tuple[bool, Any]:
        return await self.repository.update_services(update)

    async def update_service(
        self,
        service_id: str,
        update: ServiceMutation,
    ) -> Tuple[bool, Any, Optional[Dict[str, Any]]]:
        return await self.repository.update_service(service_id, update)

    def reload_config(self):
        """Recarrega as configurações do arquivo config.json"""
        try:
            config = settings.reload_config()
            self._load_config_from_file()
            return config
        except Exception as e:
            logging.error(f"Erro ao recarregar configurações: {str(e)}")
            return None

    def update_config(self, new_config: Dict[str, Any]):
        """Atualiza as configurações de timeout"""
        try:
            config = settings.load_config()
            for section, values in new_config.items():
                if isinstance(values, dict) and isinstance(config.get(section), dict):
                    config[section].update(values)
                else:
                    config[section] = values

            if settings.save_config(config):
                self._load_config_from_file()
                return True
            return False
        except Exception as e:
            logging.error(f"Erro ao atualizar configurações: {str(e)}")
            return False

    def get_config(self) -> Dict[str, Any]:
        """Retorna as configurações atuais"""
        return {
            "timeout": {
                "tempo_maximo_uso": self.tempo_maximo_uso,
                "verificar_intervalo": self.verificar_intervalo,
                "lembrete_intervalo": self.lembrete_intervalo,
                "max_extensoes": self.max_extensoes
            }
        }
    async def check_services(self) -> None:
        await self.usage_monitor.check_services(self)

    async def refresh_persistent_message(self):
        """Atualiza a mensagem persistente se existir"""
        try:
            channel = self.bot.get_channel(settings.PERSISTENT_CHANNEL_ID)
            if not channel:
                logging.error(f"Canal {settings.PERSISTENT_CHANNEL_ID} não encontrado")
                return False

            if self.persistent_message is None:
                return await self.setup_persistent_message()

            services = self.load_services()
            view = ServiceDropdown(None, services, self, show_all_services=True)
            await self.persistent_message.edit(view=view)
            logging.info("Mensagem persistente do Glassfish atualizada")
            return True
        except discord.NotFound:
            logging.warning("Mensagem persistente não encontrada, será recriada")
            self.persistent_message = None
            return await self.setup_persistent_message()
        except Exception as e:
            logging.error(f"Erro ao atualizar mensagem persistente: {str(e)}")
            return False

    async def setup_persistent_message(self):
        """Configura ou atualiza a mensagem persistente no canal específico"""
        try:
            channel = self.bot.get_channel(settings.PERSISTENT_CHANNEL_ID)
            if not channel:
                logging.error(f"Canal {settings.PERSISTENT_CHANNEL_ID} não encontrado")
                return False

            async for message in channel.history(limit=100):
                if message.author == self.bot.user and "**Serviços Glassfish**" in message.content:
                    self.persistent_message = message
                    break

            servicos_config = self.load_services()
            view = ServiceDropdown(None, servicos_config, self, show_all_services=True)
            message_content = (
                "**Serviços Glassfish**\n"
                "Selecione um serviço abaixo para gerenciá-lo.\n"
                "🟢 = Disponível | 🔴 = Em uso\n"
                f"⚠️ Serviços em uso por mais de {self.tempo_maximo_uso} horas sem confirmação serão liberados automaticamente."
            )

            if self.persistent_message:
                await self.persistent_message.edit(content=message_content, view=view)
            else:
                self.persistent_message = await channel.send(message_content, view=view)

            logging.info("Mensagem persistente do Glassfish configurada/atualizada")
            return True
        except Exception as e:
            logging.error(f"Erro ao configurar mensagem persistente: {str(e)}")
            return False

