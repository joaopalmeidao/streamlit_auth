import logging

from streamlit_auth.config import settings 


class CustomFormatter(logging.Formatter):
    '''Classe para customizar o Logger'''

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "[%(asctime)s] [%(name)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        """_summary_

        Args:
            record (_type_): _description_

        Returns:
            _type_: _description_
        """
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

logger = logging.getLogger(settings.MAIN_LOGGER_NAME)

console_handler = logging.StreamHandler()
console_handler.setLevel(settings.LOG_LEVEL)
console_handler.setFormatter(CustomFormatter())

# Evita que o logger propague mensagens para o logger pai (root)
logger.propagate = False

logger.setLevel(settings.LOG_LEVEL)
logger.addHandler(console_handler)
