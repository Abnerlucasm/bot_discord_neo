import json
import logging
import os
from copy import deepcopy
from typing import Any, Dict

CONFIG_FILE = "config.json"

DEVELOPMENT_MODE = False

DEFAULT_CARGO_TI_ID = 994300483348996176
DEFAULT_LOGS_CHANNEL_ID = 994341371634782279
DEFAULT_PERSISTENT_CHANNEL_ID = 994299965323091968

if DEVELOPMENT_MODE:
    DEFAULT_TEMPO_MAXIMO_USO = 1
    DEFAULT_VERIFICAR_INTERVALO = 1
    DEFAULT_LEMBRETE_INTERVALO = 1
    DEFAULT_MAX_EXTENSOES = 2
else:
    DEFAULT_TEMPO_MAXIMO_USO = 24
    DEFAULT_VERIFICAR_INTERVALO = 15
    DEFAULT_LEMBRETE_INTERVALO = 2
    DEFAULT_MAX_EXTENSOES = 3

try:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    CARGO_TI_ID = config["cargos"]["ti_id"]
    LOGS_CHANNEL_ID = config["canais"]["logs_id"]
    PERSISTENT_CHANNEL_ID = config["canais"]["persistent_id"]

    TEMPO_MAXIMO_USO = config["timeout"]["tempo_maximo_uso"]
    VERIFICAR_INTERVALO = config["timeout"]["verificar_intervalo"]
    LEMBRETE_INTERVALO = config["timeout"]["lembrete_intervalo"]
    MAX_EXTENSOES = config["timeout"].get("max_extensoes", DEFAULT_MAX_EXTENSOES)

    logging.info(f"Configurações carregadas com sucesso do arquivo {CONFIG_FILE}")
except Exception as e:

    logging.error(f"Erro ao carregar configurações do arquivo {CONFIG_FILE}: {str(e)}")
    logging.warning("Usando valores padrão para as configurações")

    CARGO_TI_ID = DEFAULT_CARGO_TI_ID
    LOGS_CHANNEL_ID = DEFAULT_LOGS_CHANNEL_ID
    PERSISTENT_CHANNEL_ID = DEFAULT_PERSISTENT_CHANNEL_ID
    TEMPO_MAXIMO_USO = DEFAULT_TEMPO_MAXIMO_USO
    VERIFICAR_INTERVALO = DEFAULT_VERIFICAR_INTERVALO
    LEMBRETE_INTERVALO = DEFAULT_LEMBRETE_INTERVALO
    MAX_EXTENSOES = DEFAULT_MAX_EXTENSOES

DEFAULT_CONFIG = {
    "cargos": {
        "ti_id": DEFAULT_CARGO_TI_ID
    },
    "canais": {
        "logs_id": DEFAULT_LOGS_CHANNEL_ID,
        "persistent_id": DEFAULT_PERSISTENT_CHANNEL_ID
    },
    "timeout": {
        "tempo_maximo_uso": DEFAULT_TEMPO_MAXIMO_USO,
        "verificar_intervalo": DEFAULT_VERIFICAR_INTERVALO,
        "lembrete_intervalo": DEFAULT_LEMBRETE_INTERVALO,
        "max_extensoes": DEFAULT_MAX_EXTENSOES
    }
}

def load_config() -> Dict[str, Any]:
    """Carrega as configurações do arquivo config.json"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"Erro ao carregar configurações: {str(e)}")

    return deepcopy(DEFAULT_CONFIG)

def save_config(config: Dict[str, Any]) -> bool:
    """Salva as configurações no arquivo config.json"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logging.info(f"Configurações salvas com sucesso em {CONFIG_FILE}")
        return True
    except Exception as e:
        logging.error(f"Erro ao salvar configurações: {str(e)}")
        return False

def reload_config() -> Dict[str, Any]:
    """Recarrega as configurações globais do arquivo"""
    global CARGO_TI_ID, LOGS_CHANNEL_ID, PERSISTENT_CHANNEL_ID
    global TEMPO_MAXIMO_USO, VERIFICAR_INTERVALO, LEMBRETE_INTERVALO, MAX_EXTENSOES

    try:
        config = load_config()

        CARGO_TI_ID = config["cargos"]["ti_id"]
        LOGS_CHANNEL_ID = config["canais"]["logs_id"]
        PERSISTENT_CHANNEL_ID = config["canais"]["persistent_id"]
        TEMPO_MAXIMO_USO = config["timeout"]["tempo_maximo_uso"]
        VERIFICAR_INTERVALO = config["timeout"]["verificar_intervalo"]
        LEMBRETE_INTERVALO = config["timeout"]["lembrete_intervalo"]
        MAX_EXTENSOES = config["timeout"].get("max_extensoes", DEFAULT_MAX_EXTENSOES)

        logging.info("Configurações globais recarregadas com sucesso")
        return config
    except Exception as e:
        logging.error(f"Erro ao recarregar configurações: {str(e)}")
        return deepcopy(DEFAULT_CONFIG)
