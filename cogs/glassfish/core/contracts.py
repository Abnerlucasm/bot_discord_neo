from typing import Any, Callable, Dict, Optional, Protocol, Tuple


ServiceMutation = Callable[[Dict[str, Any]], Tuple[bool, Any]]


class GlassfishServiceContract(Protocol):
    bot: Any
    tempo_maximo_uso: int
    verificar_intervalo: int
    lembrete_intervalo: int
    max_extensoes: int

    def load_services(self) -> Dict[str, Any]: ...

    def get_config(self) -> Dict[str, Any]: ...

    def reload_config(self) -> Optional[Dict[str, Any]]: ...

    def update_config(self, new_config: Dict[str, Any]) -> bool: ...

    async def check_services(self) -> None: ...

    async def setup_persistent_message(self) -> bool: ...

    async def refresh_persistent_message(self) -> bool: ...

    async def update_services(self, update: ServiceMutation) -> Tuple[bool, Any]: ...

    async def update_service(
        self,
        service_id: str,
        update: ServiceMutation,
    ) -> Tuple[bool, Any, Optional[Dict[str, Any]]]: ...
