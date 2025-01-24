import os
from setuptools import setup, find_packages

def read_requirements():
    """Lê as dependências do arquivo requirements.txt"""
    with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as f:
        return f.read().splitlines()

def read_long_description():
    # Carrega o README principal
    with open("readme/en.md", encoding="utf-8") as f:
        en_content = f.read()
    
    # Inclui link para o README em português
    pt_link = "\n\n## 🌎 Other Languages\n\n- [Português](https://github.com/joaopalmeidao/streamlit_auth/blob/main/readme/pt-BR.md)\n"
    
    return en_content + pt_link

setup(
    name="streamlit_auth_mfa",
    version="3.1.0",
    description="Uma biblioteca para autenticação segura com Streamlit e 2FA.",
    long_description=read_long_description(), 
    long_description_content_type="text/markdown",
    author="João Pedro Almeida Oliveira",
    author_email="jp080496@gmail.com",
    url="https://github.com/joaopalmeidao/streamlit_auth",
    packages=find_packages(),
    install_requires=read_requirements(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)
