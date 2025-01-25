import streamlit as st
import logging
import base64
import pandas as pd

from streamlit_auth.authentication import (
    Authenticate,
    user_manager_main_page,
    user_profile_page,
)
from streamlit_auth.config import settings
from doc.app.documentacao import doc_page


logger = logging.getLogger(settings.MAIN_LOGGER_NAME)

TITLE = "Strealit Auth Library"

def test_page():
    st.set_page_config(
        page_title=TITLE,
        layout='wide',
        initial_sidebar_state="expanded",
        page_icon='🔒'
        )
    
    st.sidebar.image(
        'doc/imgs/logo.png'
    )
    
    st.markdown(
        '''
<div style="text-align: center;">
    <img src="https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/logo.png?raw=True" alt="Logo" width="300"/>
</div>
        ''', unsafe_allow_html=True
    )
    
    opcoes_livres = [
        '📝 Documentação',
        f'🔑 {TITLE}'
        ]
    
    tabs = st.tabs(opcoes_livres)
    
    with tabs[0]:
        doc_page()
    
    with tabs[1]:
    
        authenticator = Authenticate(
            secret_key='98duasng@89duas98duan9d8a21321u@#0dsa9',
            session_expiry_days=7,
            require_2fa=False,
            auth_reset_views=False,
            site_name='https://st-mfa.streamlit.app/',
            user_activation_request=False,
        )
        
        authenticator.role_to_create = 'admin'
        
        user_data = authenticator.login("Login")

        authentication_status = user_data['authentication_status']
        username = user_data['username']
        authenticated_2fa = user_data['authenticated_2fa']
        role = user_data['role']
        
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
            opcoes_usuario = [
                'Perfil de Usuário',
                ]
            
            st.sidebar.write(f'Seja bem vindo {username}')
            
            if role == 'admin':
                user_permissions = opcoes_usuario + opcoes_admin  + settings.APP_NAMES
                
            else:
                user_permissions = authenticator.get_user_apps_perms(username)
                user_permissions += opcoes_usuario
            
            selected_option = st.sidebar.selectbox(
                "Selecione uma opção:",
                sorted(user_permissions),
                )
            
            if role == 'admin' and selected_option == "Gerenciar":
                user_manager_main_page()
            
            elif selected_option == "Perfil de Usuário":
                user_profile_page(user_data)
    
    # Rodapé
    st.markdown("""
    ---
    *Desenvolvido por João Paulo Almeida. Conecte-se comigo no [GitHub](https://github.com/joaopalmeidao) e [LinkedIn](https://www.linkedin.com/in/joaopalmeidao/).*
    """)


if __name__ == '__main__':
    Authenticate.create_admin_if_not_exists()
    test_page()
