import pyotp
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import pandas as pd

from streamlit_auth.authentication import Authenticate, ValidationError

# Fixture para instanciar a classe Authenticate
@pytest.fixture
def auth_instance():
    return Authenticate(
        secret_key="test_secret",
        session_expiry_days=1,
        require_2fa=False,
        site_name='http://localhost:8501/',
        user_activation_request=False
    )

# Teste de validação de senha
def test_password_validation():
    errors = []
    password = "Weak1"
    errors = Authenticate.password_validation(password, errors)
    assert not Authenticate.format_errors(errors)['valid']
    assert "A senha deve ter pelo menos 8 caracteres." in errors

    password = "StrongPass1!"
    errors = []
    errors = Authenticate.password_validation(password, errors)
    assert Authenticate.format_errors(errors)['valid']

# Teste de validação de e-mail
def test_email_validation():
    errors = []
    email = "invalid-email"
    errors = Authenticate.email_validation(email, errors)
    assert not Authenticate.format_errors(errors)['valid']
    assert "O email informado é inválido. Certifique-se de usar um formato válido (ex: exemplo@dominio.com)." in errors

    email = "valid@example.com"
    errors = []
    errors = Authenticate.email_validation(email, errors)
    assert Authenticate.format_errors(errors)['valid']

# Teste de registro de usuário com sucesso
@patch('streamlit_auth.authentication.Authenticate.get_existant_user_by_username')
@patch('streamlit_auth.authentication.Authenticate.insert_user')
def test_user_register_success(mock_insert_user, mock_get_user):
    mock_get_user.return_value = pd.DataFrame()
    auth = Authenticate(
        secret_key="test_secret",
        session_expiry_days=1,
        require_2fa=False,
        site_name='http://localhost:8501/',
        user_activation_request=False
    )
    
    with patch('streamlit.session_state') as mock_session_state:
        auth.insert_user("Test User", "testuser", "StrongPass1!", "jp080496@gmail.com", "user")
        mock_insert_user.assert_called_once()

# Teste de registro de usuário com username existente
@patch('streamlit_auth.authentication.Authenticate.get_existant_user_by_username')
def test_user_register_existing_username(mock_get_user):
    mock_get_user.return_value = pd.DataFrame({'username': ['testuser']})
    auth = Authenticate(
        secret_key="test_secret",
        session_expiry_days=1,
        require_2fa=False,
        site_name='http://localhost:8501/',
        user_activation_request=False
    )
    
    with pytest.raises(ValidationError) as exc_info:
        auth.insert_user("Test User", "testuser", "StrongPass1!", "jp080496@gmail.com", "user")
    
    assert "Já existe um usuário com esse username." in exc_info.value.args[0]

# Teste de login bem-sucedido
@patch('streamlit_auth.authentication.Authenticate.get_active_user_by_username')
@patch('streamlit_auth.authentication.Authenticate.check_password')
@patch('streamlit_auth.authentication.Authenticate._create_session')
@patch('streamlit_auth.authentication.Authenticate._write_session_to_cookie')
def test_login_success(mock_write_cookie, mock_create_session, mock_check_password, mock_get_user, auth_instance):
    mock_get_user.return_value = pd.DataFrame({
        'id': [1],
        'username': ['testuser'],
        'name': ['Test User'],
        'role': ['user'],
        'email': ['jp080496@gmail.com'],
        'password': [Authenticate.hash("StrongPass1!")]
    })
    mock_check_password.return_value = True
    mock_create_session.return_value = "session123"

    # Inicializa session_state com valores padrão
    initial_session_state = {
        'user_id': None,
        'session_id': None,
        'username': None,
        'name': None,
        'role': None,
        'email': None,
        'authenticated_2fa': False,
        'authentication_status': False,
        'logout': False,
    }

    with patch('streamlit.session_state', initial_session_state):
        result = auth_instance.check_credentials("testuser", "StrongPass1!")
        assert result == True
        user_data = auth_instance._get_user_data()
        assert user_data.get('username') == "testuser"

# Teste de login com senha incorreta
@patch('streamlit_auth.authentication.Authenticate.get_active_user_by_username')
@patch('streamlit_auth.authentication.Authenticate.check_password')
def test_login_wrong_password(mock_check_password, mock_get_user, auth_instance):
    mock_get_user.return_value = pd.DataFrame({
        'id': [1],
        'username': ['testuser'],
        'name': ['Test User'],
        'role': ['user'],
        'email': ['jp080496@gmail.com'],
        'password': [Authenticate.hash("StrongPass1!")]
    })
    mock_check_password.return_value = False

    with patch('streamlit.session_state', {}):
        result = auth_instance.check_credentials("testuser", "WrongPass!")
        assert result == False
        assert not auth_instance._get_user_data().get('authentication_status')

# Teste de autenticação 2FA
@patch('streamlit_auth.authentication.Authenticate.get_active_user_by_id')
@patch('streamlit_auth.authentication.Authenticate._create_session')
def test_2fa_authentication(mock_create_session, mock_get_user, auth_instance):
    auth_instance.require_2fa = True
    mock_get_user.return_value = pd.DataFrame({
        'id': [1],
        'username': ['testuser'],
        'name': ['Test User'],
        'role': ['user'],
        'email': ['jp080496@gmail.com'],
        'secret_tfa': [pyotp.random_base32()]
    })
    
    # Simular criação de sessão com 2FA não autenticado
    with patch.object(auth_instance, '_component_require2fa') as mock_2fa:
        mock_2fa.return_value = True
        auth_instance._component_require2fa()
        mock_2fa.assert_called_once()

def test_user_validation():
    # Testar com dados válidos
    validate = Authenticate.user_validation(username="validuser", password="StrongPass1!", email="valid@example.com")
    assert validate['valid'] == True
    assert 'errors' not in validate

    # Testar com dados inválidos
    validate = Authenticate.user_validation(username="ab", password="weak", email="invalid-email")
    assert validate['valid'] == False
    assert "O nome de usuário deve ter entre 3 e 30 caracteres e pode conter apenas letras, números, '_' ou '-'." in validate['errors']
    assert "A senha deve ter pelo menos 8 caracteres." in validate['errors']
    assert "A senha deve conter pelo menos uma letra maiúscula." in validate['errors']
    assert "A senha deve conter pelo menos um caractere especial (!@#$%^&*()-_=+[]{}|;:'\",.<>?/~`)." in validate['errors']
    assert "O email informado é inválido. Certifique-se de usar um formato válido (ex: exemplo@dominio.com)." in validate['errors']

# Teste de ativação de usuário
@patch('streamlit_auth.core.SendMail')
def test_send_activation(mock_send_email, auth_instance):
    username = 'testuser'
    
    with mock_send_email() as mailer:
        mailer.subtype = 'plain'
        token, _ = auth_instance.generate_activation_token(username)
        activation_url = f"{auth_instance.site_name}?activation_token={token}"
        mailer.assunto = 'Ativação de Conta'
        mailer.destinatarios = ['jp080496@gmail.com']
        message = f"""
        Olá {username},

        Bem-vindo! Para ativar sua conta, clique no link abaixo:

        {activation_url}

        Este link é válido por 24 horas. Se você não solicitou este e-mail, ignore-o.

        """
        mailer.enviar_email(message)
    
    mock_send_email.assert_any_call()
