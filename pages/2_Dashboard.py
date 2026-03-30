import streamlit as st
import pandas as pd
import plotly.express as px
from services.database import load_latest_detail, load_latest_summary, load_uploads

st.set_page_config(page_title="Dashboard Estoque", layout="wide")

# =========================
# CONFIG
# =========================
CD_FILIAIS_BASE = [
    "BELO HORIZONTE", "BENEVIDES - PA", "BRASILIA", "CAMBE", "CAMPINAS",
    "CD CAMPO GRANDE", "CD RIBEIRAO PRETO", "CURITIBA", "HORIZONTE",
    "MARINGA", "RIO DE JANEIRO", "SAO JOSE", "SAO LOURENCO"
]


def normalizar_texto(txt):
    if pd.isna(txt):
        return ""
    return str(txt).strip().upper()


def classificar_cd_fab(filial):
    return "CD" if normalizar_texto(filial) in CD_FILIAIS_BASE else "FAB"


def fmt_num(v):
    try:
        return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"


def fmt_pct(v):
    try:
        return f"{round(float(v))}%"
    except:
        return "0%"


# =========================
# DADOS
# =========================
summary = load_latest_summary()
detail = load_latest_detail()

if summary.empty:
    st.warning("Sem dados")
    st.stop()

summary["peso_total"] = pd.to_numeric(
    summary["peso_total"], errors="coerce").fillna(0)
summary["capacidade_total"] = pd.to_numeric(
    summary["capacidade_total"], errors="coerce").fillna(0)
detail["peso_liquido"] = pd.to_numeric(
    detail["peso_liquido"], errors="coerce").fillna(0)

summary = summary[summary["peso_total"] > 0]
detail = detail[detail["peso_liquido"] > 0]

# =========================
# KPI
# =========================
total = summary["peso_total"].sum()
capacidade = summary.groupby("filial")["capacidade_total"].max().sum()
ocupacao = (total / capacidade * 100) if capacidade > 0 else 0

c1, c2 = st.columns(2)
c1.metric("TOTAL", fmt_num(total))
c2.metric("OCUPAÇÃO", fmt_pct(ocupacao))

# =========================
# TIPO
# =========================
tipo_df = (
    summary.groupby("tipo_estoque", as_index=False)
    .agg(ESTOQUE=("peso_total", "sum"))
    .sort_values("ESTOQUE", ascending=False)
)

tipo_df["%"] = tipo_df["ESTOQUE"] / tipo_df["ESTOQUE"].sum() * 100
tipo_df["ESTOQUE"] = tipo_df["ESTOQUE"].apply(fmt_num)
tipo_df["%"] = tipo_df["%"].apply(fmt_pct)

st.subheader("TIPO DE ESTOQUE")
st.dataframe(tipo_df, use_container_width=True, hide_index=True)

# =========================
# GRUPO
# =========================
grupo_df = (
    detail.groupby("corte_animal", as_index=False)
    .agg(ESTOQUE=("peso_liquido", "sum"))
    .sort_values("ESTOQUE", ascending=False)
)

grupo_df["%"] = grupo_df["ESTOQUE"] / grupo_df["ESTOQUE"].sum() * 100
grupo_df["ESTOQUE"] = grupo_df["ESTOQUE"].apply(fmt_num)
grupo_df["%"] = grupo_df["%"].apply(fmt_pct)

st.subheader("GRUPO")
st.dataframe(grupo_df, use_container_width=True, hide_index=True)

# =========================
# FILIAL
# =========================
resumo = (
    summary.groupby("filial", as_index=False)
    .agg(
        ESTOQUE=("peso_total", "sum"),
        CAPACIDADE=("capacidade_total", "max")
    )
)

resumo = resumo[(resumo["ESTOQUE"] > 0) & (resumo["CAPACIDADE"] > 0)]
resumo["%"] = resumo["ESTOQUE"] / resumo["CAPACIDADE"] * 100

resumo = resumo.sort_values("ESTOQUE", ascending=False)

resumo["ESTOQUE"] = resumo["ESTOQUE"].apply(fmt_num)
resumo["CAPACIDADE"] = resumo["CAPACIDADE"].apply(fmt_num)
resumo["%"] = resumo["%"].apply(fmt_pct)

st.subheader("RESUMO POR FILIAL")
st.dataframe(resumo, use_container_width=True, hide_index=True)

# =========================
# GRÁFICO
# =========================
grafico = (
    summary.groupby("filial", as_index=False)
    .agg(ESTOQUE=("peso_total", "sum"))
)

grafico = grafico[grafico["ESTOQUE"] > 0]
grafico = grafico.sort_values("ESTOQUE", ascending=True)

fig = px.bar(
    grafico,
    x="ESTOQUE",
    y="filial",
    orientation="h"
)

st.plotly_chart(fig, use_container_width=True)
