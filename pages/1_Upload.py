import streamlit as st
import pandas as pd
from services.database import init_db, save_upload, save_resumo, save_detalhe
from services.transform import prepare_data

st.title("📤 Upload do arquivo")

init_db()

file = st.file_uploader("Selecione o XLS/XLSX diário", type=["xls", "xlsx"])

if file:
    st.success(f"Arquivo selecionado: {file.name}")

    if st.button("Processar arquivo"):
        try:
            # LEITURA FIXA NO PADRÃO DO Pasta1.xlsx
            df = pd.read_excel(file, sheet_name="FJ Sistemas", header=3)

            df.columns = [str(c).strip().lower() for c in df.columns]

            df = df.rename(columns={
                "filial": "filial",
                "grupo": "grupo",
                "subgrupo": "subgrupo",
                "id prod.": "id_produto",
                "descricao": "descricao",
                "quantidade": "quantidade",
                "peso liquido": "peso_liquido",
                "validade": "validade",
                "producao": "producao",
            })

            colunas_obrigatorias = [
                "filial", "grupo", "subgrupo", "id_produto", "descricao",
                "quantidade", "peso_liquido", "validade", "producao"
            ]

            faltando = [c for c in colunas_obrigatorias if c not in df.columns]
            if faltando:
                raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(faltando)}")

            df = df[df["filial"].notna()].copy()

            capacidades = pd.read_csv("data/capacidades.csv")
            mapa_grupos = pd.read_csv("data/mapa_grupos.csv")

            data_ref = pd.Timestamp.today().strftime("%Y-%m-%d")

            detalhe, resumo = prepare_data(
                df=df,
                capacities_df=capacidades,
                group_map_df=mapa_grupos,
                data_referencia=data_ref,
                product_map_df=None
            )

            save_upload(file.name, data_ref)
            save_detalhe(detalhe)
            save_resumo(resumo)

            peso_total_lido = pd.to_numeric(df["peso_liquido"], errors="coerce").fillna(0).sum()

            st.success("Arquivo processado com sucesso 🚀")
            st.info(f"Peso total lido do arquivo: {peso_total_lido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

            with st.expander("Prévia do resumo gerado"):
                st.dataframe(resumo, use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")