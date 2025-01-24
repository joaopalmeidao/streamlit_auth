# Streamlit Auth Library

Descrição

A Streamlit Auth Library é uma biblioteca que adiciona autenticação robusta e recursos de gerenciamento de usuários ao seu aplicativo Streamlit. Com suporte para autenticação de dois fatores (2FA), permissões e gerenciamento de sessões, ela é ideal para aplicativos que requerem segurança e controle de acesso.

[PyPI - streamlit-auth-mfa](https://pypi.org/project/streamlit-auth-mfa/)

## Telas Prontas

![Gerenciar Permissões](doc/imgs/gerenciar_perms.png)

![Gerenciar Usuários](doc/imgs/gerenciar_usuarios.png)

## Instalação

```bash
pip install streamlit-auth-mfa
```

## Configuração

A biblioteca utiliza variáveis de ambiente e arquivos de configuração para personalizar comportamentos. Certifique-se de configurar os arquivos necessários antes de usar a biblioteca.

.env
As variáveis de ambiente devem ser configuradas no arquivo .env:

```env
DEBUG=True
LOG_LEVEL=DEBUG

# Banco de Dados
DB_URI=sqlite:///db.sqlite3

# E-mail
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha

# Configuração de Apps
APP_NAMES_FILE=config/app_names.json
```

## Arquivos de Configuração

config/app_names.json
Defina os nomes dos aplicativos para os quais você gerencia permissões:

```json
{
    "APP_NAMES": ["App1", "App2", "App3"]
}
```

Recursos

- Autenticação
- Username e senha: Utiliza bcrypt para segurança.
- 2FA opcional: Adicione uma camada extra de segurança com TOTP.
- Gerenciamento de sessões: Rastreamento e controle de logins.
- Gerenciamento de Usuários e Permissões
- Gerenciar usuários: Adicione, edite ou remova usuários.
- Gerenciar permissões: Controle o acesso por aplicativo.
- Integração com E-mail
- Envio de e-mails transacionais, incluindo suporte para anexos e imagens embutidas.

## Exemplo de uso

Autenticação Simples

```python
from streamlit_auth.authentication import Authenticate

authenticator = Authenticate(
    secret_key='minha_chave_secreta',
    session_expiry_days=7,
    require_2fa=True
)

user_data = authenticator.login("Login")

if user_data['authentication_status']:
    st.success("Bem-vindo, {}!".format(user_data['name']))
    authenticator.logout("Sair")
else:
    st.error("Autenticação falhou. Verifique suas credenciais.")
```

### Gerenciamento

Use a função main_page_gerenciar para exibir a tela de permissões de usuários. Veja como implementar:

```python
from streamlit_auth.authentication import main_page_gerenciar

# Tela para gerenciar permissões e usuarios
main_page_gerenciar()
```

Execute o servidor normalmente no arquivo criado:

```bash
streamlit run <arquivo criado>.py
```

## Modelos de Banco de Dados

A biblioteca fornece modelos integrados para gerenciar usuários e sessões:

- TbUsuarioStreamlit - Gerenciamento de usuários.
- TbSessaoStreamlit - Rastreamento de sessões.
- TbPermissaoUsuariosStreamlit - Controle de permissões.

## Envio de E-mails

Com a classe SendMail, você pode enviar e-mails com suporte para anexos e imagens.

```python
from streamlit_auth.enviar_email import SendMail

with SendMail(
    host="smtp.gmail.com",
    port=587,
    email="seu_email@gmail.com",
    password="sua_senha",
    username="usuario"
) as mailer:
    mailer.destinatarios = ["destinatario@gmail.com"]
    mailer.assunto = "Teste"
    mailer.enviar_email("Olá, esta é uma mensagem de teste!")
```

## Licença

Esta biblioteca é distribuída sob a licença MIT. Consulte o arquivo LICENSE para mais informações.
