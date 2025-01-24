import streamlit as st

from .perms import user_perms_page
from .users import user_manager_page
from .sessions import session_manager_page


def user_manager_page():
    st.title('Gerenciar')
    
    page = st.selectbox("Escolha uma página", 
        [
            "Usuários",
            "Permissões",
            "Sessões",
            ]
        )
    
    if page == "Usuários":
        user_manager_page()
    elif page == "Permissões":
        user_perms_page()
    elif page == "Sessões":
        session_manager_page()
