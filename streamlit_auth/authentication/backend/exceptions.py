import streamlit as st


def display_validation_errors(exception):
    """
    Exibe as mensagens de erro no frontend.
    
    Args:
        exception (ValidationError): A exceção de validação contendo mensagens.
    """
    if isinstance(exception, ValidationError):
        for message in exception.messages:
            st.error(f"❌ {message}")  # Exibe cada mensagem como um erro no Streamlit
    else:
        st.error("❌ Um erro inesperado ocorreu.")

class ValidationError(Exception):
    """
    Exceção personalizada para validação de entradas.
    
    Attributes:
        messages (list): Lista de mensagens de erro.
    """
    def __init__(self, messages):
        if isinstance(messages, str):
            messages = [messages]  # Converte string única em uma lista
        self.messages = messages
        super().__init__("\n".join(self.messages)) 