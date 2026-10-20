from ..core.contracts import GlassfishServiceContract
from ..core.permissions import user_has_ti_role


class GlassfishCommandBase:
    def __init__(self, bot, service: GlassfishServiceContract):
        self.bot = bot
        self.service = service

    def _tem_permissao_ti(self, user) -> bool:
        return user_has_ti_role(user)
