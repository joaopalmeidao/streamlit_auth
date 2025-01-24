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
DB_URI = load_json_config("DB_URI", DB_URI_DATA_DEFAULT)

# //////////////////////////////////////////// 
# DEBUG
# //////////////////////////////////////////// 

DEBUG = str_to_bool(os.getenv("DEBUG", "False"))

# ////////////////////////////////////////////
# Configuração de Autenticação:
# ////////////////////////////////////////////

APP_NAMES = json.loads(os.getenv("APP_NAMES", '["Test1", "Test2", "Test3"]'))

# Secret Key para autenticação
DEFAULT_SECRET_SERVER = '3a5f756fec09f3edf8f1feb97d7d11329be019c290b4fd4704f1ba24805043f4'
SECRET_SERVER = os.getenv('SECRET_SERVER', DEFAULT_SECRET_SERVER)

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
if SECRET_SERVER == DEFAULT_SECRET_SERVER:
    _messages.append('TROCAR SECRET_SERVER para uma chave segura e única.')
if DEBUG:
    _messages.append('RODANDO EM DEBUG')

# Exibir mensagens de aviso
if _messages:
    for msg in _messages:
        logger.warning(f'WARNING: {msg}')
