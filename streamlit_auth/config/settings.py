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


# Inicializar mensagens de aviso
_messages = []

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

ENV_LOC = find_dotenv()

SYSTEM = system()

# //////////////////////////////////////////// 
# Log Config:
# //////////////////////////////////////////// 

LOG_LEVEL = logging._nameToLevel.get(
    os.getenv("LOG_LEVEL", "DEBUG")
)

# ////////////////////////////////////////////
# Configuração do Banco de Dados:
# ////////////////////////////////////////////

# Configurações de leitura do banco de dados de produção
DB_URI_DATA_DEFAULT = 'sqlite:///db.sqlite3'
DB_URI = os.getenv("DB_URI", DB_URI_DATA_DEFAULT)

# //////////////////////////////////////////// 
# DEBUG
# //////////////////////////////////////////// 

DEBUG = str_to_bool(os.getenv("DEBUG", "False"))

# ////////////////////////////////////////////
# Configuração de Autenticação:
# ////////////////////////////////////////////

APP_NAMES = json.loads(os.getenv("APP_NAMES", '["Test1", "Test2", "Test3"]'))

# ////////////////////////////////////////////
# Configuração de Email:
# ////////////////////////////////////////////

EMAIL_URI_DATA_DEFAULT = {
    "HOST": "",
    "PORT": 587,
    "USERNAME": "",
    "EMAIL": "",
    "PASSWORD": ""
}
EMAIL_URI_DATA = load_json_config("EMAIL_URI_DATA", EMAIL_URI_DATA_DEFAULT)


# Avisos sobre configurações críticas
if DEBUG:
    _messages.append('RODANDO EM DEBUG')

# Exibir mensagens de aviso
if _messages:
    for msg in _messages:
        logger.warning(f'WARNING: {msg}')
