import os
from setuptools import setup, find_packages

def read_requirements():
    """Lê as dependências do arquivo requirements.txt"""
    with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as f:
        return f.read().splitlines()

# Carregar o README.md para usar como descrição longa no PyPI
def read_long_description():
    with open("README.md", encoding="utf-8") as f:
        return f.read()

setup(
    name="streamlit-auth-mfa",  # Nome do seu pacote
    version="1.0.0",  # Versão do seu pacote
    description="Uma biblioteca para autenticação segura com Streamlit e 2FA.",
    long_description=read_long_description(),  # Descrição longa no PyPI
    long_description_content_type="text/markdown",  # Tipo de conteúdo do README
    author="João Pedro Almeida Oliveira",
    author_email="jp080496@gmail.com",
    url="https://github.com/joaopalmeidao/streamlit_auth",  # URL do repositório GitHub ou outro
    packages=find_packages(),  # Pacotes que você deseja incluir no PyPI
    install_requires=read_requirements(),  # Dependências do seu pacote
    classifiers=[  # Informações sobre o pacote para PyPI
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",  # Versão mínima do Python
)
