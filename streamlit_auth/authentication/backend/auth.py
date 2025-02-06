from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import bcrypt
import pyotp
import qrcode
import io
import extra_streamlit_components as stx
import logging
import uuid
from time import sleep
import secrets
import hashlib
from sqlalchemy.orm import Session
import re

from sqlalchemy import text
from streamlit_auth.core.enviar_email import SendMail
from streamlit_auth.core.database.manager import (
    default_engine as engine,
    execute_query,
    )
from streamlit_auth.config import settings
from .exceptions import (
    ValidationError,
    display_errors,
)
from .models import (
    ROLES,
    Base,
    TbUsuarioStreamlit,
    TbSessaoStreamlit,
    TbPermissaoUsuariosStreamlit,
    )


if not settings.DEBUG:
    st.set_option('client.showErrorDetails', False)

logger = logging.getLogger(settings.MAIN_LOGGER_NAME)


class Authenticate:
    """
    Classe de autenticação segura com:
    - Armazenamento de sessões no banco de dados.
    - Verificação de senha com bcrypt.
    - Fluxo completo de configuração e autenticação 2FA (opcional).
    - Logs de ações do usuário.
    - Sessão e estado gerenciados pelo Streamlit.
    """
    defaults = {
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
    
    role_to_create = 'user'

    def __init__(self, 
        secret_key: str,
        session_expiry_days: int = 7,
        require_2fa: bool = True,
        cookie_name: str = 'session',
        auth_reset_views: bool = False,
        site_name: str = 'http://localhost:8501/',
        
        max_sessions: int = None,
        user_activation_request: bool = True,
        
        limit_login_fail: bool = False,
        max_login_attempts: int = 5,
        lockout_time: int = 15,
        
        ) -> None:
        self.cookie_name = cookie_name
        self.secret_key = secret_key
        self.session_expiry_days = session_expiry_days
        self.require_2fa = require_2fa
        self.auth_reset_views = auth_reset_views
        self.site_name = site_name
        
        self.cookie_manager = stx.CookieManager()
        
        self.max_sessions = max_sessions
        self.user_activation_request = user_activation_request
        
        self.limit_login_fail = limit_login_fail
        self.max_login_attempts = max_login_attempts
        self.lockout_time = lockout_time # minutes

        # Inicializa o session_state caso não exista
        self._initialize_session_state()

        # Checa e restaura a sessão a partir do cookie
        self._check_and_restore_session_from_cookie()

        if self.auth_reset_views:
            if not settings.EMAIL or not settings.EMAIL_PASSWORD:
                logger.warning("SETTINGS WARNING: Configurações de email estão incompletas. Funcionalidades de email podem não funcionar corretamente.")

    def _initialize_session_state(self) -> None:
        # Definição inicial das variáveis de sessão
        for k, v in self.defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v
    
    def _check_and_restore_session_from_cookie(self) -> None:
        """Lê o cookie session_id, busca a sessão no DB e restaura o estado do usuário se válido."""
        session_id = self.cookie_manager.get(self.cookie_name)
        
        if session_id:
            session_data = self.get_session_by_id(session_id)

            if session_data:
                if pd.to_datetime(session_data['expires_at']) > datetime.utcnow():
                    user_id = session_data['user_id']
                    authenticated_2fa = session_data['authenticated_2fa']

                    # Busca dados do usuário no DB
                    df_user = self.get_active_user_by_id(user_id)

                    if not df_user.empty:
                        # Atualiza session_state apenas se não estiver já autenticado
                        if not st.session_state['authentication_status']:
                            st.session_state['user_id'] = user_id
                            st.session_state['session_id'] = session_id
                            
                            st.session_state['username'] = df_user['username'][0]
                            st.session_state['name'] = str(df_user['name'][0]).title()
                            st.session_state['role'] = df_user['role'][0]
                            st.session_state['email'] = df_user['email'][0]

                            if self.require_2fa:
                                st.session_state['authenticated_2fa'] = authenticated_2fa
                                st.session_state['authentication_status'] = True
                                st.session_state['logout'] = False
                            else:
                                st.session_state['authenticated_2fa'] = True  # Considera 2FA como autenticado
                                st.session_state['authentication_status'] = True
                                st.session_state['logout'] = False

    def _create_session(self, user_id: int, authenticated_2fa: bool) -> str:
        """Cria uma nova sessão no banco de dados e retorna o session_id."""
        if self.max_sessions:
            active_sessions = self.get_active_sessions(user_id)
            if len(active_sessions) >= self.max_sessions:
                # Revoga a sessão mais antiga
                oldest_session = active_sessions.iloc[0]
                self.revoke_session(session_id=oldest_session['session_id'])
                logger.debug(f"Limite de sessões atingido para o usuário {user_id}. Sessão antiga revogada.")
        
        session_id = self.generate_session_id()
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(days=self.session_expiry_days)

        # Gerar fingerprint do dispositivo
        fingerprint = self.generate_device_fingerprint(st.context.headers)

        execute_query('''
            INSERT INTO TbSessaoStreamlit (
                session_id,
                user_id,
                authenticated_2fa,
                created_at,
                expires_at,
                fingerprint
            )
            VALUES (
                :session_id,
                :user_id,
                :authenticated_2fa,
                :created_at,
                :expires_at,
                :fingerprint
            )
        ''', params={
            'session_id': session_id,
            'user_id': user_id,
            'authenticated_2fa': authenticated_2fa,
            'created_at': created_at,
            'expires_at': expires_at,
            'fingerprint': fingerprint
        })
        return session_id

    def _update_session_expiry(self, session_id: str) -> None:
        """Atualiza a data de expiração da sessão."""
        new_expires_at = datetime.utcnow() + timedelta(days=self.session_expiry_days)
        execute_query('''
            UPDATE TbSessaoStreamlit
            SET expires_at = :expires_at
            WHERE session_id = :session_id
        ''', params={
            'expires_at': new_expires_at,
            'session_id': session_id
        })

    def _write_session_to_cookie(self, session_id: str) -> None:
        """Escreve o session_id no cookie."""
        self.cookie_manager.delete(self.cookie_name)
        expire_date = datetime.now() + timedelta(days=self.session_expiry_days)
        while True:
            try:
                self.cookie_manager.set(
                    self.cookie_name, 
                    session_id, 
                    expires_at=expire_date, 
                    secure=False if settings.DEBUG else True,
                    same_site='strict' if settings.DEBUG else 'lax',
                )
                session_id = self.cookie_manager.get(self.cookie_name)
                if session_id:
                    break
            except: 
                sleep(2)

    def _clear_session_and_cookie(self, session_id: str) -> None:
        """Limpa sessão e cookie ao fazer logout ou falha de autenticação."""
        logger.debug('Limpando sessão e cookie...')
        if self.cookie_name in self.cookie_manager.cookies:
            self.cookie_manager.delete(self.cookie_name) 
        execute_query('''
            DELETE FROM TbSessaoStreamlit
            WHERE session_id = :session_id
        ''', params={'session_id': session_id})
        for key in self.defaults:
            st.session_state[key] = None
        st.session_state['logout'] = True
        st.session_state['authentication_status'] = False
        st.session_state['authenticated_2fa'] = False
    
    def _component_require2fa(self) -> None:
        if st.session_state['authentication_status'] and not st.session_state['authenticated_2fa']:
            user_id = st.session_state['user_id']
            df_user = self.get_active_user_by_id(user_id)
            secret_db = df_user['secret_tfa'][0]

            if not secret_db:
                # Configurar 2FA
                st.info("Você ainda não configurou o 2FA. Por favor, configure agora.")
                if self._configurar_2fa(df_user):
                    # Atualizar a sessão para refletir que 2FA foi autenticado
                    session_id = st.session_state['session_id']
                    if session_id:
                        self._update_session_authenticated_2fa(session_id, True)
                    st.session_state['authenticated_2fa'] = True
                    st.rerun()
            else:
                # Autenticar 2FA
                st.info("Por favor, autentique-se via 2FA.")
                if self._autenticar_2fa(df_user, secret_db):
                    # Atualizar a sessão para refletir que 2FA foi autenticado
                    session_id = st.session_state['session_id']
                    if session_id:
                        self._update_session_authenticated_2fa(session_id, True)
                    st.session_state['authenticated_2fa'] = True
                    st.rerun()
    
    def _component_create_session(self) -> None:
        # Criar nova sessão
        session_id = self._create_session(int(st.session_state['user_id']), st.session_state['authenticated_2fa'])
        logger.debug(f'Session ID: {session_id}')
        if session_id:
            st.session_state['session_id'] = session_id
            self._write_session_to_cookie(session_id)
        else:
            st.error("Erro ao criar sessão. Tente novamente.")

    def logout(
        self,
        button_name: str,
        container = st.sidebar,
        key: str = None,
        session_keys_to_delete: list = []
        ) -> None:
        if container.button(button_name, key=key):
            for i in session_keys_to_delete:
                if i in st.session_state.keys():
                    st.session_state[i] = None
                    
            session_id = st.session_state['session_id']
            self._perform_logout(session_id)

    def _perform_logout(self, session_id: str) -> None:
        self._clear_session_and_cookie(session_id)
        st.rerun()

    def _configurar_2fa(self, df_user: pd.DataFrame, container=st) -> bool:
        username = df_user['username'][0]
        # Se já existir segredo no DB, não precisamos gerar outro, apenas autenticar
        secret_db = df_user['secret_tfa'][0]
        if secret_db:
            return self._autenticar_2fa(df_user, secret_db)

        # Gera novo segredo 2FA
        secret = pyotp.random_base32()
        
        if not 'secret2fa_config' in st.session_state:
            st.session_state['secret2fa_config'] = secret
        
        # Gera QR Code
        totp = pyotp.TOTP(st.session_state['secret2fa_config'])
        provisioning_uri = totp.provisioning_uri(username, issuer_name=self.site_name)

        qr = qrcode.make(provisioning_uri)
        buffered = io.BytesIO()
        qr.save(buffered)
        buffered.seek(0)

        container.write("Este é seu segredo, mantenha-o seguro!")
        container.write(st.session_state['secret2fa_config'])
        container.write("Escaneie o QR Code com seu aplicativo de autenticação (Google Authenticator/Authy):")
        container.image(buffered)

        auth_form = container.form(f"2fa_config_form")
        auth_form.subheader("Autenticação 2FA")
        otp = auth_form.text_input("Digite o código 2FA gerado pelo app", key=f"2fa_auth_code_input")
        submitted = auth_form.form_submit_button("Autenticar")

        if submitted:
            # Solicita o primeiro código
            if otp:
                if totp.verify(otp, valid_window=1):
                    Authenticate.save_secret_to_db(username, st.session_state['secret2fa_config'])
                    container.success("Configuração do 2FA bem-sucedida!")
                    # 2FA autenticado
                    return True
                else:
                    container.error("Código 2FA inválido! Tente novamente.")
            else:
                container.warning("Por favor, insira o código 2FA antes de autenticar.")

        else:
            container.warning("Por favor, insira o código 2FA antes de autenticar.")

        return False

    def _autenticar_2fa(self, df_user: pd.DataFrame, secret_tfa: str, container: st = st) -> bool:
        username = df_user['username'][0]
        totp = pyotp.TOTP(secret_tfa)

        auth_form = container.form(f"2fa_auth_form")
        auth_form.subheader("Autenticação 2FA")
        otp = auth_form.text_input("Digite o código 2FA", key=f"2fa_auth_code_input")
        submitted = auth_form.form_submit_button("Autenticar")

        if submitted:
            if otp:
                if totp.verify(otp, valid_window=1):
                    container.success("Autenticação 2FA bem-sucedida!")
                    return True
                else:
                    container.error("Código 2FA inválido! Tente novamente.")
            else:
                container.warning("Por favor, insira o código 2FA antes de autenticar.")

        return False

    def _update_session_authenticated_2fa(self, session_id: str, authenticated: bool) -> None:
        """Atualiza o campo authenticated_2fa na sessão."""
        execute_query('''
            UPDATE TbSessaoStreamlit
            SET authenticated_2fa = :authenticated
            WHERE session_id = :session_id
        ''', params={
            'authenticated': authenticated,
            'session_id': session_id
        })

    def _get_user_data(self) -> dict:
        return {
            'user_id': st.session_state['user_id'],
            'session_id': st.session_state['session_id'],
            'username': st.session_state['username'],
            'name': st.session_state['name'],
            'role': st.session_state['role'],
            'email': st.session_state['email'],
            'authentication_status': st.session_state['authentication_status'],
            'authenticated_2fa': st.session_state['authenticated_2fa']
        }
    
    def _request_password_reset(self, container: st = st) -> None:
        with container:
            with st.expander('♻️ Solicitar Redefinição de Senha'):
                form = st.form('password_reset')
                username = form.text_input("Username")
                if form.form_submit_button("Enviar Link de Redefinição"):
                    if not username:
                        st.error('Preencha o username')
                        return
                    with st.spinner('Enviando...'):
                        df = pd.read_sql(text('''
                            SELECT email
                            FROM TbUsuarioStreamlit
                            WHERE username = :username
                        '''), engine, params={'username': username}).head(1)

                        if not df.empty:
                            email = df.email[0]
                            token, _ = Authenticate.generate_reset_password_token(username)
                            reset_url = f"{self.site_name}?password_token={token}"
                            Authenticate.send_reset_email(username, email, reset_url, "Senha")
                        st.success("Um link de redefinição de senha foi enviado para o seu e-mail.")
    
    def _reset_password(self, container: st = st) -> None:
        token = st.query_params.get('password_token')
        if not token:
            return
        
        df = pd.read_sql(text('''
            SELECT username, reset_password_token_expiry
            FROM TbUsuarioStreamlit
            WHERE reset_password_token = :token
        '''), engine, params={'token': token}).head(1)

        
        st.title("Redefinir Senha")
        if df.empty:
            st.error("Token inválido.")
            st.query_params.clear()
            return

        username, expiry = df.username[0], df.reset_password_token_expiry[0]
        if datetime.utcnow() > pd.to_datetime(expiry):
            st.error("Token expirado.")
            st.query_params.clear()
            return

        container.success(f"Bem-vindo, {username}. Redefina sua senha abaixo.")

        new_password = container.text_input("Nova Senha", type="password")
        confirm_password = container.text_input("Confirme a Nova Senha", type="password")

        if container.button("Redefinir"):
            if not new_password or new_password != confirm_password:
                container.error("As senhas não coincidem.")
            else:
                hashed_pass = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

                execute_query('''
                    UPDATE TbUsuarioStreamlit
                    SET password = :password,
                        reset_password_token = NULL,
                        reset_password_token_expiry = NULL
                    WHERE username = :username
                ''', params={'password': hashed_pass, 'username': username})

                container.success("Senha redefinida com sucesso!")
                st.query_params.clear()
                st.rerun()
        else:
            st.stop()
    
    def _request_2fa_reset(self, container: st = st) -> None:
        with container:
            if self.require_2fa:
                with st.expander('♻️ Solicitar Redefinição de 2FA'):
                    form = st.form('2fa_reset')
                    username = form.text_input("Username")
                    if form.form_submit_button("Enviar Link de Redefinição"):
                        if not username:
                            st.error('Preencha o username')
                            return
                        with st.spinner('Enviando...'):
                            df = pd.read_sql(text('''
                                SELECT email
                                FROM TbUsuarioStreamlit
                                WHERE username = :username
                            '''), engine, params={'username': username}).head(1)

                            if not df.empty:
                                email = df.email[0]
                                token, _ = Authenticate.generate_reset_tfa_token(username)
                                reset_url = f"{self.site_name}?2fa_token={token}"
                                Authenticate.send_reset_email(username, email, reset_url, "2FA")
                            st.success("Um link de redefinição de 2FA foi enviado para o seu e-mail.")
        
    def _reset_2fa(self, container: st = st) -> None:
        if self.require_2fa:
            token = st.query_params.get('2fa_token')
            if not token:
                return

            df = pd.read_sql(text('''
                SELECT username, reset_tfa_token_expiry
                FROM TbUsuarioStreamlit
                WHERE reset_tfa_token = :token
            '''), engine, params={'token': token}).head(1)
            
            if df.empty:
                st.error("Token inválido.")
                st.query_params.clear()
                return

            st.title("Redefinir 2FA")
            username, expiry = df.username[0], df.reset_tfa_token_expiry[0]
            if datetime.utcnow() > pd.to_datetime(expiry):
                st.error("Token expirado.")
                st.query_params.clear()
                return

            container.success(f"Bem-vindo, {username}. Redefina o 2FA abaixo.")

            if container.button("Redefinir 2FA"):
                execute_query('''
                    UPDATE TbUsuarioStreamlit
                    SET secret_tfa = NULL,
                        reset_tfa_token = NULL,
                        reset_tfa_token_expiry = NULL
                    WHERE username = :username
                ''', params={'username': username})

                st.success("2FA redefinido com sucesso! Você será solicitado a configurar novamente ao fazer login.")
                st.query_params.clear()
                st.rerun()
            else:
                st.stop()
    
    def _activate_user(self, container: st = st) -> None:
        """
        Processa o token de ativação e ativa o usuário.
        """
        token = st.query_params.get('activation_token')
        if not token:
            return
        
        df = pd.read_sql(text('''
            SELECT username, activation_token_expiry
            FROM TbUsuarioStreamlit
            WHERE activation_token = :token
        '''), engine, params={'token': token}).head(1)
        
        st.title("Ativar Conta")
        if df.empty:
            st.error("Token inválido.")
            st.query_params.clear()
            return

        username, expiry = df.username[0], df.activation_token_expiry[0]
        if datetime.utcnow() > pd.to_datetime(expiry):
            st.error("Token expirado.")
            st.query_params.clear()
            return

        container.success(f"Bem-vindo, {username}. Sua conta foi ativada com sucesso!")
    
        execute_query('''
            UPDATE TbUsuarioStreamlit
            SET active = 1,
                activation_token = NULL,
                activation_token_expiry = NULL
            WHERE username = :username
        ''', params={'username': username})
        
        st.query_params.clear()
    
    def _request_user_activation(self, container: st = st) -> None:
        """
        Solicita a ativação do usuário enviando um link por e-mail.
        """
        with container:
            with st.expander('📩 Solicitar Ativação de Conta'):
                form = st.form('activation_request')
                username = form.text_input("Username")
                if form.form_submit_button("Enviar Link de Ativação"):
                    df_user = Authenticate.get_active_user_by_username(username)
                    if df_user.empty:
                        if not username:
                            st.error('Preencha o username.')
                            return
                        
                        with st.spinner('Enviando...'):
                            df = pd.read_sql(text('''
                                SELECT email
                                FROM TbUsuarioStreamlit
                                WHERE username = :username
                            '''), engine, params={'username': username}).head(1)
                            
                            if not df.empty:
                                email = df.email[0]
                                token, _ = self.generate_activation_token(username)
                                activation_url = f"{self.site_name}?activation_token={token}"
                                self.send_activation_email(username, email, activation_url)
                                st.success("Um link de ativação foi enviado para o seu e-mail.")
                    else:
                        st.error('Usuário já está ativo.')

    def user_register_form(self) -> None:
        col1, col2 = st.columns([2, 1])
        
        with col1.expander('📝 Criar Conta'):
            # Form para cada ação
            with st.form(key="user_register_form"):
                nome = st.text_input("Nome Completo:")
                username = st.text_input("Nome de Usuário:")
                email = st.text_input("Email:")
                password = st.text_input("Senha:", type="password")
                confirmar_senha = st.text_input("Confirmar Senha:", type="password")
                if st.form_submit_button("Criar Conta"):
                    if password == confirmar_senha:
                        with st.spinner('Criando usuário...'):
                            try:
                                active = False if self.user_activation_request else True
                                Authenticate.insert_user(
                                    nome, 
                                    username, 
                                    password, 
                                    email, 
                                    self.role_to_create,
                                    active,
                                    )
                                message = "Usuário adicionado com sucesso!"
                                if not active:
                                    token, expiry = self.generate_activation_token(username)
                                    activation_url = f"{self.site_name}?activation_token={token}"
                                    self.send_activation_email(username, email, activation_url)
                                    message = f"Foi enviado um email de ativação para {email}."
                                st.success(message)
                            except Exception as e:
                                logger.error(e, exc_info=True)
                                display_errors(e)
                    else:
                        st.error("As senhas não coincidem.")
        
        if self.user_activation_request:
            self._request_user_activation(col2)
    
    def login(self, form_name: str, container: st = st) -> None:
        """
        Realiza o fluxo completo de login:
        1. Se não autenticado: pede username e senha.
        2. Verifica credenciais. Se ok, verifica se necessita 2FA.
        3. Se 2FA não configurado, configura. Se configurado, pede código.
        4. Se 2FA verificado, gera sessão e salva no cookie.
        """

        self._activate_user()
        
        if self.auth_reset_views:
            self._reset_password()
            
            if self.require_2fa:
                self._reset_2fa()
        
        col1, col2 = st.columns(2)
        
        if st.session_state['authentication_status']:
            if self.require_2fa:
                if st.session_state['authenticated_2fa']:
                    # Já autenticado completamente
                    return self._get_user_data()
            else:
                # 2FA não é requerido
                return self._get_user_data()

        # Passo 1: Se não autenticado (username/senha)
        if not st.session_state['authentication_status']:
            if self.auth_reset_views:
                self._request_password_reset(col1)

            login_form = container.form('Login')
            login_form.subheader(form_name)
            
            username = login_form.text_input('Username', key='login_username_input').strip()
            password = login_form.text_input('Password', type='password', key='login_password_input')
            
            if login_form.form_submit_button('Login'):
                if not username:
                    container.error("Preencha o campo Username.")

                if self.check_credentials(username, password):
                    
                    self._component_create_session()
                    logger.debug(f"Usuário {username} autenticado com sucesso.")
                else:
                    if not self.limit_login_fail:
                        container.error('Usuário ou senha incorretos.')

        # # # Passo 2: Usuário e senha ok, mas falta 2FA
        if self.require_2fa:
            if self.auth_reset_views:
                self._request_2fa_reset(col2)
            
            self._component_require2fa()

        return self._get_user_data()
    
    def check_credentials(self, username: str, password: str) -> bool:
        df_user = Authenticate.get_active_user_by_username(username)
        if df_user.empty:
            self._clear_session_and_cookie(None)
            return False

        if self.limit_login_fail:
            lockout_until = df_user['lockout_until'][0]
            if lockout_until and datetime.utcnow() < pd.to_datetime(lockout_until):
                st.error("Conta bloqueada devido a múltiplas tentativas de login falhadas. Tente novamente mais tarde.")
                return False

        if not self.check_password(password, df_user['password'][0]):
            if self.limit_login_fail:
                failed_attempts = int(df_user['failed_attempts'][0]) + 1
                if failed_attempts >= self.max_login_attempts:
                    # Bloquear conta
                    execute_query('''
                        UPDATE TbUsuarioStreamlit
                        SET failed_attempts = :failed_attempts,
                            lockout_until = :lockout_until
                        WHERE username = :username
                    ''', params={
                        'failed_attempts': failed_attempts,
                        'lockout_until': datetime.utcnow() + timedelta(minutes=self.lockout_time),
                        'username': username
                    })
                    st.error("Conta bloqueada devido a múltiplas tentativas de login falhadas. Tente novamente mais tarde.")
                else:
                    execute_query('''
                        UPDATE TbUsuarioStreamlit
                        SET failed_attempts = :failed_attempts
                        WHERE username = :username
                    ''', params={
                        'failed_attempts': failed_attempts,
                        'username': username
                    })
                    st.error(f"Usuário ou senha incorretos. {self.max_login_attempts - failed_attempts} tentativas restantes.")
            return False

        execute_query('''
            UPDATE TbUsuarioStreamlit
            SET failed_attempts = 0,
                lockout_until = NULL
            WHERE username = :username
        ''', params={'username': username})

        st.session_state['user_id'] = df_user['id'][0]
        st.session_state['username'] = df_user['username'][0]
        st.session_state['name'] = str(df_user['name'][0]).title()
        st.session_state['role'] = df_user['role'][0]
        st.session_state['email'] = df_user['email'][0]
        st.session_state['authentication_status'] = True

        if self.require_2fa:
            st.session_state['authenticated_2fa'] = False
        else:
            st.session_state['authenticated_2fa'] = True

        return True
    
    @staticmethod
    def generate_device_fingerprint(headers) -> str:
        
        """Gera um fingerprint baseado no User-Agent e no endereço IP."""
        data = (
            headers.get('User-Agent', ''),
            headers.get('Accept-Language', ''),
            headers.get('Origin', ''),
            headers.get('Host', ''),
            headers.get('Sec-Gpc', ''),
            headers.get('Accept-Encoding', ''),
            headers.get('Accept', ''),
            headers.get('X-Real-Ip', ''),
        )
        
        return hashlib.sha256(''.join(data).encode()).hexdigest()
    
    @staticmethod
    def password_validation(password: str, errors: list) -> list:
        # Validação da força da senha
        if len(password) < 8:
            errors.append("A senha deve ter pelo menos 8 caracteres.")
        if not any(char.isupper() for char in password):
            errors.append("A senha deve conter pelo menos uma letra maiúscula.")
        if not any(char.islower() for char in password):
            errors.append("A senha deve conter pelo menos uma letra minúscula.")
        if not any(char.isdigit() for char in password):
            errors.append("A senha deve conter pelo menos um número.")
        if not any(char in "!@#$%^&*()-_=+[]{}|;:'\",.<>?/~`" for char in password):
            errors.append("A senha deve conter pelo menos um caractere especial (!@#$%^&*()-_=+[]{}|;:'\",.<>?/~`).")
        
        return errors
    
    @staticmethod
    def email_validation(email: str, errors: list) -> list:
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append("O email informado é inválido. Certifique-se de usar um formato válido (ex: exemplo@dominio.com).")
        return errors
    
    @staticmethod
    def role_validation(role: str, errors: list) -> list:
        if not role in ROLES:
            errors.append(f"Somente são permitidas as opçoes: {ROLES}")
        return errors
    
    @staticmethod
    def username_validation(username: str, errors: list) -> list:
        if not re.match(r'^[a-zA-Z0-9_-]{3,30}$', username):
            errors.append("O nome de usuário deve ter entre 3 e 30 caracteres e pode conter apenas letras, números, '_' ou '-'.")
        return errors
    
    @staticmethod
    def user_validation(username: str, password: str, email: str) -> dict:
        """
        Valida o nome de usuário, a força da senha e o formato do email.
        
        Args:
            username (str): O nome de usuário a ser validado.
            password (str): A senha a ser validada.
            email (str): O email a ser validado.
        
        Returns:
            dict: Um dicionário com os resultados da validação.
        """
        errors = []
        
        # Validação do nome de usuário
        errors = Authenticate.username_validation(username, errors)
        
        # Validação da força da senha
        errors = Authenticate.password_validation(password, errors)

        # Validação do email
        errors = Authenticate.email_validation(email, errors)
        
        return Authenticate.format_errors(errors)
    
    @staticmethod
    def format_errors(errors: list) -> dict:
        # Retorna os erros ou uma mensagem de sucesso
        if errors:
            return {"valid": False, "errors": errors}
        return {"valid": True, "message": "Nome de usuário, senha e email são válidos."}
    
    @staticmethod
    def clean_expired_sessions():
        execute_query('''
            DELETE FROM TbSessaoStreamlit
            WHERE expires_at < :current_time
        ''', params={'current_time': datetime.utcnow()})
        logger.info("Sessões expiradas foram removidas.")

    @staticmethod
    def clean_expired_tokens():
        execute_query('''
            UPDATE TbUsuarioStreamlit
            SET activation_token = NULL, activation_token_expiry = NULL
            WHERE activation_token_expiry < :current_time
        ''', params={'current_time': datetime.utcnow()})
        execute_query('''
            UPDATE TbUsuarioStreamlit
            SET reset_password_token = NULL, reset_password_token_expiry = NULL
            WHERE reset_password_token_expiry < :current_time
        ''', params={'current_time': datetime.utcnow()})
        execute_query('''
            UPDATE TbUsuarioStreamlit
            SET reset_tfa_token = NULL, reset_tfa_token_expiry = NULL
            WHERE reset_tfa_token_expiry < :current_time
        ''', params={'current_time': datetime.utcnow()})
        logger.info("Tokens expirados foram removidos.")
    
    @staticmethod
    def generate_session_id() -> str:
        """Gera um session_id único e seguro."""
        return str(uuid.uuid4())
    
    @staticmethod
    def hash(password) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    @staticmethod
    def check_password(password: str, hashed_pw: str) -> bool:
        try:
            resultado = bcrypt.checkpw(password.encode(), hashed_pw.encode())
            return resultado
        except:
            return

    @staticmethod
    def generate_activation_token(username: str, activation_token_expiry=24) -> tuple:
        """
        Gera um token de ativação e o armazena no banco.
        
        Args:
            username (str): Nome de usuário.
            activation_token_expiry (int): Expiração do token em horas.
        
        Returns:
            tuple: Token e data de expiração.
        """
        token = secrets.token_urlsafe(64)
        expiry = datetime.utcnow() + timedelta(hours=activation_token_expiry)

        execute_query('''
            UPDATE TbUsuarioStreamlit
            SET activation_token = :token,
                activation_token_expiry = :expiry
            WHERE username = :username
        ''', params={'token': token, 'expiry': expiry, 'username': username})
        
        return token, expiry
    
    @staticmethod
    def get_active_user_by_username(username: str) -> pd.DataFrame:
        # Ajuste a query conforme a necessidade
        return pd.read_sql(
            text('''
                SELECT *
                FROM TbUsuarioStreamlit
                WHERE username = :username 
                AND active = 1
                ORDER BY id DESC
            '''),
            engine, params={'username': username}
        ).head(1)
        
    @staticmethod
    def get_existant_user_by_username(username: str) -> pd.DataFrame:
        # Ajuste a query conforme a necessidade
        return pd.read_sql(
            text('''
                SELECT *
                FROM TbUsuarioStreamlit
                WHERE username = :username 
                ORDER BY id DESC
            '''),
            engine, params={'username': username}
        ).head(1)
    
    @staticmethod
    def get_active_user_by_id(user_id: int) -> pd.DataFrame:
        if user_id:
            return pd.read_sql(
                text('''
                    SELECT *
                    FROM TbUsuarioStreamlit
                    WHERE id = :user_id
                    AND active = 1
                    ORDER by id DESC
                '''),
                engine, params={'user_id': int(user_id)}
            ).head(1)
        else:
            return pd.DataFrame()

    @staticmethod
    def get_all_users() -> pd.DataFrame:
        df = pd.read_sql(text(f'''
            SELECT * FROM TbUsuarioStreamlit 
            ORDER by id DESC
            '''), engine)
        return df
    
    @staticmethod
    def get_all_active_users() -> pd.DataFrame:
        df = pd.read_sql(text(f'''
            SELECT * FROM TbUsuarioStreamlit 
            WHERE active = 1
            ORDER by id DESC
            '''), engine)
        return df
    
    @staticmethod
    def insert_user(
        name: str, 
        username: str,
        password: str,
        email: str,
        role: str,
        active: bool = True,
        ) -> None:
        validate = Authenticate.user_validation(
            username=username,
            password=password,
            email=email
        )
        if not validate['valid']:
            raise ValidationError(validate['errors'])
        if Authenticate.get_existant_user_by_username(username).empty:
            hashed_pass = Authenticate.hash(password)
            execute_query(f'''
                INSERT INTO TbUsuarioStreamlit
                (
                    name,
                    email,
                    username,
                    password,
                    change_date,
                    role,
                    active,
                    failed_attempts
                    )
                VALUES (
                    :name,
                    :email,
                    :username,
                    :password,
                    :change_date,
                    :role,
                    :active,
                    :failed_attempts
                )
            ''', params={
                'name': name.strip(),
                'email': email.strip(),
                'username': username.strip(),
                'password': hashed_pass,
                'change_date': datetime.now(),
                'active': active,
                'role': role,
                'failed_attempts': 0,
            })
        else:
            raise ValidationError(['Já existe um usuário com esse username.'])

    @staticmethod
    def update_dados(
        username: str,
        new_username: str = None,
        new_email: str = None,
        new_role: str = None,
        new_name: str = None
        ) -> None:
        '''
        update dados do usuario
        '''
        df_usuarios = Authenticate.get_all_users()
        df_usuario = df_usuarios[df_usuarios['username'] == username].copy()
        if new_username:
            df_new_usuario = df_usuarios[df_usuarios['username'] == new_username.strip()].copy()
            if not df_usuario.empty:
                if not df_new_usuario.empty and new_username.strip() != username:
                    raise ValidationError(['Já existe um usuário com esse username.'])
            else:
                raise ValidationError(['Não existe usuário com esse username.'])
                
        name = df_usuario['name'].values[0]
        email = df_usuario['email'].values[0]
        role = df_usuario['role'].values[0]
        
        if not new_username:
            new_username = username
        if not new_name:
            new_name = name
        if not new_email:
            new_email = email
        if not new_role:
            new_role = role
        
        errors = []
        
        errors = Authenticate.username_validation(new_username, errors)
        
        errors = Authenticate.email_validation(new_email, errors)
        
        errors = Authenticate.role_validation(new_role, errors)
        
        validate = Authenticate.format_errors(errors)
        
        if not validate['valid']:
            raise ValidationError(validate['errors'])
        
        execute_query(f'''
            UPDATE TbUsuarioStreamlit
            SET
                username = :username,
                email = :email,
                role = :role,
                name = :name,
                change_date = :change_date
            where username = :username_old
        ''', params={
            'username': new_username.strip(),
            'email': new_email.strip(),
            'role': new_role.strip(),
            'name': new_name.strip(),
            'change_date': datetime.now(),
            'username_old': username
        })
    
    @staticmethod
    def update_senha(username: str, new_password: str) -> None:
        df_usuarios = Authenticate.get_all_users()
        df_usuario = df_usuarios[df_usuarios['username'] == username].copy()
        if not df_usuario.empty:
            errors = []
        
            errors = Authenticate.password_validation(new_password, errors)
            
            validate = Authenticate.format_errors(errors)
            
            if not validate['valid']:
                raise ValidationError(validate['errors'])
                
            hashed_pass = Authenticate.hash(new_password)
            execute_query(f'''
                UPDATE TbUsuarioStreamlit
                SET
                    password = :password,
                    change_date = :change_date
                WHERE username = :username
            ''', params={
                'password': hashed_pass,
                'change_date': datetime.now(),
                'username': username,
            })
        else:
            raise ValidationError(['Não existe usuário com esse username.'])
    
    @staticmethod
    def delete_usuario(username: str) -> None:
        execute_query(f'''
            DELETE FROM TbUsuarioStreamlit
            WHERE 
                username = :username
        ''', params={
            'username': username,
        })

    @staticmethod
    def deactivate_user(username: str) -> None:
        execute_query(f'''
            UPDATE TbUsuarioStreamlit
            SET active = 0
            WHERE 
                username = :username
        ''', params={
            'username': username,
        })
        
    @staticmethod
    def activate_user(username: str) -> None:
        execute_query(f'''
            UPDATE TbUsuarioStreamlit
            SET active = 1
            WHERE 
                username = :username
        ''', params={
            'username': username,
        })

    @staticmethod
    def delete_secret(username: str) -> None:
        execute_query(f'''
            UPDATE TbUsuarioStreamlit
            SET secret_tfa = :secret
            WHERE 
                username = :username
        ''', params={
            'username': username,
            'secret': None,
        })
    
    @staticmethod
    def save_secret_to_db(username: str, secret: str) -> None:
        execute_query(f'''
            UPDATE TbUsuarioStreamlit
            SET secret_tfa = :secret
            WHERE 
                username = :username
        ''', params={
            'username': username,
            'secret': secret,
        })

    @staticmethod
    def revoke_session(session_id: str = None, username: str = None) -> None:
        # Remova a sessão do banco de dados
        query = '''
                DELETE FROM TbSessaoStreamlit
            '''
        params = {}
        if session_id:
            query+='''
                WHERE session_id = :session_id
            '''
            params['session_id'] = session_id
        
        if username:
            query_add = '''
                user_id in (
                    SELECT id from TbUsuarioStreamlit
                    WHERE username = :username
                )
            '''
            if 'WHERE'.lower() in query.lower():
                query+='and' + query_add
            
            query+='WHERE' + query_add
            
            params['username'] = username
        
        if not params:
            params = None
        
        execute_query(query, params=params)
    
    @staticmethod
    def generate_reset_tfa_token(username: str ,  reset_token_expiry: int = 1) -> tuple:
        '''reset_token_expiry horas'''
        token = secrets.token_urlsafe(64)
        expiry = datetime.utcnow() + timedelta(hours=reset_token_expiry)

        execute_query('''
            UPDATE TbUsuarioStreamlit
            SET reset_tfa_token = :token,
                reset_tfa_token_expiry = :expiry
            WHERE username = :username
        ''', params={
            'token': token,
            'expiry': expiry,
            'username': username
        })
        return token, expiry
    
    @staticmethod
    def generate_reset_password_token(username: str, reset_token_expiry: int = 1) -> tuple:
        '''reset_token_expiry horas'''
        token = secrets.token_urlsafe(64)
        expiry = datetime.utcnow() + timedelta(hours=reset_token_expiry)

        execute_query('''
            UPDATE TbUsuarioStreamlit
            SET reset_password_token = :token,
                reset_password_token_expiry = :expiry
            WHERE username = :username
        ''', params={
            'token': token,
            'expiry': expiry,
            'username': username
        })
        return token, expiry
    
    @staticmethod
    def get_all_sessions() -> pd.DataFrame:
        """Retorna as sessões ativas de um usuário."""
        df_sessions = pd.read_sql(
            text('''
                SELECT
                    u.username 
                    ,s.session_id
                    ,s.authenticated_2fa
                    ,s.created_at
                    ,s.expires_at
                FROM TbSessaoStreamlit as s
                LEFT JOIN TbUsuarioStreamlit as u on u.id = s.user_id 
                ORDER BY created_at DESC
            '''),
            engine
        )
        return df_sessions
    
    @staticmethod
    def get_active_sessions(user_id: int) -> pd.DataFrame:
        """Retorna as sessões ativas de um usuário."""
        df_sessions = pd.read_sql(
            text('''
                SELECT *
                FROM TbSessaoStreamlit
                WHERE user_id = :user_id
                AND expires_at > :current_time
                ORDER BY created_at ASC
            '''),
            engine, params={'user_id': user_id, 'current_time': datetime.utcnow()}
        )
        return df_sessions

    @staticmethod
    def get_session_by_id(session_id: str) -> dict:
        """Recupera dados da sessão do banco de dados."""
        df_session = pd.read_sql(
            text('''
                SELECT *
                FROM TbSessaoStreamlit
                WHERE session_id = :session_id
            '''),
            engine, params={'session_id': session_id}
        )
        if not df_session.empty:
            session = df_session.iloc[0].to_dict()

            # Gerar o fingerprint atual e comparar com o salvo
            current_fingerprint = Authenticate.generate_device_fingerprint(st.context.headers)

            if session['fingerprint'] != current_fingerprint:
                logger.warning("Fingerprint não corresponde. Sessão potencialmente comprometida.")
                return None  # Fingerprint não corresponde

            return {
                'session_id': session['session_id'],
                'user_id': session['user_id'],
                'authenticated_2fa': session['authenticated_2fa'],
                'created_at': session['created_at'],
                'expires_at': session['expires_at']
            }
        else:
            return None
    
    @staticmethod
    def get_user_permissions(username: str) -> pd.DataFrame:
        df = pd.read_sql(text(f'''
            SELECT * FROM TbPermissaoUsuariosStreamlit 
            WHERE username = :username
        '''), engine, params={'username': username})
        return df

    @staticmethod
    def get_all_permissions() -> pd.DataFrame:
        df = pd.read_sql(text(f'''
            SELECT * FROM TbPermissaoUsuariosStreamlit 
        '''), engine)
        return df

    @staticmethod
    def adicionar_permissao(username: str, app_name: str) -> None:
        u_permissions = Authenticate.get_user_permissions(username)
        df_user: pd.DataFrame = Authenticate.get_active_user_by_username(username)
        user_id = df_user['id'].values[0]
        if app_name not in u_permissions.app_name.to_list():
            df = pd.DataFrame([{
                'user_id': user_id,
                'username': username,
                'app_name': app_name,
            }])
            df['date'] = datetime.now()
            df.to_sql(
                name='TbPermissaoUsuariosStreamlit',
                con=engine,
                if_exists='append',
                index=False,
            )

    @staticmethod
    def remover_permissao(username: str, app_name: str) -> None:
        execute_query(f'''
            DELETE FROM TbPermissaoUsuariosStreamlit 
            WHERE username = :username
            AND app_name = :app_name
        ''', params={'username': username, 'app_name': app_name})

    @staticmethod
    def create_admin_if_not_exists() -> None:
        # Criar uma sessão para interagir com o banco
        session = Session(engine)

        try:
            # Verificar se já existe algum usuário no banco
            user_count = session.query(TbUsuarioStreamlit).count()
            if user_count == 0:
                # Se não houver nenhum usuário, cria um usuário admin
                logger.debug("Nenhum usuário encontrado. Criando o usuário admin...")
                
                # Criar um novo usuário admin com a senha "admin"
                admin_user = TbUsuarioStreamlit(
                    name="Admin",
                    email="admin@domain.com",
                    username="admin",
                    password=Authenticate.hash("admin"),  # Lembre-se de hashear a senha!
                    role="admin",
                    active=True,
                    change_date=datetime.utcnow()
                )
                
                session.add(admin_user)
                session.commit()

                # Log de sucesso
                logger.debug("Usuário admin criado com sucesso com a senha 'admin'.")
            else:
                logger.debug("Usuários já existem no banco de dados. Nenhuma ação necessária.")
        
        except Exception as e:
            logger.error(f"Erro ao tentar verificar ou criar o usuário admin: {e}")
        finally:
            # Fechar a sessão
            session.close()
    
    @staticmethod
    def get_user_apps_perms(username: str) -> list:
        return sorted(
            list(i for i in set(
                Authenticate.get_user_permissions(username)['app_name'].to_list()
            ) if i in settings.APP_NAMES))
    
    @staticmethod
    def send_reset_email(username: str, email: str, reset_url: str, reset_type: str) -> None:
        with SendMail() as mailer:
            mailer.subtype = 'plain'
            mailer.assunto = f'Redefinição de {reset_type}'
            mailer.destinatarios = [
                email,
            ]
            message = f"""
            
        Olá {username},

        Você solicitou a redefinição de {reset_type}. Clique no link abaixo para continuar:

        {reset_url}

        Este link é válido por 1 hora. Se você não solicitou isso, ignore este e-mail.
        
        """
            mailer.enviar_email(
                message,
            )
    
    @staticmethod
    def send_activation_email(username: str, email: str, activation_url: str) -> None:
        """
        Envia um e-mail com o link de ativação do usuário.
        
        Args:
            username (str): Nome de usuário.
            email (str): E-mail do usuário.
            activation_url (str): URL com o token de ativação.
        """
        with SendMail() as mailer:
            mailer.subtype = 'plain'
            mailer.assunto = 'Ativação de Conta'
            mailer.destinatarios = [email]
            message = f"""
            Olá {username},

            Bem-vindo! Para ativar sua conta, clique no link abaixo:

            {activation_url}

            Este link é válido por 24 horas. Se você não solicitou este e-mail, ignore-o.

            """
            mailer.enviar_email(message)
