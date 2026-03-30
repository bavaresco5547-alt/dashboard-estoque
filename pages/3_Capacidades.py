
import streamlit as st
import pandas as pd
from services.database import read_table, save_capacities

st.title("3️⃣ Capacidades por filial")

df = read_table("filiais_capacidade")
if df.empty:
    df = pd.DataFrame(columns=[
        "filial", "cod_filial", "capacidade_congelado",
        "capacidade_resfriado", "capacidade_ambiente", "capacidade_total"
    ])

edited = st.data_editor(df, use_container_width=True, num_rows="dynamic")

if st.button("Salvar capacidades", type="primary"):
    edited = edited.copy()
    for col in ["capacidade_congelado", "capacidade_resfriado", "capacidade_ambiente"]:
        edited[col] = pd.to_numeric(edited[col], errors="coerce").fillna(0)
    edited["capacidade_total"] = (
        edited["capacidade_congelado"] +
        edited["capacidade_resfriado"] +
        edited["capacidade_ambiente"]
    )
    edited["filial"] = edited["filial"].astype(str).str.strip().str.upper()
    edited["cod_filial"] = edited["cod_filial"].astype(str).str.strip().str.upper()

    save_capacities(edited)
    st.success("Capacidades salvas com sucesso.")
