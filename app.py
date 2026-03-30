import streamlit as st
from services.database import init_db

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Dashboard de Estoque",
    page_icon="📦",
    layout="wide",
)

# =========================
# INICIALIZA BANCO
# =========================
init_db()

# =========================
# INTERFACE
# =========================
st.title("📦 Dashboard de Estoque")

st.markdown(
    """
    Sistema simples para:

    - subir 1 arquivo XLS/XLSX por dia  
    - processar o estoque automaticamente  
    - comparar com a capacidade por filial  
    - salvar histórico local em banco SQLite  
    - visualizar dashboard interativo  
    """
)

st.info("👉 Use o menu lateral para ir em **1_Upload** e processar o arquivo do dia.")

st.markdown(
    """
    ### 📂 Estrutura esperada do arquivo

    - Aba principal: `FJ Sistemas`  
    - Cabeçalho na linha 4  

    #### Colunas obrigatórias:
    - Filial  
    - Grupo  
    - Subgrupo  
    - Id Prod.  
    - Descricao  
    - Quantidade  
    - Peso Liquido  
    - Validade  
    - Producao  
    """
)

st.success("Sistema pronto para uso local 🚀")
