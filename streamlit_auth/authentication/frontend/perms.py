from time import sleep

import streamlit as st
from streamlit_auth.authentication.backend.auth import Authenticate
from streamlit_auth.config import settings


def pagina_gerenciar_permissao():
    st.title("🔑 Gerenciar Permissões")
    
    df_perms = Authenticate.get_all_permissions()
    df_all_users = Authenticate.select_all_users()
    lista_perms = settings.APP_NAMES
    
    # Mesclar permissões globais com permissões específicas
    with st.expander('Filtros'):
        tcol1, tcol2 = st.columns(2)
        
        with tcol1:
            f_username = st.text_input("Digite o Nome do Usuário (ou parte dele):").lower().strip()
        
        with tcol2:
            f_app_name = st.text_input("Digite o nome do APP (ou parte dele):").lower().strip()
    
    # Filtrar permissões pelo nome do usuário e ID da DAG
    filtered_df = df_perms[
        (df_perms['username'].str.lower().str.contains(f_username)) &
        (df_perms['app_name'].str.lower().str.contains(f_app_name))
    ].copy()

    # Exibir as permissões filtradas (incluindo usuários com permissão global)
    st.subheader("Permissões dos Usuários:")
    st.dataframe(filtered_df, use_container_width=True, height=300, hide_index=True)
    
    st.write(f"Total de registros filtrados: {len(filtered_df)}")

    # Gerenciamento de permissões
    st.subheader("Gerenciar Permissões")

    # Ações disponíveis
    actions = ["Adicionar Permissão", "Remover Permissão"]
    selected_action = st.selectbox("Escolha uma ação:", actions)

    with st.form(key='dag_management_form'):
        
        if selected_action == "Adicionar Permissão":
            selected_user = st.selectbox("Usuário:", df_all_users['username'])
            select_perms = st.multiselect("Permissões:", lista_perms)
            
            if st.form_submit_button("Adicionar"):
                for app_name in select_perms:
                    Authenticate.adicionar_permissao(selected_user, app_name)
                st.success("Permissões adicionadas com sucesso!")
                sleep(2)
                st.rerun()
                
        elif selected_action == "Remover Permissão":
            selected_user = st.selectbox("Usuário:", df_perms['username'])
            select_perms = st.multiselect("Permissões:", lista_perms)
            
            if st.form_submit_button("Remover"):
                for app_name in select_perms:
                    Authenticate.remover_permissao(selected_user, app_name)
                st.success("Permissões removidas com sucesso!")
                sleep(2)
                st.rerun()
