import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
import logging

from streamlit_auth.config import settings

logger = logging.getLogger(settings.MAIN_LOGGER_NAME)


class SendMail:
    subtype = 'html'

    assunto: str = ''
    destinatarios: list = []
    copia: list = []
    copia_oculta: list = []

    server = None
    email_msg = None

    def __init__(self,
        host=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        email=settings.EMAIL,
        password=settings.EMAIL_PASSWORD
        ):
        self.host = host
        self.port = port
        self.email = email
        self.password = password

    def connect(self):
        """Conecta ao servidor de e-mail."""
        if not self.server:
            logger.debug('Conectando ao servidor: %s', self.host)
            if self.port == 587:
                self.server = smtplib.SMTP(host=self.host, port=self.port)
                self.server.ehlo()
                self.server.starttls()
            elif self.port == 465:
                self.server = smtplib.SMTP_SSL(host=self.host, port=self.port)
            else:
                raise Exception(f'Invalid port: {self.port}')
            self.server.login(self.email, self.password)

    def disconnect(self):
        """Desconecta do servidor de e-mail."""
        if self.server:
            logger.debug('Desconectando do servidor: %s', self.host)
            self.server.quit()
            self.server = None
            self.email_msg = None

    def __enter__(self):
        """Gerenciador de contexto: conecta automaticamente."""
        self.connect()
        return self

    def __exit__(self, *args, **kwargs):
        """Gerenciador de contexto: desconecta automaticamente."""
        self.disconnect()

    def _load_message(self, mensagem):
        """Carrega a mensagem de e-mail."""
        destina = ','.join(self.destinatarios)
        copia = ','.join(self.copia)
        copia_oculta = ','.join(self.copia_oculta)

        self.email_msg = MIMEMultipart('related')
        self.email_msg['From'] = self.email
        self.email_msg['To'] = destina
        self.email_msg['Cc'] = copia
        self.email_msg['Cco'] = copia_oculta
        self.email_msg['Subject'] = self.assunto
        self.email_msg.attach(MIMEText(mensagem, self.subtype))

    def _anexar_arquivos(self, arquivos):
        """Anexa os arquivos."""
        for key, val in arquivos.items():
            att = MIMEBase('application', 'octet-stream')
            att.set_payload(val.getvalue())
            encoders.encode_base64(att)
            att.add_header('Content-Disposition', f'attachment; filename={key}')
            self.email_msg.attach(att)
            logger.info(f'{key} Anexado!')

    def _anexar_imagens(self, imagens):
        """Anexa imagens."""
        for key, val in imagens.items():
            if val:
                img_mime = MIMEImage(val.getvalue(), name=f'{key}.png')
                img_mime.add_header('Content-ID', f'<{key}>')
                img_mime.add_header('Content-Disposition', 'inline', filename=f'{key}.png')
                self.email_msg.attach(img_mime)
                logger.info(f'{key} Anexado!')

    def enviar_email(self, message, arquivos=None, imagens=None):
        """Envia o e-mail."""
        if not self.server:
            logger.error("Servidor de e-mail não conectado. Use 'connect()' ou o gerenciador de contexto.")
            raise Exception("Servidor de e-mail não conectado.")

        arquivos = arquivos or {}
        imagens = imagens or {}

        logger.info('Enviando E-mail para: %s', self.destinatarios + self.copia + self.copia_oculta)
        self._load_message(message)
        self._anexar_arquivos(arquivos)
        self._anexar_imagens(imagens)

        recipients = self.destinatarios + self.copia + self.copia_oculta
        self.server.sendmail(self.email_msg['From'], recipients, self.email_msg.as_string())
        logger.info('E-mail enviado para %s!', recipients)
