import os
import json
import logging
from typing import Dict, Any

# Configurações do arquivo JSON
CONFIG_FILE = "config.json"

# Modo de desenvolvimento (para testes)
DEVELOPMENT_MODE = False  # Mude para True para ativar o modo de desenvolvimento

# Valores padrão caso não consiga carregar do arquivo
DEFAULT_CARGO_TI_ID = 994300483348996176
DEFAULT_LOGS_CHANNEL_ID = 994341371634782279
DEFAULT_PERSISTENT_CHANNEL_ID = 994299965323091968

# Configurações de timeout para desenvolvimento vs produção
if DEVELOPMENT_MODE:
    DEFAULT_TEMPO_MAXIMO_USO = 2  # 1 hora para testes
    DEFAULT_VERIFICAR_INTERVALO = 1  # 1 minuto para testes
    DEFAULT_LEMBRETE_INTERVALO = 1  # 1 hora para testes
    DEFAULT_MAX_EXTENSOES = 2  # 2 extensões para testes
else:
    DEFAULT_TEMPO_MAXIMO_USO = 24  # 24 horas em produção
    DEFAULT_VERIFICAR_INTERVALO = 15  # 15 minutos em produção
    DEFAULT_LEMBRETE_INTERVALO = 2  # 2 horas em produção
    DEFAULT_MAX_EXTENSOES = 3  # 3 extensões em produção

# Carrega as configurações do arquivo JSON
try:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    # Carrega as configurações de cargos e canais
    CARGO_TI_ID = config["cargos"]["ti_id"]
    LOGS_CHANNEL_ID = config["canais"]["logs_id"]
    PERSISTENT_CHANNEL_ID = config["canais"]["persistent_id"]
    
    # Carrega as configurações de timeout
    TEMPO_MAXIMO_USO = config["timeout"]["tempo_maximo_uso"]
    VERIFICAR_INTERVALO = config["timeout"]["verificar_intervalo"]
    LEMBRETE_INTERVALO = config["timeout"]["lembrete_intervalo"]
    MAX_EXTENSOES = config["timeout"].get("max_extensoes", DEFAULT_MAX_EXTENSOES)
    
    logging.info(f"Configurações carregadas com sucesso do arquivo {CONFIG_FILE}")
except Exception as e:
    # Valores padrão caso não consiga carregar do arquivo
    logging.error(f"Erro ao carregar configurações do arquivo {CONFIG_FILE}: {str(e)}")
    logging.warning("Usando valores padrão para as configurações")
    
    CARGO_TI_ID = DEFAULT_CARGO_TI_ID
    LOGS_CHANNEL_ID = DEFAULT_LOGS_CHANNEL_ID
    PERSISTENT_CHANNEL_ID = DEFAULT_PERSISTENT_CHANNEL_ID
    TEMPO_MAXIMO_USO = DEFAULT_TEMPO_MAXIMO_USO
    VERIFICAR_INTERVALO = DEFAULT_VERIFICAR_INTERVALO
    LEMBRETE_INTERVALO = DEFAULT_LEMBRETE_INTERVALO
    MAX_EXTENSOES = DEFAULT_MAX_EXTENSOES

# Configurações padrão completas
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
    
    return DEFAULT_CONFIG.copy()

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
        
        # Atualiza as variáveis globais
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
        return DEFAULT_CONFIG.copy() 