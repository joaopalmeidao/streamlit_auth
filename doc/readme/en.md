# Streamlit Auth Library

Description

The Streamlit Auth Library is a robust authentication and user management library for your Streamlit application. With support for two-factor authentication (2FA), permissions, and session management, it is ideal for applications requiring security and access control.

...

[Back to README](../../README.md)

## PyPI

[PyPI - streamlit-auth-mfa](https://pypi.org/project/streamlit-auth-mfa/)

## Ready-to-Use Screens

### Manage Permissions

![Manage Permissions](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/manage_perms.png?raw=True)

### Manage Users

![Manage Users](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/user_manager.png?raw=True)

### Manage Sessions

![Manage Sessions](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/session_manager.png?raw=True)

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

### User Profile

![User Profile](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/user_profile.png?raw=True)

## Instalação

```bash
pip install streamlit-auth-mfa
```

## Installation

The library uses environment variables and configuration files to customize behavior. Make sure to set up the required files before using the library.

### .env

Environment variables should be configured in the .env file:

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

## Configuration Files

config/app_names.json
Define the names of the applications for which you manage permissions:

```json
{
    "APP_NAMES": ["App1", "App2", "App3"]
}
```

## Features

- Authentication
  - Username and password: Uses bcrypt for security.
  - Optional 2FA: Adds an extra layer of security with TOTP.
  - Session management: Tracks and controls logins.
  - User Activation: Support for activating user accounts via a link sent by email.
- User and Permission Management
  - Manage users: Add, edit, or delete users.
  - Manage permissions: Control access by application.
- Email Integration
  - Send transactional emails, including support for attachments and embedded images.

## Usage Example

Simple Authentication

```python
from streamlit_auth.authentication import Authenticate

authenticator = Authenticate(
    secret_key='my_secret_key',
    session_expiry_days=7,
    require_2fa=True
)

user_data = authenticator.login("Login")

if user_data['authentication_status']:
    st.success(f"Welcome, {user_data['name']}!")
    authenticator.logout("Logout")
else:
    st.error("Authentication failed. Please check your credentials.")
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

TITLE = "Streamlit Authenticate"

def test_page():
    st.set_page_config(page_title=TITLE, layout='wide')
    
    authenticator = Authenticate(
        secret_key='123',
        session_expiry_days=7,
        require_2fa=True,
        auth_reset_views=True,
        site_name='http://localhost:8501/',
    )
    
    user_data = authenticator.login("Login")

    authentication_status = user_data['authentication_status']
    name = user_data['name']
    username = user_data['username']
    authenticated_2fa = user_data['authenticated_2fa']
    secret_tfa = user_data.get('secret', None)
    role = user_data['role']

    st.sidebar.write(TITLE)
    
    # Basic Messages
    if not authentication_status:
        st.warning("Please enter your username.")
        authenticator.user_register_form()
        return

    # Logout
    if authentication_status:
        authenticator.logout("Logout")

    # If already authenticated with 2FA, display the application
    if authentication_status and authenticated_2fa:
        
        admin_options = ['Manage']
        user_options = ['User Profile']
        
        st.write('Authenticated')
        
        if role == 'admin':
            user_permissions = user_options + admin_options
            
        else:
            user_permissions = Authenticate.get_user_permissions(username)['app_name'].to_list()
            user_permissions = sorted(list(i for i in set(user_permissions) if i in settings.APP_NAMES))
            user_permissions += user_options
        
        selected_option = st.sidebar.selectbox(
            "Select an option:",
            user_permissions,
        )
        
        if role == 'admin' and selected_option == "Manage":
            user_manager_main_page()
        
        if selected_option == "User Profile":
            user_profile_page(user_data)
```

### Gerenciamento

Use the user_manager_main_page function to display the user permissions management screen. Here is how to implement it:

```python
from streamlit_auth.authentication import user_manager_main_page

# Screen for managing permissions and users
user_manager_main_page()
```

Run the server with the created file:

```bash
streamlit run <arquivo criado>.py
```

## Database Configuration

The library uses SQLAlchemy for database management, allowing you to configure any URI supported by SQLAlchemy. You can set the database URI in the .env file:

```env
DB_URI=<your_database_uri>
```

Examples of valid URIs:

- SQLite: sqlite:///db.sqlite3
- PostgreSQL: postgresql://user:password@localhost/dbname
- MySQL: mysql+pymysql://user:password@localhost/dbname
- Microsoft SQL Server: mssql+pyodbc://user:password@dsn

Refer to the SQLAlchemy documentation for more details on supported database URIs.

## Database Models

The library provides built-in models for managing users and sessions:

- TbUsuarioStreamlit - User management.
- TbSessaoStreamlit - Session tracking.
- TbPermissaoUsuariosStreamlit - Permission control.

## Email Sending

With the SendMail class, you can send emails with support for attachments and images.

```python
from streamlit_auth.enviar_email import SendMail

with SendMail(
    host="smtp.gmail.com",
    port=587,
    email="your_email@gmail.com",
    password="your_password",
) as mailer:
    mailer.destinatarios = ["recipient@gmail.com"]
    mailer.assunto = "Test"
    mailer.enviar_email("Hello, this is a test message!")
```

## License

This library is distributed under the MIT license. See the [LICENCE](https://github.com/joaopalmeidao/streamlit_auth/blob/main/LICENCE?raw=True) file for more details.
