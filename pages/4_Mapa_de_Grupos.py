
import streamlit as st
import pandas as pd
from services.database import read_table, save_group_map

st.title("4️⃣ Mapa de grupos")

df = read_table("mapa_grupos")
if df.empty:
    df = pd.DataFrame(columns=["grupo_original", "tipo_estoque"])

edited = st.data_editor(
    df,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "tipo_estoque": st.column_config.SelectboxColumn(
            "tipo_estoque",
            options=["CONGELADO", "RESFRIADO", "AMBIENTE"],
        )
    }
)

if st.button("Salvar mapa de grupos", type="primary"):
    edited["grupo_original"] = edited["grupo_original"].astype(str).str.strip().str.upper()
    edited["tipo_estoque"] = edited["tipo_estoque"].astype(str).str.strip().str.upper()
    save_group_map(edited)
    st.success("Mapa de grupos salvo com sucesso.")
