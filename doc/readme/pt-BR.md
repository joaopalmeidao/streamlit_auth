# Streamlit Auth Library

Descrição

A Streamlit Auth Library é uma biblioteca que adiciona autenticação robusta e recursos de gerenciamento de usuários ao seu aplicativo Streamlit. Com suporte para autenticação de dois fatores (2FA), permissões e gerenciamento de sessões, ela é ideal para aplicativos que requerem segurança e controle de acesso.

...

[Voltar ao README](../../README.md)

## PyPI

[PyPI - streamlit-auth-mfa](https://pypi.org/project/streamlit-auth-mfa/)

## Telas Prontas

### Gerenciar Permissões

![Gerenciar Permissões](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/manage_perms.png?raw=True)

### Gerenciar Usuários

![Gerenciar Usuários](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/user_manager.png?raw=True)

### Gerenciar Sessões

![Gerenciar Sessões](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/session_manager.png?raw=True)

### Login Form

![Login Form](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/login_form.png?raw=True)

### 2FA Form

![2FA Form](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/mfa_form.png?raw=True)

### Reset Form

![Reset Forms](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/reset_forms.png?raw=True)

### Register Form

![Register Form](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/user_register.png?raw=True)

### User Activation Form

![User Activation Form](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/user_activation.png?raw=True)

### Perfil de Usuário

![Perfil de Usuário](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/user_profile.png?raw=True)

## Instalação

```bash
pip install streamlit-auth-mfa
```

## Configuração

A biblioteca utiliza variáveis de ambiente e arquivos de configuração para personalizar comportamentos. Certifique-se de configurar os arquivos necessários antes de usar a biblioteca.

### .env

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

## Recursos

- Autenticação
  - Username e senha: Utiliza bcrypt para segurança.
  - 2FA opcional: Adicione uma camada extra de segurança com TOTP.
  - Gerenciamento de sessões: Rastreamento e controle de logins.
  - Ativação de usuário: Suporte para ativar contas de usuários via link enviado por e-mail.
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

Autenticação Completa

```python
import streamlit as st

from streamlit_auth.authentication import (
    Authenticate,
    user_manager_main_page,
    user_profile_page,
)
from streamlit_auth.config import settings

TITLE = "Strealit Authenticate"

def test_page():
    st.set_page_config(page_title=TITLE, layout='wide')
    
    
    authenticator = Authenticate(
        secret_key='123',
        session_expiry_days=7,
        require_2fa=False,
        auth_reset_views=True,
        site_name='http://localhost:8501/',
    )
    
    user_data = authenticator.login("Login")

    authentication_status = user_data['authentication_status']
    name = user_data['name']
    username = user_data['username']
    authenticated_2fa = user_data['authenticated_2fa']
    role = user_data['role']

    st.sidebar.write(TITLE)
    
    # Mensagens básicas
    if not authentication_status:
        st.warning("Por favor, insira seu nome de usuário.")
        authenticator.user_register_form()
        return

    # Logout
    if authentication_status:
        authenticator.logout("Logout")

    # Se já autenticado com 2FA OK, mostra aplicação
    if authentication_status and authenticated_2fa:
        
        opcoes_admin = ['Gerenciar']
        opcoes_usuario = ['Perfil de Usuário']
        
        st.write('Autenticado')
        
        if role == 'admin':
            user_permissions = opcoes_usuario + opcoes_admin
            
        else:
            user_permissions = authenticator.get_user_apps_perms(username)
            user_permissions += opcoes_usuario
        
        selected_option = st.sidebar.selectbox(
            "Selecione uma opção:",
            user_permissions,
            )
        
        if role == 'admin' and selected_option == "Gerenciar":
            user_manager_main_page()
        
        if selected_option == "Perfil de Usuário":
            user_profile_page(user_data)
```

### Gerenciamento

Use a função user_manager_main_page para exibir a tela de permissões de usuários. Veja como implementar:

```python
from streamlit_auth.authentication import user_manager_main_page

# Tela para gerenciar permissões e usuarios
user_manager_main_page()
```

Execute o servidor normalmente no arquivo criado:

```bash
streamlit run <arquivo criado>.py
```

## Configuração do Banco de Dados

A biblioteca utiliza o SQLAlchemy para gerenciamento de banco de dados, permitindo que você configure qualquer URI suportada pelo SQLAlchemy. Você pode definir a URI do banco de dados no arquivo .env:

```env
DB_URI=<sua_uri_de_banco_de_dados>
```

Exemplos de URIs válidas:

- SQLite: sqlite:///db.sqlite3
- PostgreSQL: postgresql://usuario:senha@localhost/nome_do_banco
- MySQL: mysql+pymysql://usuario:senha@localhost/nome_do_banco
- Microsoft SQL Server: mssql+pyodbc://usuario:senha@dsn

Consulte a documentação do SQLAlchemy para mais detalhes sobre as URIs de banco de dados suportadas.

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
) as mailer:
    mailer.destinatarios = ["destinatario@gmail.com"]
    mailer.assunto = "Teste"
    mailer.enviar_email("Olá, esta é uma mensagem de teste!")
```

## Licença

Esta biblioteca é distribuída sob a licença MIT. Consulte o arquivo [LICENCE](https://github.com/joaopalmeidao/streamlit_auth/blob/main/LICENCE?raw=True) para mais informações.
