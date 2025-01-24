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
    

    def __init__(self, connection=settings.EMAIL_URI_DATA) -> None:
        """_summary_

        Args:
            connection (_type_, optional): _description_. Defaults to MailConnections.CONNECTIONS['MIS'].
        """
        self._connection = connection
        self.host = self._connection['HOST']
        self.port = self._connection['PORT']
        self.email = self._connection['EMAIL']
        self.senha = self._connection['PASSWORD']
        self.username = self._connection['USERNAME']

    def __connect__(self) -> smtplib.SMTP_SSL:
        """Conecta com o servidor do email

        Returns:
            smtplib.SMTP_SSL: _description_
        """
        logger.debug('Conectando ao servidor: %s' % (self._connection['HOST']))
        if self.port == 587:
            server = smtplib.SMTP(host=self.host,port=self.port)
            server.ehlo()
            server.starttls()
        elif self.port == 465:
            server = smtplib.SMTP_SSL(host=self.host,port=self.port)
        else: raise Exception('Invalid port: %d' % self.port)
        server.login(self.email,self.senha)
        return server

    def __exit__(self,server) -> None:
        """Fecha a conexao com o servidor do email

        Args:
            server (_type_): _description_
        """
        logger.debug('Desconectando do servidor: %s' % (self._connection['HOST']))
        server.quit()


    def carregar_mensagem(self,mensagem) -> MIMEMultipart:
        """Carrega a mensagem de email

        Args:
            mensagem (_type_): _description_

        Returns:
            MIMEMultipart: _description_
        """
        destina = ','.join(self.destinatarios)
        copia = ','.join(self.copia)
        copia_oculta = ','.join(self.copia_oculta)
        email_msg = MIMEMultipart('related')
        email_msg['From'] = self.email
        email_msg['To'] = destina
        email_msg['Cc'] = copia
        email_msg['Cco'] = copia_oculta
        email_msg['Subject'] = self.assunto
        email_msg.attach(MIMEText(mensagem,self.subtype))
        return email_msg

    def anexar_arquivos(self,email_msg,arquivos: dict) -> None:
        """Anexa os aquivos

        Args:
            email_msg (_type_): _description_
            caminho_arquivos (list): _description_
            nome_arquivos (list): _description_
        """
        for key,val in arquivos.items():
            
            att = MIMEBase('application','octet-stream')
            att.set_payload(val.getvalue())
            encoders.encode_base64(att)
            att.add_header('Content-Disposition', 'attachment; filename=%s' % (key))
            email_msg.attach(att)
            logger.info(f'{key} Anexado!')
            
    def anexar_imagens(self,email_msg, imagens: dict) -> None:
        for key,val in imagens.items():
            if val:
                img_mime = MIMEImage(val.getvalue(), name=f'{key}.png')
                img_mime.add_header('Content-ID', f'<{key}>')  # O CID é referenciado no HTML
                img_mime.add_header('Content-Disposition', 'inline', filename=f'{key}.png')  # Para garantir que seja embutido
                email_msg.attach(img_mime)
                logger.info(f'{key} Anexado!')

    def enviar_email(self,message,arquivos={}, imagens={}) -> None:
        """Faz o envio do email
        """
        logger.info('Enviando E-mail para: %s' % (self.destinatarios+self.copia+self.copia_oculta))
        server = self.__connect__()
        self.email_msg = self.carregar_mensagem(message)
        
        self.anexar_arquivos(self.email_msg,
                            arquivos
                            )
        self.anexar_imagens(self.email_msg,
                            imagens
                            )

        server.sendmail(self.email_msg['From'],self.destinatarios+self.copia,self.email_msg.as_string())
        logger.info('E-mail enviado para %s!' % (self.destinatarios+self.copia))

        self.__exit__(server)

