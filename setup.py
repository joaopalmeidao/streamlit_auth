import os
from setuptools import setup, find_packages

def read_requirements():
    """Lê as dependências do arquivo requirements.txt"""
    with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as f:
        return f.read().splitlines()

def read_long_description():
    # Carrega o README principal
    with open("README.md", encoding="utf-8") as f:
        readme_content = f.read()
        
    with open("doc/readme/en.md", encoding="utf-8") as f:
        en_content = f.read()
    
    return readme_content + en_content

setup(
    name="streamlit_auth_mfa",
    version="4.1.0",
    description="A robust library for authentication with Streamlit, featuring 2FA, permissions, and session management.",
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
