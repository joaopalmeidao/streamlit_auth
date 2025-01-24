from datetime import datetime, timedelta
from math import e
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
from sqlalchemy import or_

from sqlalchemy import text
from streamlit_auth.core.enviar_email import SendMail
from streamlit_auth.core.database.manager import default_engine as engine
from streamlit_auth.config import settings
from .models import (
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

    def __init__(self, 
        secret_key: str,
        session_expiry_days: int = 7,
        require_2fa: bool = True,
        cookie_name: str = 'session',
        auth_reset_views = False,
        site_name = 'http://localhost:8501/',
        
        max_sessions=None
        
        ):
        self.cookie_name = cookie_name
        self.secret_key = secret_key
        self.session_expiry_days = session_expiry_days
        self.require_2fa = require_2fa  # Novo parâmetro para controlar o 2FA
        self.auth_reset_views = auth_reset_views  # Novo parâmetro para controlar o 2FA
        self.site_name = site_name
        
        self.cookie_manager = stx.CookieManager()
        
        self.max_sessions = max_sessions

        # Inicializa o session_state caso não exista
        self._initialize_session_state()

        # Checa e restaura a sessão a partir do cookie
        self._check_and_restore_session_from_cookie()

        if self.auth_reset_views:
            if not all(settings.EMAIL_URI_DATA.values()):
                logger.warning("Configurações de email estão incompletas. Funcionalidades de email podem não funcionar corretamente.")

    def _initialize_session_state(self):
        # Definição inicial das variáveis de sessão
        for k, v in self.defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v

    def create_admin_if_not_exists():
        # Criar uma sessão para interagir com o banco
        session = Session(engine)

        try:
            # Verificar se já existe algum usuário no banco
            user_count = session.query(TbUsuarioStreamlit).count()
            if user_count == 0:
                # Se não houver nenhum usuário, cria um usuário admin
                logger.info("Nenhum usuário encontrado. Criando o usuário admin...")
                
                # Criar um novo usuário admin com a senha "admin"
                admin_user = TbUsuarioStreamlit(
                    nome="Admin",
                    email="admin@domain.com",
                    username="admin",
                    password=Authenticate.hash("admin"),  # Lembre-se de hashear a senha!
                    role="admin",
                    ativo=True,
                    data_alteracao=datetime.utcnow()
                )
                
                session.add(admin_user)
                session.commit()

                # Log de sucesso
                logger.info("Usuário admin criado com sucesso com a senha 'admin'.")
            else:
                logger.info("Usuários já existem no banco de dados. Nenhuma ação necessária.")
        
        except Exception as e:
            logger.error(f"Erro ao tentar verificar ou criar o usuário admin: {e}")
        finally:
            # Fechar a sessão
            session.close()
    
    def hash(password):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    def _check_and_restore_session_from_cookie(self):
        """Lê o cookie session_id, busca a sessão no DB e restaura o estado do usuário se válido."""
        session_id = self.cookie_manager.get(self.cookie_name)
        
        if session_id:
            session_data = Authenticate._get_session_by_id(session_id)

            if session_data:
                if pd.to_datetime(session_data['expires_at']) > datetime.utcnow():
                    user_id = session_data['user_id']
                    authenticated_2fa = session_data['authenticated_2fa']

                    # Busca dados do usuário no DB
                    df_user = self._get_user_by_id(user_id)

                    if not df_user.empty:
                        # Atualiza session_state apenas se não estiver já autenticado
                        if not st.session_state['authentication_status']:
                            st.session_state['user_id'] = user_id
                            st.session_state['session_id'] = session_id
                            
                            st.session_state['username'] = df_user['username'][0]
                            st.session_state['name'] = str(df_user['nome'][0]).title()
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

    def _get_session_by_id(session_id: str):
        """Recupera dados da sessão do banco de dados."""
        try:
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
        except Exception as e:
            logger.error(f"Erro ao recuperar sessão: {e}")
            return None

    def _generate_session_id(self) -> str:
        """Gera um session_id único e seguro."""
        return str(uuid.uuid4())

    def generate_device_fingerprint(headers):
        
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
    
    def _get_active_sessions(self, user_id: int):
        """Retorna as sessões ativas de um usuário."""
        try:
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
        except Exception as e:
            logger.error(f"Erro ao obter sessões ativas: {e}")
            return pd.DataFrame()
    
    def _create_session(self, user_id: int, authenticated_2fa: bool) -> str:
        """Cria uma nova sessão no banco de dados e retorna o session_id."""
        if self.max_sessions:
            active_sessions = self._get_active_sessions(user_id)
            if len(active_sessions) >= self.max_sessions:
                # Revoga a sessão mais antiga
                oldest_session = active_sessions.iloc[0]
                Authenticate.revoke_session(session_id=oldest_session['session_id'])
                logger.debug(f"Limite de sessões atingido para o usuário {user_id}. Sessão antiga revogada.")
        
        session_id = self._generate_session_id()
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(days=self.session_expiry_days)

        # Gerar fingerprint do dispositivo
        fingerprint = Authenticate.generate_device_fingerprint(st.context.headers)

        try:
            with engine.begin() as con:
                con.execute(text('''
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
                '''), [{
                    'session_id': session_id,
                    'user_id': user_id,
                    'authenticated_2fa': authenticated_2fa,
                    'created_at': created_at,
                    'expires_at': expires_at,
                    'fingerprint': fingerprint
                }])
            return session_id
        except Exception as e:
            logger.error(f"Erro ao criar sessão: {e}")
            return None

    def _update_session_expiry(self, session_id: str):
        """Atualiza a data de expiração da sessão."""
        new_expires_at = datetime.utcnow() + timedelta(days=self.session_expiry_days)
        try:
            with engine.begin() as con:
                con.execute(text('''
                    UPDATE TbSessaoStreamlit
                    SET expires_at = :expires_at
                    WHERE session_id = :session_id
                '''), [{
                    'expires_at': new_expires_at,
                    'session_id': session_id
                }])
        except Exception as e:
            logger.error(f"Erro ao atualizar expiração da sessão: {e}")

    def _write_session_to_cookie(self, session_id: str):
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

    def _clear_session_and_cookie(self, session_id: str):
        """Limpa sessão e cookie ao fazer logout ou falha de autenticação."""
        logger.debug('Limpando sessão e cookie...')
        if self.cookie_name in self.cookie_manager.cookies:
            self.cookie_manager.delete(self.cookie_name) 
        try:
            with engine.begin() as con:
                con.execute(text('''
                    DELETE FROM TbSessaoStreamlit
                    WHERE session_id = :session_id
                '''), {'session_id': session_id})
        except Exception as e:
            logger.error(f"Erro ao deletar sessão: {e}")
        for key in self.defaults:
            st.session_state[key] = None
        st.session_state['logout'] = True
        st.session_state['authentication_status'] = False
        st.session_state['authenticated_2fa'] = False
        
    def login(self, form_name: str, container: st = st):
        """
        Realiza o fluxo completo de login:
        1. Se não autenticado: pede username e senha.
        2. Verifica credenciais. Se ok, verifica se necessita 2FA.
        3. Se 2FA não configurado, configura. Se configurado, pede código.
        4. Se 2FA verificado, gera sessão e salva no cookie.
        """

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
            
            username = login_form.text_input('Username', key='login_username_input').lower().strip()
            password = login_form.text_input('Password', type='password', key='login_password_input')
            
            if login_form.form_submit_button('Login'):
                if not username:
                    container.error("Preencha o campo Username.")

                with container.spinner('Carregando...'):
                    if self._check_credentials(username, password):
                        
                        self._component_create_session()
                        logger.debug(f"Usuário {username} autenticado com sucesso.")
                    else:
                        container.error('Usuário ou senha incorretos.')

        # # # Passo 2: Usuário e senha ok, mas falta 2FA
        if self.require_2fa:
            if self.auth_reset_views:
                self._request_2fa_reset(col2)
            
            self._component_require2fa()

        return self._get_user_data()
    
    def _component_require2fa(self):
        if st.session_state['authentication_status'] and not st.session_state['authenticated_2fa']:
            user_id = st.session_state['user_id']
            df_user = self._get_user_by_id(user_id)
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
    
    def _component_create_session(self):
        # Criar nova sessão
        session_id = self._create_session(int(st.session_state['user_id']), st.session_state['authenticated_2fa'])
        if session_id:
            st.session_state['session_id'] = session_id
            self._write_session_to_cookie(session_id)
        else:
            st.error("Erro ao criar sessão. Tente novamente.")

    def logout(self, button_name: str, container = st.sidebar, key: str = None, session_keys_to_delete=[]):
        if container.button(button_name, key=key):
            session_id = st.session_state['session_id']
            self._perform_logout(session_id)
            
            for i in session_keys_to_delete:
                if i in st.session_state.keys():
                    st.session_state[i] = None

    def _perform_logout(self, session_id: str):
        self._clear_session_and_cookie(session_id)

    def _check_credentials(self, username: str, password: str) -> bool:
        df_user = Authenticate._select_usuario(username)
        if df_user.empty:
            self._clear_session_and_cookie(None)
            return False

        if not self._check_password(password, df_user['password'][0]):
            self._clear_session_and_cookie(None)
            return False

        # Credenciais corretas
        st.session_state['user_id'] = df_user['id'][0]
        st.session_state['username'] = df_user['username'][0]
        st.session_state['name'] = str(df_user['nome'][0]).title()
        st.session_state['role'] = df_user['role'][0]
        st.session_state['email'] = df_user['email'][0]
        st.session_state['authentication_status'] = True

        if self.require_2fa:
            st.session_state['authenticated_2fa'] = False
        else:
            st.session_state['authenticated_2fa'] = True

        return True

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
        provisioning_uri = totp.provisioning_uri(username, issuer_name="saec-ct.apic3")

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

    def _autenticar_2fa(self, df_user: pd.DataFrame, secret_tfa: str, container=st) -> bool:
        username = df_user['username'][0]
        totp = pyotp.TOTP(secret_tfa)

        auth_form = container.form(f"2fa_auth_form")
        auth_form.subheader("Autenticação 2FA")
        otp = auth_form.text_input("Digite o código 2FA", key=f"2fa_auth_code_input")
        container.write("**Atenção:** Se você perdeu o acesso ao 2FA, por favor, entre em contato com o administrador do sistema.")
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

    def _update_session_authenticated_2fa(self, session_id: str, authenticated: bool):
        """Atualiza o campo authenticated_2fa na sessão."""
        with engine.begin() as con:
            con.execute(text('''
                UPDATE TbSessaoStreamlit
                SET authenticated_2fa = :authenticated
                WHERE session_id = :session_id
            '''), [{
                'authenticated': authenticated,
                'session_id': session_id
            }])

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
    
    def _check_password(self, password: str, hashed_pw: str) -> bool:
        try:
            resultado = bcrypt.checkpw(password.encode(), hashed_pw.encode())
            return resultado
        except:
            return

    def _select_usuario(username: str):
        """Busca o usuário pelo username e retorna como DataFrame."""
        session = Session(engine)
        try:
            user = session.query(TbUsuarioStreamlit).filter_by(username=username, ativo=True).first()
            if user:
                # Convertendo o objeto para DataFrame
                return pd.DataFrame([{
                    'id': user.id,
                    'nome': user.nome,
                    'email': user.email,
                    'username': user.username,
                    'password': user.password,
                    'role': user.role,
                    'ativo': user.ativo,
                    'data_alteracao': user.data_alteracao,
                    'secret_tfa': user.secret_tfa,
                    'reset_token': user.reset_token,
                    'reset_token_expiry': user.reset_token_expiry
                }])
            else:
                return pd.DataFrame()  # Caso não encontre o usuário
        except Exception as e:
            logger.error(f"Erro ao buscar usuário: {e}")
            return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro
        finally:
            session.close()

    def _get_user_by_id(self, user_id: int):
        if user_id:
            return pd.read_sql(
                text('''
                    SELECT *
                    FROM TbUsuarioStreamlit
                    WHERE id = :user_id
                    AND ATIVO = 1
                    order by id desc
                '''),
                engine, params={'user_id': int(user_id)}
            ).head(1)
        else:
            return pd.DataFrame()

    def select_usuarios():
        with engine.begin() as con:
            df = pd.read_sql(text(f'''
                SELECT * FROM TbUsuarioStreamlit 
                WHERE role = 'admin'
                order by id desc
                '''), con)
        return df
    
    def select_usuarios_ativos():
        """Busca todos os usuários ativos com o papel 'admin' e retorna como DataFrame."""
        session = Session(engine)
        try:
            users = session.query(TbUsuarioStreamlit).filter_by(role='admin', ativo=True).all()
            if users:
                # Convertendo os resultados para DataFrame
                return pd.DataFrame([{
                    'id': user.id,
                    'nome': user.nome,
                    'email': user.email,
                    'username': user.username,
                    'password': user.password,
                    'role': user.role,
                    'ativo': user.ativo,
                    'data_alteracao': user.data_alteracao,
                    'secret_tfa': user.secret_tfa,
                    'reset_token': user.reset_token,
                    'reset_token_expiry': user.reset_token_expiry
                } for user in users])
            else:
                return pd.DataFrame()  # Retorna um DataFrame vazio caso não encontre
        except Exception as e:
            logger.error(f"Erro ao buscar usuários ativos: {e}")
            return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro
        finally:
            session.close()
        
    def insert_usuario(
        nome, username, password, email, role
    ):  
        df_usuarios = Authenticate.select_usuarios()
        if df_usuarios[df_usuarios['username'] == username].empty:
            hashed_pass = Authenticate.hash(password)
            with engine.begin() as con:
                con.execute(text(f'''
                    INSERT INTO TbUsuarioStreamlit
                    (NOME, EMAIL, USERNAME, PASSWORD, DATA_ALTERACAO, ROLE, ATIVO)
                    VALUES (
                        :NOME,
                        :EMAIL,
                        :USERNAME,
                        :PASSWORD,
                        :DATA_ALTERACAO,
                        :ROLE,
                        :ATIVO
                    )
                '''),[{
                    'NOME': nome.strip(),
                    'EMAIL': email.strip(),
                    'USERNAME': username.strip(),
                    'PASSWORD': hashed_pass[0],
                    'DATA_ALTERACAO': datetime.now(),
                    'ATIVO': 1,
                    'ROLE': role
                }])
        else:
            raise Exception('Já existe um usuário com esse username.')

    def update_dados(username, new_username=None, new_email=None, new_role=None, new_name=None):  
        df_usuarios = Authenticate.select_usuarios()
        df_usuario = df_usuarios[df_usuarios['username'] == username].copy()
        if new_username:
            df_new_usuario = df_usuarios[df_usuarios['username'] == new_username.strip()].copy()
            if not df_usuario.empty:
                if not df_new_usuario.empty and new_username.strip() != username:
                    raise Exception('Já existe um usuário com esse username.')
            else:
                raise Exception('Não existe usuário com esse username.')
                
        nome = df_usuario['nome'].values[0]
        email = df_usuario['email'].values[0]
        role = df_usuario['role'].values[0]
        
        if not new_username:
            new_username = username
        if not new_name:
            new_name = nome
        if not new_email:
            new_email = email
        if not new_role:
            new_role = role
        
        with engine.begin() as con:
            con.execute(text(f'''
                UPDATE TbUsuarioStreamlit
                SET
                    USERNAME = :USERNAME,
                    EMAIL = :EMAIL,
                    ROLE = :ROLE,
                    NOME = :NOME,
                    DATA_ALTERACAO = :DATA_ALTERACAO
                WHERE USERNAME = :USERNAME_OLD
            '''),[{
                'USERNAME': new_username.strip(),
                'EMAIL': new_email.strip(),
                'ROLE': new_role.strip(),
                'NOME': new_name.strip(),
                'DATA_ALTERACAO': datetime.now(),
                'USERNAME_OLD': username
            }])
        
    def update_senha(username, new_password):  
        df_usuarios = Authenticate.select_usuarios()
        df_usuario = df_usuarios[df_usuarios['username'] == username].copy()
        if not df_usuario.empty:
            hashed_pass = Authenticate.hash(new_password)
            with engine.begin() as con:
                con.execute(text(f'''
                    UPDATE TbUsuarioStreamlit
                    SET
                        PASSWORD = :PASSWORD,
                        DATA_ALTERACAO = :DATA_ALTERACAO
                    WHERE USERNAME = :USERNAME
                '''),[{
                    'PASSWORD': hashed_pass,
                    'DATA_ALTERACAO': datetime.now(),
                    'USERNAME': username,
                }])
        else:
            raise Exception('Não existe usuário com esse username.')
        
    def delete_usuario(username):
        with engine.begin() as con:
            con.execute(text(f'''
                DELETE FROM TbUsuarioStreamlit
                WHERE 
                    USERNAME = :USERNAME
            '''),[{
                'USERNAME': username,
            }])

    def desativar_usuario(username):
        with engine.begin() as con:
            con.execute(text(f'''
                UPDATE TbUsuarioStreamlit
                SET ATIVO = 0
                WHERE 
                    USERNAME = :USERNAME
            '''),[{
                'USERNAME': username,
            }])
            
    def ativar_usuario(username):
        with engine.begin() as con:
            con.execute(text(f'''
                UPDATE TbUsuarioStreamlit
                SET ATIVO = 1
                WHERE 
                    USERNAME = :USERNAME
            '''),[{
                'USERNAME': username,
            }])

    def delete_secret(username):
        with engine.begin() as con:
            con.execute(text(f'''
                UPDATE TbUsuarioStreamlit
                SET secret_tfa = :secret
                WHERE 
                    USERNAME = :USERNAME
            '''),[{
                'USERNAME': username,
                'secret': None,
            }])
    
    def save_secret_to_db(username, secret):
        with engine.begin() as con:
            con.execute(text(f'''
                UPDATE TbUsuarioStreamlit
                SET secret_tfa = :secret
                WHERE 
                    USERNAME = :USERNAME
            '''),[{
                'USERNAME': username,
                'secret': secret,
            }])
            
    def revoke_session(session_id=None, username=None):
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
                    select id from TbUsuarioStreamlit
                    where username = :username
                )
            '''
            if 'WHERE'.lower() in query.lower():
                query+='and' + query_add
            
            query+='WHERE' + query_add
            
            params['username'] = username
        
        if not params:
            params = None
        
        with engine.begin() as con:
            con.execute(text(query), params)
    
    def generate_reset_token(username, reset_token_expiry=1):
        '''reset_token_expiry horas'''
        token = secrets.token_urlsafe(64)
        expiry = datetime.utcnow() + timedelta(hours=reset_token_expiry)

        with engine.begin() as con:
            con.execute(text('''
                UPDATE TbUsuarioStreamlit
                SET reset_token = :token,
                    reset_token_expiry = :expiry
                WHERE username = :username
            '''), {
                'token': token,
                'expiry': expiry,
                'username': username
            })
        return token, expiry

    def _request_password_reset(self, container=st):
        with container:
            with st.expander('Solicitar Redefinição de Senha'):
                form = st.form('password_reset')
                username = form.text_input("Username")
                if form.form_submit_button("Enviar Link de Redefinição"):
                    if not username:
                        st.error('Preencha o username')
                        return
                    with st.spinner('Enviando...'):
                        with engine.begin() as con:
                            result = con.execute(text('''
                                SELECT email
                                FROM TbUsuarioStreamlit
                                WHERE username = :username
                            '''), {'username': username}).fetchone()

                        if result:
                            email = result[0]
                            token, _ = Authenticate.generate_reset_token(username)
                            reset_url = f"{self.site_name}?password_token={token}"
                            Authenticate.send_reset_email(username, email, reset_url, "Senha")
                        st.success("Um link de redefinição de senha foi enviado para o seu e-mail.")
    
    def _reset_password(self, container=st):
        token = st.query_params.get('password_token')
        if not token:
            return
        
        with engine.begin() as con:
            result = con.execute(text('''
                SELECT username, reset_token_expiry
                FROM TbUsuarioStreamlit
                WHERE reset_token = :token
            '''), {'token': token}).fetchone()

        st.title("Redefinir Senha")
        if not result:
            st.error("Token inválido.")
            st.query_params.clear()
            return

        username, expiry = result
        if datetime.utcnow() > expiry:
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

                with engine.begin() as con:
                    con.execute(text('''
                        UPDATE TbUsuarioStreamlit
                        SET password = :password,
                            reset_token = NULL,
                            reset_token_expiry = NULL
                        WHERE username = :username
                    '''), {'password': hashed_pass, 'username': username})

                container.success("Senha redefinida com sucesso!")
                st.query_params.clear()
                st.rerun()
        else:
            st.stop()
    
    def _request_2fa_reset(self, container=st):
        with container:
            if self.require_2fa:
                with st.expander('Solicitar Redefinição de 2FA'):
                    form = st.form('2fa_reset')
                    username = form.text_input("Username")
                    if form.form_submit_button("Enviar Link de Redefinição"):
                        if not username:
                            st.error('Preencha o username')
                            return
                        with st.spinner('Enviando...'):
                            with engine.begin() as con:
                                result = con.execute(text('''
                                    SELECT email
                                    FROM TbUsuarioStreamlit
                                    WHERE username = :username
                                '''), {'username': username}).fetchone()

                            if result:
                                email = result[0]
                                token, _ = Authenticate.generate_reset_token(username)
                                reset_url = f"{self.site_name}?2fa_token={token}"
                                Authenticate.send_reset_email(username, email, reset_url, "2FA")
                            st.success("Um link de redefinição de 2FA foi enviado para o seu e-mail.")
        
    def _reset_2fa(self, container=st):
        if self.require_2fa:
            token = st.query_params.get('2fa_token')
            if not token:
                return

            with engine.begin() as con:
                result = con.execute(text('''
                    SELECT username, reset_token_expiry
                    FROM TbUsuarioStreamlit
                    WHERE reset_token = :token
                '''), {'token': token}).fetchone()

            if not result:
                st.error("Token inválido.")
                st.query_params.clear()
                return

            st.title("Redefinir 2FA")
            username, expiry = result
            if datetime.utcnow() > expiry:
                st.error("Token expirado.")
                st.query_params.clear()
                return

            container.success(f"Bem-vindo, {username}. Redefina o 2FA abaixo.")

            if container.button("Redefinir 2FA"):
                with engine.begin() as con:
                    con.execute(text('''
                        UPDATE TbUsuarioStreamlit
                        SET secret_tfa = NULL,
                            reset_token = NULL,
                            reset_token_expiry = NULL
                        WHERE username = :username
                    '''), {'username': username})

                st.success("2FA redefinido com sucesso! Você será solicitado a configurar novamente ao fazer login.")
                st.query_params.clear()
                st.rerun()
            else:
                st.stop()
    
    def get_user_permissions(username):
        with engine.begin() as con:
            df = pd.read_sql(text(f'''
                SELECT * FROM TbPermissaoUsuariosStreamlit 
                WHERE username = :username
            '''), con, params=[{'username': username}])
        return df

    def get_all_permissions():
        with engine.begin() as con:
            df = pd.read_sql(text(f'''
                SELECT * FROM TbPermissaoUsuariosStreamlit 
            '''), con)
        return df

    def adicionar_permissao(username, app_name):
        u_permissions = Authenticate.get_user_permissions(username)
        df_user: pd.DataFrame = Authenticate._select_usuario(username)
        
        user_id = df_user['id'].values[0]
        
        if app_name not in u_permissions.app_name.to_list():
            df = pd.DataFrame([{
                'user_id': user_id,
                'username': username,
                'app_name': app_name,
            }])
            df['data'] = datetime.now()
            df.to_sql(
                name='TbPermissaoUsuariosStreamlit',
                con=engine,
                if_exists='append',
                index=False,
            )

    def remover_permissao(username, app_name):
        with engine.begin() as con:
            con.execute(text(f'''
                DELETE FROM TbPermissaoUsuariosStreamlit 
                WHERE username = :username
                AND app_name = :app_name
            '''), [{'username': username, 'app_name': app_name}])
    
    def send_reset_email(username, email, reset_url, reset_type):
        mail = SendMail()
        
        mail.subtype = 'plain'
        
        mail.assunto = f'Redefinição de {reset_type}'
        
        mail.destinatarios = [
            email,
        ]
        
        message = f"""
        
    Olá {username},

    Você solicitou a redefinição de {reset_type}. Clique no link abaixo para continuar:

    {reset_url}

    Este link é válido por 1 hora. Se você não solicitou isso, ignore este e-mail.
    
    """
        
        mail.enviar_email(
            message,
        )
