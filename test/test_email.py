
from streamlit_auth.core import SendMail


with SendMail() as mail:
        
    mail.subtype = 'plain'

    mail.assunto = f'Redefinição de'

    mail.destinatarios = [
        'jp080496@gmail.com',
    ]

    message = f"""

    Você solicitou a redefinição de Clique no link abaixo para continuar:

    Este link é válido por 1 hora. Se você não solicitou isso, ignore este e-mail.

    """

    mail.enviar_email(
        message,
    )