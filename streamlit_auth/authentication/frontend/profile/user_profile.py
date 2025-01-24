import streamlit as st
import pandas as pd

from streamlit_auth.core.database.manager import default_engine as engine
from streamlit_auth.authentication.backend.auth import Authenticate
from streamlit_auth.authentication.backend.models import (
    TbUsuarioStreamlit,
    TbPermissaoUsuariosStreamlit
    )


def user_profile_page(user_data):
    st.title("👤 Perfil do Usuário")

    # Exibe as informações do usuário
    st.subheader("📄 Informações Pessoais")
    with st.form("form_editar_perfil"):
        nome = st.text_input("Nome", value=user_data['name'])
        email = st.text_input("Email", value=user_data['email'])
        _ = st.text_input("Nome de Usuário", value=user_data['username'], disabled=True)

        submit_button = st.form_submit_button(label="Atualizar Perfil")

    if submit_button:
        try:
            Authenticate.update_dados(
                username=user_data['username'],
                new_email=email,
                new_name=nome
            )
            st.success("Perfil atualizado com sucesso!")
        except Exception as e:
            st.error(f"Erro ao atualizar o perfil.")

    # Exibe permissões do usuário
    st.subheader("🔒 Permissões")
    if user_data['role'] == 'admin':
        st.success("O usuário tem permissão global.")
    else:
        df_permissoes: pd.DataFrame = Authenticate.get_user_permissions(user_data['username']).drop(
            columns=[
                'id',
                'date',
                'username',
            ]
        )
        if not df_permissoes.empty:
            st.dataframe(df_permissoes, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma permissão encontrada para este usuário.")

    # Opção para redefinir senha
    st.subheader("🔑 Redefinir Senha")
    with st.form("form_redefinir_senha"):
        current_password = st.text_input("Senha Atual", type="password")
        new_password = st.text_input("Nova Senha", type="password")
        confirm_new_password = st.text_input("Confirmar Nova Senha", type="password")

        submit_reset = st.form_submit_button(label="Redefinir Senha")

    if submit_reset:
        df_user: pd.DataFrame = Authenticate.get_active_user_by_username(user_data['username'])
        
        # Verifica a senha atual
        if not Authenticate.check_password(current_password, df_user['password'][0]):
            st.error("Senha atual incorreta.")
        elif new_password != confirm_new_password:
            st.error("As novas senhas não coincidem.")
        else:
            try:
                Authenticate.update_senha(user_data['username'], new_password)
                st.success("Senha atualizada com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao atualizar senha.")
