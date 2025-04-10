import logging

# Importa funções e classes dos módulos criados
from cogs.persistence import setup_persistence, get_instance_persistence, restore_views
from cogs.interaction_handler import setup_interaction_handler, handle_button_interactions

# Este arquivo serve apenas como ponto de entrada para manter compatibilidade com código existente
# Todas as implementações foram movidas para módulos específicos

__all__ = [
    'setup_persistence', 
    'get_instance_persistence', 
    'restore_views',
    'setup_interaction_handler', 
    'handle_button_interactions'
]

logging.info("Módulo utils.py carregado - usando implementações modulares") 