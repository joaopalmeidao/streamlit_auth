import streamlit as st
import pandas as pd

from streamlit_auth.core.database.manager import default_engine as engine
from streamlit_auth.authentication.backend.auth import Authenticate
from streamlit_auth.authentication.backend.models import (
    TbSessaoStreamlit,
    TbUsuarioStreamlit,
)

def session_manager_page():
    st.title("🔑 Gerenciar Sessões dos Usuários")

    df_sessoes = Authenticate.get_all_sessions()

    st.subheader("📋 Lista de Sessões Ativas")
    st.dataframe(df_sessoes, height=300, use_container_width=True, hide_index=True)

    # Seção para revogar sessões
    st.subheader("🛠️ Revogar Sessão")

    # Dropdown para selecionar a sessão a revogar
    selected_sessions = st.multiselect("Selecione uma sessão para revogar:", df_sessoes['session_id'])

    # Botão para revogar a sessão selecionada
    if st.button("Revogar Sessão Selecionada"):
        try:
            for session_id in selected_sessions:
                # Encontrar a sessão no banco de dados
                Authenticate.revoke_session(session_id=session_id)
            st.success(f"Sessão {selected_sessions} revogada com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao revogar sessão: {str(e)}")
