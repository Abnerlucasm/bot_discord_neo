from .agendamentos import (
    create_agendamento_help,
    create_atualizacao_help,
    create_beta99_help,
)
from .geral import create_sobre_help
from .glassfish_admin import (
    create_adicionar_glassfish_help,
    create_configurar_timeout_glassfish_help,
    create_editar_glassfish_help,
    create_liberar_todos_glassfish_help,
    create_recarregar_config_glassfish_help,
    create_relatorio_glassfish_help,
    create_remover_glassfish_help,
    create_verificacao_forcada_glassfish_help,
)
from .glassfish_development import (
    create_modo_desenvolvimento_glassfish_help,
    create_simular_tempo_glassfish_help,
    create_status_servico_glassfish_help,
    create_testar_envio_lembrete_glassfish_help,
    create_testar_lembrete_glassfish_help,
)
from .glassfish_user import create_glassfish_help, create_obter_timeout_glassfish_help
from .overview import create_general_help

HELP_TOPICS = {
    "glassfish": create_glassfish_help,
    "agendamento": create_agendamento_help,
    "atualizacao": create_atualizacao_help,
    "beta99": create_beta99_help,
    "sobre": create_sobre_help,
    "recarregar_config_glassfish": create_recarregar_config_glassfish_help,
    "verificacao_forcada_glassfish": create_verificacao_forcada_glassfish_help,
    "configurar_timeout_glassfish": create_configurar_timeout_glassfish_help,
    "obter_timeout_glassfish": create_obter_timeout_glassfish_help,
    "liberar_todos_glassfish": create_liberar_todos_glassfish_help,
    "testar_lembrete_glassfish": create_testar_lembrete_glassfish_help,
    "modo_desenvolvimento_glassfish": create_modo_desenvolvimento_glassfish_help,
    "simular_tempo_glassfish": create_simular_tempo_glassfish_help,
    "status_servico_glassfish": create_status_servico_glassfish_help,
    "testar_envio_lembrete_glassfish": create_testar_envio_lembrete_glassfish_help,
    "relatorio_glassfish": create_relatorio_glassfish_help,
    "adicionar_glassfish": create_adicionar_glassfish_help,
    "editar_glassfish": create_editar_glassfish_help,
    "remover_glassfish": create_remover_glassfish_help,
}
