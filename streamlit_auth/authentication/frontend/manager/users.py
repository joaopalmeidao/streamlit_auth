import streamlit as st

from streamlit_auth.config import settings
from streamlit_auth.authentication.backend.models import ROLES
from streamlit_auth.authentication.backend.auth import (
    Authenticate,
)


def user_manager_page():
    st.title("🔑 Gerenciar Usuários")

    # Obter lista de usuários (sem a senha)
    df_usuarios = Authenticate.get_all_users().drop(columns=[
        "password",
        "secret_tfa",
        "reset_token",
        ])

    # Exibir a tabela de usuários existentes
    st.subheader("📋 Lista de Usuários")
    if not df_usuarios.empty:
        st.dataframe(df_usuarios, height=300, use_container_width=True)
    else:
        st.info("Nenhum usuário encontrado.")

    # Gerenciar Usuários
    st.subheader("⚙️ Gerenciar Usuário")

    # Dropdown para selecionar usuário
    if not df_usuarios.empty:
        selected_user = st.selectbox(
            "Selecione um usuário:", df_usuarios["username"], index=0
        )
        df_user = df_usuarios[df_usuarios["username"] == selected_user].copy()
    else:
        st.warning("Nenhum usuário disponível para gerenciar.")
        return

    # Ações disponíveis
    actions = [
        "Adicionar Usuário",
        "Trocar Senha",
        "Atualizar Dados",
        "Desativar Usuário",
        "Ativar Usuário",
        "Deletar Usuário",
        "Resetar Sessões",
        "Resetar 2FA",
    ]
    
    selected_action = st.selectbox("Escolha uma ação:", actions)

    # Form para cada ação
    with st.form(key="user_management_form"):
        if selected_action == "Trocar Senha":
            st.write("### Trocar Senha")
            new_password = st.text_input("Nova Senha:", type="password")
            confirmar_senha = st.text_input("Confirmar Nova Senha:", type="password")
            if st.form_submit_button("Atualizar Senha"):
                if new_password == confirmar_senha:
                    try:
                        Authenticate.update_senha(selected_user, new_password)
                        st.success("Senha atualizada com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao atualizar senha: {str(e)}")
                else:
                    st.error("As senhas não coincidem.")

        elif selected_action == "Atualizar Dados":
            st.write("### Atualizar Dados do Usuário")
            new_email = st.text_input("Email:", value=df_user["email"].values[0])
            new_role = st.selectbox(
                "Função:", ROLES, index=ROLES.index(df_user["role"].values[0])
            )
            new_name = st.text_input("Nome Completo:", value=df_user["nome"].values[0])
            if st.form_submit_button("Atualizar Dados"):
                try:
                    Authenticate.update_dados(
                        username=selected_user,
                        new_email=new_email,
                        new_role=new_role,
                        new_name=new_name
                        )
                    st.success("Dados do usuário atualizados com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar dados: {str(e)}")

        elif selected_action == "Adicionar Usuário":
            st.write("### Adicionar Novo Usuário")
            nome = st.text_input("Nome Completo:")
            username = st.text_input("Nome de Usuário:")
            email = st.text_input("Email:")
            role = st.selectbox("Função:", ROLES, index=0)
            password = st.text_input("Senha:", type="password")
            confirmar_senha = st.text_input("Confirmar Senha:", type="password")
            if st.form_submit_button("Adicionar Usuário"):
                if password == confirmar_senha:
                    try:
                        Authenticate.insert_user(nome, username, password, email, role)
                        st.success("Usuário adicionado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao adicionar usuário: {str(e)}")
                else:
                    st.error("As senhas não coincidem.")

        elif selected_action == "Desativar Usuário":
            st.write("### Desativar Usuário")
            if st.form_submit_button("Desativar"):
                try:
                    Authenticate.deactivate_user(selected_user)
                    st.success("Usuário desativado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao desativar usuário: {str(e)}")

        elif selected_action == "Ativar Usuário":
            st.write("### Ativar Usuário")
            if st.form_submit_button("Ativar"):
                try:
                    Authenticate.active_user(selected_user)
                    st.success("Usuário ativado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao ativar usuário: {str(e)}")

        elif selected_action == "Deletar Usuário":
            st.write("### Deletar Usuário")
            st.warning(f"Você está prestes a deletar o usuário **{selected_user}**.")
            if st.form_submit_button("Deletar"):
                try:
                    Authenticate.delete_usuario(selected_user)
                    st.success("Usuário deletado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao deletar usuário: {str(e)}")

        elif selected_action == "Resetar 2FA":
            st.write("### Resetar 2FA")
            if st.form_submit_button("Resetar"):
                try:
                    Authenticate.delete_secret(selected_user)
                    st.success("2FA resetado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao resetar 2FA: {str(e)}")

        elif selected_action == "Resetar Sessões":
            st.write("### Resetar Sessões")
            if st.form_submit_button("Resetar"):
                try:
                    Authenticate.revoke_session(username=selected_user)
                    st.success("Sessões do usuário resetadas com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao resetar sessões: {str(e)}")
