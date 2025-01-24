import logging
from platform import system
from dotenv import load_dotenv, find_dotenv
import json
import os


MAIN_LOGGER_NAME = "main_logger"

logger = logging.getLogger(MAIN_LOGGER_NAME)

# Função auxiliar para converter strings para booleanos
def str_to_bool(value: str) -> bool:
    return value.lower() in ('true', '1', 't')

# Função para carregar configurações de conexão a partir de JSON
def load_json_config(env_var: str, default: dict) -> dict:
    try:
        config = json.loads(os.getenv(env_var, json.dumps(default)))
        return config
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON para {env_var}: {e}")
        return default

def load_json_file(file_path: str, default: dict) -> dict:
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
        return config
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Erro ao carregar JSON de {file_path}: {e}")
        return default

# Inicializar mensagens de aviso
_messages = []

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

ENV_LOC = find_dotenv()

SYSTEM = system()

# //////////////////////////////////////////// 
# DEBUG
# //////////////////////////////////////////// 

DEBUG = str_to_bool(os.getenv("DEBUG", "False"))

# //////////////////////////////////////////// 
# Log Config:
# //////////////////////////////////////////// 

_DEFAULT_LOG_LEVEL = 'INFO'
if DEBUG:
    _DEFAULT_LOG_LEVEL = 'DEBUG'
LOG_LEVEL = logging._nameToLevel.get(
    os.getenv("LOG_LEVEL", _DEFAULT_LOG_LEVEL)
)

# ////////////////////////////////////////////
# Configuração do Banco de Dados:
# ////////////////////////////////////////////

# Configurações de leitura do banco de dados de produção
_DEFAULT_DB_URI = 'sqlite:///db.sqlite3'
DB_URI = os.getenv("DB_URI", _DEFAULT_DB_URI)

# ////////////////////////////////////////////
# Configuração de Apps:
# ////////////////////////////////////////////

# Caminho do arquivo JSON de configuração de aplicativos
APP_NAMES_FILE = os.getenv("APP_NAMES_FILE", "config/app_names.json")
APP_NAMES = load_json_file(APP_NAMES_FILE, {"APP_NAMES": []})["APP_NAMES"]

# ////////////////////////////////////////////
# Configuração de Email:
# ////////////////////////////////////////////

EMAIL_HOST = os.getenv("EMAIL_HOST", 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL = os.getenv("EMAIL", '')
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", '')

# Avisos sobre configurações críticas
if DEBUG:
    _messages.append('RODANDO EM DEBUG')

# Exibir mensagens de aviso
if _messages:
    for msg in _messages:
        logger.warning(f'SETTINGS WARNING: {msg}')
