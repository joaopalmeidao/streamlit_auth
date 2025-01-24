# Meu Projeto

Este é um pacote Python para autenticação segura com Streamlit e 2FA. Ele oferece:

- Autenticação via username e senha com bcrypt.
- Suporte para autenticação de dois fatores (2FA) com TOTP.
- Gerenciamento de sessões no banco de dados.
- Suporte para cookies e gerenciamento de estado no Streamlit.

## Instalação

```bash
pip install streamlit_auth
```

## Exemplo de uso

```python
import streamlit as st
import logging

from streamlit_auth.authentication import (
    Authenticate,
    main_page_auth
)
from streamlit_auth.config import settings


logger = logging.getLogger(settings.MAIN_LOGGER_NAME)


def init_session_state(**kwargs):
    for key, value in kwargs.items():
        if not key in st.session_state.keys():
            st.session_state[key] = value

def init_app():
    init_session_state()
    
    st.set_page_config(page_title="Strealit Authenticate", layout='wide')

    st.markdown(""" 
    <style> 

        .font {                                          
            font-size:30px; 
            font-family: 'Cooper Black'; 
            color: white;
            } 

        #MainMenu, 
        .stAppToolbar,
        .css-10pw50.ea3mdgi1 {
                visibility: hidden;
                }
        
        .css-vk3wp9 {
            background-color: #333333 !important;
            color: black !important;
        }
        
    </style> """, unsafe_allow_html=True)
    

# Página principal
def main():
    
    init_app()
    
    authenticator = Authenticate(
        secret_key='123',
        session_expiry_days=7,
        require_2fa=False,
        auth_reset_views=False,
    )
    
    user_data = authenticator.login("Login")

    authentication_status = user_data['authentication_status']
    name = user_data['name']
    username = user_data['username']
    authenticated_2fa = user_data['authenticated_2fa']
    secret_tfa = user_data.get('secret', None)
    role = user_data['role']

    st.sidebar.write('Strealit Authenticate')
    
    # Logout
    if authentication_status:
        authenticator.logout("Logout")

    # Mensagens básicas
    if authentication_status == False:
        st.warning("Por favor, insira seu nome de usuário e senha corretamente.")
        return

    # Se já autenticado com 2FA OK, mostra aplicação
    if authentication_status and authenticated_2fa:
        
        opcoes_admin = ['Gerenciar']
        
        st.write('Autenticado')
        
        if role == 'admin':
            dd_opcoes_admin = st.sidebar.selectbox(
                "Selecione uma opção:",
                opcoes_admin,
                )
            if dd_opcoes_admin == "Gerenciar":
                main_page_auth()

```
