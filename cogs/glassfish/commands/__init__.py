from .admin import GlassfishAdminCommands
from .development import GlassfishDevelopmentCommands
from .user import GlassfishUserCommands


class GlassfishCommands(
    GlassfishUserCommands,
    GlassfishAdminCommands,
    GlassfishDevelopmentCommands,
):
    pass
