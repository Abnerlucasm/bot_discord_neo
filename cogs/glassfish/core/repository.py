import asyncio
import json
import logging
import os
import tempfile
from typing import Any, Dict, Optional, Tuple

from .contracts import ServiceMutation


class GlassfishServiceRepository:
    def __init__(self, services_file: str = "services.json"):
        self.services_file = services_file
        self._services_lock = asyncio.Lock()

    def load_services(self) -> Dict[str, Any]:
        """Carrega os serviços do arquivo services.json"""
        try:
            with open(self.services_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logging.warning("Arquivo services.json não encontrado. Criando um novo.")
            return {}
        except json.JSONDecodeError as e:
            logging.error(f"Erro ao decodificar JSON do arquivo services.json: {str(e)}")
            return {}
        except Exception as e:
            logging.error(f"Erro ao carregar serviços: {str(e)}")
            return {}

    def save_services(self, services: Dict[str, Any]) -> bool:
        """Salva os serviços no arquivo services.json"""
        temporary_file = None
        try:
            directory = os.path.dirname(os.path.abspath(self.services_file))
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=directory,
                prefix=".services-",
                suffix=".tmp",
                delete=False,
            ) as file:
                temporary_file = file.name
                json.dump(services, file, indent=4, ensure_ascii=False)
                file.flush()
                os.fsync(file.fileno())

            os.replace(temporary_file, self.services_file)
            logging.info("Serviços salvos com sucesso em services.json")
            return True
        except Exception as e:
            logging.error(f"Erro ao salvar serviços: {str(e)}")
            if temporary_file and os.path.exists(temporary_file):
                try:
                    os.remove(temporary_file)
                except OSError as cleanup_error:
                    logging.error(f"Erro ao remover arquivo temporário: {cleanup_error}")
            return False

    async def update_services(
        self,
        update: ServiceMutation,
    ) -> Tuple[bool, Any]:
        """Atualiza o estado carregado e grava apenas quando houve alteração."""
        async with self._services_lock:
            services = self.load_services()
            should_save, result = update(services)
            if not should_save:
                return True, result
            return self.save_services(services), result

    async def update_service(
        self,
        service_id: str,
        update: ServiceMutation,
    ) -> Tuple[bool, Any, Optional[Dict[str, Any]]]:
        """Atualiza um serviço usando a versão mais recente do arquivo."""
        def update_services(services: Dict[str, Any]) -> Tuple[bool, Any]:
            service = services.get(service_id)
            if service is None:
                return False, ("not_found", None)

            should_save, result = update(service)
            return should_save, (result, service)

        saved, result = await self.update_services(update_services)
        update_result, service = result
        return saved, update_result, service
