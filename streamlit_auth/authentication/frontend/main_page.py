import streamlit as st

from .perms import pagina_gerenciar_permissao
from .users import pagina_gerenciar_usuarios


def main_page_gerenciar():
    st.title('Gerenciar')
    
    page = st.selectbox("Escolha uma página", 
        [
            "Usuários",
            "Permissões",
            
            ]
        )
    
    if page == "Usuários":
        pagina_gerenciar_usuarios()
    elif page == "Permissões":
        pagina_gerenciar_permissao()
