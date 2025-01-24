import streamlit as st

from streamlit_auth.config import settings
from streamlit_auth.authentication.backend.auth import (
    Authenticate,
)


def user_register_page():
    with st.expander('📝 Criar Conta'):
        # Form para cada ação
        with st.form(key="user_register_form"):
            nome = st.text_input("Nome Completo:")
            username = st.text_input("Nome de Usuário:")
            email = st.text_input("Email:")
            password = st.text_input("Senha:", type="password")
            confirmar_senha = st.text_input("Confirmar Senha:", type="password")
            if st.form_submit_button("Criar Conta"):
                if password == confirmar_senha:
                    try:
                        Authenticate.insert_user(nome, username, password, email, 'user')
                        st.success("Usuário adicionado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        print(e)
                        st.error(f"Erro ao criar conta.")
                else:
                    st.error("As senhas não coincidem.")
