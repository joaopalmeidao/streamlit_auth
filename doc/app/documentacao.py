import streamlit as st
import logging
import base64
import pandas as pd

from streamlit_auth.authentication import (
    Authenticate,
    user_manager_main_page,
    user_profile_page,
)
from streamlit_auth.config import settings


logger = logging.getLogger(settings.MAIN_LOGGER_NAME)


def doc_page():
    st.title("📄 Documentação da Streamlit Auth Library")
    
    st.sidebar.title("Navegação")
    secoes = [
        "📝 Descrição",
        "🚀 Instalação",
        "⚙️ Configuração",
        "💡 Funcionalidades",
        "📚 Modelos de Banco de Dados",
        "📧 Envio de E-mails",
        "🔧 Exemplos de Uso",
        "🎨 Telas Prontas",
        "📦 PyPI",
        "🤝 Contribuição",
        "📜 Licença",
        "📞 Contato",
    ]

    secao = st.sidebar.radio("Ir para", secoes)
    
    if secao == "📝 Descrição":
        st.header("📝 Descrição")
        st.markdown("""
        A **Streamlit Auth Library** é uma biblioteca que adiciona autenticação robusta e recursos de gerenciamento de usuários ao seu aplicativo Streamlit. Com suporte para autenticação de dois fatores (2FA), permissões e gerenciamento de sessões, ela é ideal para aplicativos que requerem segurança e controle de acesso.

        ### Principais Características
        - **Autenticação Segura**: Login com verificação de senha utilizando bcrypt.
        - **Autenticação de Dois Fatores (2FA)**: Adicione uma camada extra de segurança com TOTP.
        - **Gerenciamento de Usuários**: Cadastro, edição, ativação/desativação e remoção de usuários.
        - **Roles e Permissões**: Controle de acesso baseado em papéis e permissões específicas por aplicativo.
        - **Sessões Gerenciadas**: Controle de sessões com expiração automática e proteção contra sessões comprometidas.
        - **Logs de Ações**: Registro detalhado das ações dos usuários para auditoria.
        - **Integração com E-mail**: Envio de e-mails para ativação de contas, redefinição de senha e 2FA.
        """)

    elif secao == "🚀 Instalação":
        st.header("🚀 Instalação")
        st.markdown("""
        Siga os passos abaixo para instalar a **Streamlit Auth Library**:

        ## PyPI
        
        1. **Instale a Biblioteca via PyPI**
        
            ```bash
            pip install streamlit-auth-mfa
            ```
        
        ## Clonar Repositório
        
        1. **Clone o Repositório**
        
            ```bash
            git clone https://github.com/joaopalmeidao/streamlit-auth.git
            cd streamlit-auth
            ```
        
        2. **Crie um Ambiente Virtual**
        
            É recomendado usar um ambiente virtual para isolar as dependências:
            
            ```bash
            python -m venv venv
            source venv/bin/activate  # No Windows: venv\\Scripts\\activate
            ```
        
        3. **Instale as Dependências**
        
            Instale as bibliotecas necessárias com:
        
            ```bash
            pip install -r requirements.txt
            ```
        
        """)

    elif secao == "⚙️ Configuração":
        st.header("⚙️ Configuração")
        st.markdown("""
        A biblioteca utiliza variáveis de ambiente e arquivos de configuração para personalizar comportamentos. Certifique-se de configurar os arquivos necessários antes de usar a biblioteca.

        ### Arquivo `.env`

        As variáveis de ambiente devem ser configuradas no arquivo `.env`:

        ```env
        DEBUG=True
        LOG_LEVEL=DEBUG

        # Banco de Dados
        DB_URI=sqlite:///db.sqlite3

        # E-mail
        EMAIL_HOST=smtp.gmail.com
        EMAIL_PORT=587
        EMAIL=seu_email@gmail.com
        EMAIL_PASSWORD=sua_senha

        # Configuração de Apps
        APP_NAMES_FILE=config/app_names.json
        SITE_NAME=http://localhost:8501/
        SECRET_KEY=SuaChaveSecretaAqui
        ```

        ### Arquivos de Configuração

        **config/app_names.json**

        Defina os nomes dos aplicativos para os quais você gerencia permissões:

        ```json
        {
            "APP_NAMES": ["App1", "App2", "App3"]
        }
        ```
        
        """)

    elif secao == "💡 Funcionalidades":
        st.header("💡 Funcionalidades")
        st.markdown("""
        A **Streamlit Auth Library** oferece uma ampla gama de funcionalidades para garantir a segurança e o gerenciamento eficaz dos usuários em seus aplicativos Streamlit.

        ### Autenticação
        - **Username e Senha**: Utiliza bcrypt para hashing seguro das senhas.
        - **2FA Opcional**: Adicione uma camada extra de segurança com TOTP (Time-based One-Time Password).
        - **Gerenciamento de Sessões**: Rastreamento e controle de logins com expiração automática.
        - **Ativação de Usuário**: Suporte para ativar contas de usuários via link enviado por e-mail.

        ### Gerenciamento de Usuários e Permissões
        - **Gerenciar Usuários**: Adicione, edite ou remova usuários.
        - **Gerenciar Permissões**: Controle o acesso por aplicativo, definindo quais usuários têm permissão para quais aplicativos.

        ### Integração com E-mail
        - **Envio de E-mails Transacionais**: Envio de e-mails para ativação de contas, redefinição de senha e 2FA.
        - **Suporte para Anexos e Imagens**: Inclua anexos e imagens embutidas nos e-mails enviados.
        """)

    elif secao == "📚 Modelos de Banco de Dados":
        st.header("📚 Modelos de Banco de Dados")
        
        st.markdown(f"""
        A biblioteca fornece modelos integrados para gerenciar usuários, sessões e permissões:

        ### `TbUsuarioStreamlit`

        Modelo para gerenciamento de usuários, contendo informações como nome, email, username, senha, roles e tokens para redefinição de senha e 2FA.

        ### `TbSessaoStreamlit`

        Modelo para rastreamento de sessões, armazenando o `session_id`, `user_id`, status do 2FA, data de criação, expiração e fingerprint do dispositivo.

        ### `TbPermissaoUsuariosStreamlit`

        Modelo para controle de permissões, definindo quais aplicativos cada usuário tem acesso.

        #### Código dos Modelos

        ```python
        from datetime import datetime
        from sqlalchemy.orm import declarative_base, relationship
        from sqlalchemy import (
            Column,
            Integer,
            String,
            Boolean,
            DateTime,
            ForeignKey,
        )
        from streamlit_auth.core.database.manager import default_engine as engine

        ROLES = ["user", "admin"]
        Base = declarative_base()

        class TbUsuarioStreamlit(Base):
            __tablename__ = 'TbUsuarioStreamlit'

            id = Column(Integer, primary_key=True, autoincrement=True)
            name = Column(String(255)) 
            email = Column(String(255))
            username = Column(String(64), unique=True, nullable=False)
            password = Column(String)
            change_date = Column(DateTime, default=datetime.utcnow)
            active = Column(Boolean, default=True)
            role = Column(String(32))
            secret_tfa = Column(String(255))
            reset_password_token = Column(String(255))
            reset_password_token_expiry = Column(DateTime)
            reset_tfa_token = Column(String(255))
            reset_tfa_token_expiry = Column(DateTime)
            activation_token = Column(String(255))
            activation_token_expiry = Column(DateTime)

            sessions = relationship('TbSessaoStreamlit', back_populates='user', cascade="all, delete-orphan")
            perms = relationship('TbPermissaoUsuariosStreamlit', back_populates='user')

        class TbSessaoStreamlit(Base):
            __tablename__ = 'TbSessaoStreamlit'

            session_id = Column(String(128), primary_key=True, unique=True, nullable=False)
            user_id = Column(Integer, ForeignKey(TbUsuarioStreamlit.id), nullable=False)
            authenticated_2fa = Column(Boolean, default=False, nullable=False)
            created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
            expires_at = Column(DateTime, nullable=False)
            fingerprint = Column(String(255), nullable=False)

            user = relationship(TbUsuarioStreamlit, back_populates='sessions')

        class TbPermissaoUsuariosStreamlit(Base):
            __tablename__ = 'TbPermissaoUsuariosStreamlit'

            id = Column(Integer, primary_key=True, autoincrement=True)
            user_id = Column(Integer, ForeignKey(TbUsuarioStreamlit.id), nullable=False)
            username = Column(String(64), nullable=False)
            app_name = Column(String, nullable=False)
            date = Column(DateTime, default=datetime.now)

            user = relationship(TbUsuarioStreamlit, back_populates='perms')

        Base.metadata.create_all(engine)
        ```
        """)

    elif secao == "📧 Envio de E-mails":
        st.header("📧 Envio de E-mails")
        st.markdown("""
        A biblioteca inclui uma classe `SendMail` que facilita o envio de e-mails com suporte para anexos e imagens embutidas.

        ### Classe `SendMail`

        #### Atributos
        - `subtype`: Tipo de conteúdo do e-mail (`'plain'` ou `'html'`).
        - `assunto`: Assunto do e-mail.
        - `destinatarios`: Lista de destinatários.
        - `copia`: Lista de cópias.
        - `copia_oculta`: Lista de cópias ocultas.

        #### Métodos Principais
        - `enviar_email(mensagem, arquivos={}, imagens={})`: Envia o e-mail com a mensagem, anexos e imagens especificadas.

        #### Exemplo de Uso

        ```python
        from streamlit_auth.core.enviar_email import SendMail

        with SendMail(
            host="smtp.gmail.com",
            port=587,
            email="seu_email@gmail.com",
            password="sua_senha",
        ) as mailer:
            mailer.destinatarios = ["destinatario@gmail.com"]
            mailer.assunto = "Teste de Envio de E-mail"
            mensagem = "
            Olá,

            Este é um e-mail de teste enviado pela Streamlit Auth Library.

            Atenciosamente,
            Seu Nome
            "
            mailer.enviar_email(mensagem)
        ```
        """)

    elif secao == "🔧 Exemplos de Uso":
        st.header("🔧 Exemplos de Uso")
        st.markdown("""
        Abaixo estão exemplos de como utilizar a **Streamlit Auth Library** em seus projetos.

        ### Autenticação Simples

        ```python
        from streamlit_auth.authentication import Authenticate
        import streamlit as st

        authenticator = Authenticate(
            secret_key='minha_chave_secreta',
            session_expiry_days=7,
            require_2fa=True
        )

        user_data = authenticator.login("Login")

        if user_data['authentication_status']:
            st.success(f"Bem-vindo, {user_data['name']}!")
            authenticator.logout("Sair")
        else:
            st.error("Autenticação falhou. Verifique suas credenciais.")
        ```

        ### Autenticação Completa com Gerenciamento

        ```python
        import streamlit as st
        from streamlit_auth.authentication import Authenticate, user_manager_main_page, user_profile_page

        TITLE = "Streamlit Authenticate"

        def main():
            st.set_page_config(page_title=TITLE, layout='wide')

            authenticator = Authenticate(
                secret_key='123',
                session_expiry_days=7,
                require_2fa=False,
                auth_reset_views=True,
                site_name='http://localhost:8501/',
            )

            user_data = authenticator.login("Login")

            authentication_status = user_data['authentication_status']
            name = user_data['name']
            username = user_data['username']
            authenticated_2fa = user_data['authenticated_2fa']
            role = user_data['role']

            st.sidebar.write(TITLE)

            if not authentication_status:
                st.warning("Por favor, insira seu nome de usuário e senha.")
                authenticator.user_register_form()
                return

            if authentication_status and authenticated_2fa:
                st.success(f"Bem-vindo, {name}!")
                authenticator.logout("Logout")

                opcoes_admin = ['Gerenciar']
                opcoes_usuario = ['Perfil de Usuário']

                if role == 'admin':
                    user_permissions = opcoes_usuario + opcoes_admin
                else:
                    user_permissions = authenticator.get_user_apps_perms(username) + opcoes_usuario

                selected_option = st.sidebar.selectbox("Selecione uma opção:", user_permissions)

                if role == 'admin' and selected_option == "Gerenciar":
                    user_manager_main_page()

                if selected_option == "Perfil de Usuário":
                    user_profile_page(user_data)

        if __name__ == "__main__":
            main()
        ```

        ### Gerenciamento de Sessões

        ```python
        import streamlit as st
        from streamlit_auth.authentication import Authenticate, display_errors

        def session_manager_page():
            st.title("🔑 Gerenciar Sessões dos Usuários")

            df_sessoes = Authenticate.get_all_sessions()

            st.subheader("📋 Lista de Sessões Ativas")
            st.dataframe(df_sessoes, height=300, use_container_width=True, hide_index=True)

            st.subheader("🛠️ Revogar Sessão")
            selected_sessions = st.multiselect("Selecione uma sessão para revogar:", df_sessoes['session_id'])

            if st.button("Revogar Sessão Selecionada"):
                try:
                    for session_id in selected_sessions:
                        Authenticate.revoke_session(session_id=session_id)
                    st.success(f"Sessão(s) {selected_sessions} revogada(s) com sucesso!")
                    st.experimental_rerun()
                except Exception as e:
                    display_errors(e)
        ```
        """)

    elif secao == "🎨 Telas Prontas":
        st.header("🎨 Telas Prontas")
        st.markdown("""
        A seguir, estão as telas prontas disponíveis para visualização:

        ### Gerenciar Permissões
        ![Gerenciar Permissões](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/manage_perms.png?raw=True)

        ### Gerenciar Usuários
        ![Gerenciar Usuários](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/user_manager.png?raw=True)

        ### Gerenciar Sessões
        ![Gerenciar Sessões](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/session_manager.png?raw=True)

        ### Login Form
        ![Login Form](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/login_form.png?raw=True)

        ### 2FA Form
        ![2FA Form](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/mfa_form.png?raw=True)

        ### Reset Form
        ![Reset Forms](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/reset_forms.png?raw=True)

        ### Register Form
        ![Register Form](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/user_register.png?raw=True)

        ### User Activation Form
        ![User Activation Form](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/user_activation.png?raw=True)

        ### Perfil de Usuário
        ![Perfil de Usuário](https://github.com/joaopalmeidao/streamlit_auth/blob/main/doc/imgs/user_profile.png?raw=True)
        """)

    elif secao == "📦 PyPI":
        st.header("📦 PyPI")
        st.markdown("""
        A **Streamlit Auth Library** está disponível no PyPI. Você pode instalá-la diretamente usando o pip:

        [PyPI - streamlit-auth-mfa](https://pypi.org/project/streamlit-auth-mfa/)
        """)

    elif secao == "🤝 Contribuição":
        st.header("🤝 Contribuição")
        st.markdown("""
        Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e enviar pull requests para melhorar este projeto.

        ### Como Contribuir

        1. **Fork o Repositório**
        2. **Crie uma Branch de Feature**

            ```bash
            git checkout -b feature/nova-feature
            ```

        3. **Commit suas Mudanças**

            ```bash
            git commit -m "Adicionar nova feature"
            ```

        4. **Push para a Branch**

            ```bash
            git push origin feature/nova-feature
            ```

        5. **Abra um Pull Request**
        """)

    elif secao == "📜 Licença":
        st.header("📜 Licença")
        st.markdown("""
        Este projeto está licenciado sob a Licença MIT. Veja o arquivo [LICENSE](https://github.com/joaopalmeidao/streamlit_auth/blob/main/LICENCE) para mais detalhes.
        """)

    elif secao == "📞 Contato":
        st.header("📞 Contato")
        st.markdown("""
        Para dúvidas, sugestões ou suporte, entre em contato:

        - **Email**: jp080496@gmail.com
        - **GitHub**: [joaopalmeidao](https://github.com/joaopalmeidao)
        - **LinkedIn**: [João Paulo Almeida](https://www.linkedin.com/in/joaopalmeidao/)
        """)

