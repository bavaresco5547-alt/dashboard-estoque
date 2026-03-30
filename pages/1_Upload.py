import streamlit as st
import pandas as pd
from services.database import init_db, save_upload, save_resumo, save_detalhe
from services.transform import prepare_data

st.title("📤 Upload do arquivo")

init_db()

file = st.file_uploader("Selecione o XLS/XLSX diário", type=["xls", "xlsx"])


def encontrar_aba_principal(xls: pd.ExcelFile) -> str:
    abas = xls.sheet_names

    # prioridade exata
    for nome in ["FJ Sistemas", "FJ SISTEMA", "FJ Sistemas ", "FJ SISTEMA "]:
        if nome in abas:
            return nome

    # prioridade por normalização
    abas_norm = {str(a).strip().upper(): a for a in abas}
    for chave in ["FJ SISTEMAS", "FJ SISTEMA"]:
        if chave in abas_norm:
            return abas_norm[chave]

    raise ValueError(
        "Não encontrei a aba principal de estoque. "
        f"Abas disponíveis no arquivo: {', '.join(abas)}"
    )


if file:
    st.success(f"Arquivo selecionado: {file.name}")

    if st.button("Processar arquivo"):
        try:
            # abre o Excel para inspecionar abas
            xls = pd.ExcelFile(file)
            aba_principal = encontrar_aba_principal(xls)

            # leitura da base principal
            # se for FJ Sistemas antigo, geralmente header está na linha 4
            if aba_principal.strip().upper() == "FJ SISTEMAS":
                df = pd.read_excel(file, sheet_name=aba_principal, header=3)
            else:
                df = pd.read_excel(file, sheet_name=aba_principal)

            df.columns = [str(c).strip().lower() for c in df.columns]

            df = df.rename(columns={
                "filial": "filial",
                "grupo": "grupo",
                "subgrupo": "subgrupo",
                "id prod.": "id_produto",
                "id prod": "id_produto",
                "cod": "id_produto",
                "descrição": "descricao",
                "descricao": "descricao",
                "quantidade": "quantidade",
                "cxs": "quantidade",
                "peso liquido": "peso_liquido",
                "peso líquido": "peso_liquido",
                "peso l.": "peso_liquido",
                "validade": "validade",
                "produção": "producao",
                "producao": "producao",
                "corte": "corte",
                "família": "familia",
                "familia": "familia",
                "condição": "condicao",
                "condicao": "condicao",
            })

            colunas_obrigatorias = [
                "filial", "grupo", "subgrupo", "id_produto", "descricao",
                "quantidade", "peso_liquido"
            ]

            faltando = [c for c in colunas_obrigatorias if c not in df.columns]
            if faltando:
                raise ValueError(
                    "Colunas obrigatórias ausentes após leitura da aba "
                    f"'{aba_principal}': {', '.join(faltando)}"
                )

            if "validade" not in df.columns:
                df["validade"] = None
            if "producao" not in df.columns:
                df["producao"] = None
            if "corte" not in df.columns:
                df["corte"] = None
            if "familia" not in df.columns:
                df["familia"] = None
            if "condicao" not in df.columns:
                df["condicao"] = None

            df = df[df["filial"].notna()].copy()

            capacidades = pd.read_csv("data/capacidades.csv")
            mapa_grupos = pd.read_csv("data/mapa_grupos.csv")

            # tenta ler auxiliares sem quebrar o fluxo
            try:
                planilha3 = pd.read_excel(file, sheet_name="Planilha3")
            except Exception:
                planilha3 = pd.DataFrame()

            try:
                aba_condicao = pd.read_excel(file, sheet_name="CONDIÇÃO")
            except Exception:
                try:
                    aba_condicao = pd.read_excel(file, sheet_name="CONDIÇÃO")
                except Exception:
                    aba_condicao = pd.DataFrame()

            data_ref = pd.Timestamp.today().strftime("%Y-%m-%d")

            detalhe, resumo = prepare_data(
                df=df,
                capacities_df=capacidades,
                group_map_df=mapa_grupos,
                data_referencia=data_ref,
                product_map_df=planilha3,
                condition_map_df=aba_condicao,
            )

            upload_id = save_upload(file.name, data_ref)
            save_detalhe(detalhe, upload_id)
            save_resumo(resumo, upload_id)

            peso_total_lido = pd.to_numeric(
                df["peso_liquido"], errors="coerce").fillna(0).sum()

            st.success("Arquivo processado com sucesso 🚀")
            st.info(f"Aba lida: {aba_principal}")
            st.info(
                "Peso total lido do arquivo: "
                + f"{peso_total_lido:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )

            with st.expander("Prévia do detalhe classificado"):
                st.dataframe(detalhe.head(
                    50), use_container_width=True, hide_index=True)

            with st.expander("Prévia do resumo gerado"):
                st.dataframe(resumo, use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")
