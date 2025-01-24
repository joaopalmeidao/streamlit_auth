import streamlit as st
import logging

from streamlit_auth.authentication import (
    Authenticate,
    user_manager_page,
    user_profile_page,
    user_register_page,
)
from streamlit_auth.config import settings


logger = logging.getLogger(settings.MAIN_LOGGER_NAME)


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
    secret_tfa = user_data.get('secret', None)
    role = user_data['role']

    st.sidebar.write(TITLE)
    
    # Logout
    if authentication_status:
        authenticator.logout("Logout")

    # Mensagens básicas
    if authentication_status == False:
        st.warning("Por favor, insira seu nome de usuário.")
        user_register_page()
        return

    # Se já autenticado com 2FA OK, mostra aplicação
    if authentication_status and authenticated_2fa:
        
        opcoes_admin = ['Gerenciar']
        opcoes_usuario = ['Perfil de Usuário']
        
        st.write('Autenticado')
        
        if role == 'admin':
            user_permissions = opcoes_usuario + opcoes_admin
            
        else:
            user_permissions = Authenticate.get_user_permissions(username)['app_name'].to_list()
            user_permissions = sorted(list(i for i in set(user_permissions) if i in settings.APP_NAMES))
            user_permissions += opcoes_usuario
        
        selected_option = st.sidebar.selectbox(
            "Selecione uma opção:",
            user_permissions,
            )
        
        if role == 'admin' and selected_option == "Gerenciar":
                user_manager_page()
        
        if selected_option == "Perfil de Usuário":
            user_profile_page(user_data)
