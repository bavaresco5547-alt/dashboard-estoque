import streamlit as st
import pandas as pd
import plotly.express as px
from services.database import load_latest_detail, load_latest_summary, load_uploads

st.set_page_config(page_title="Dashboard Estoque", layout="wide")

CD_FILIAIS_BASE = [
    "BELO HORIZONTE",
    "BENEVIDES - PA",
    "BRASILIA",
    "CAMBE",
    "CAMPINAS",
    "CD CAMPO GRANDE",
    "CD RIBEIRAO PRETO",
    "CD RIBEIRÃO PRETO",
    "CURITIBA",
    "HORIZONTE",
    "MARINGA",
    "RIO DE JANEIRO",
    "SAO JOSE",
    "SAO LOURENCO",
    "SAO LOURENÇO",
]


def normalizar_texto(txt):
    if pd.isna(txt):
        return ""
    txt = str(txt).strip().upper()
    trocas = {
        "Á": "A", "À": "A", "Ã": "A", "Â": "A",
        "É": "E", "È": "E", "Ê": "E",
        "Í": "I", "Ì": "I", "Î": "I",
        "Ó": "O", "Ò": "O", "Õ": "O", "Ô": "O",
        "Ú": "U", "Ù": "U", "Û": "U",
        "Ç": "C",
    }
    for k, v in trocas.items():
        txt = txt.replace(k, v)
    txt = " ".join(txt.split())
    return txt


CD_FILIAIS_NORMALIZADAS = {normalizar_texto(x) for x in CD_FILIAIS_BASE}


def classificar_cd_fab(filial):
    return "CD" if normalizar_texto(filial) in CD_FILIAIS_NORMALIZADAS else "FAB"


def fmt_num(v):
    try:
        return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00"


def fmt_pct(v):
    try:
        return f"{round(float(v))}%"
    except Exception:
        return "0%"


st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #161922 0%, #202531 100%);
}
.block-container {
    max-width: 98%;
    padding-top: 0.9rem;
    padding-bottom: 1rem;
}
.hero {
    background: linear-gradient(135deg, #2f3645 0%, #262c39 100%);
    padding: 22px 24px;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 14px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.18);
}
.hero-title {
    color: white;
    font-size: 27px;
    font-weight: 800;
    letter-spacing: 0.3px;
}
.hero-subtitle {
    color: #c7cdd9;
    font-size: 13px;
    margin-top: 6px;
}
.top-line {
    height: 10px;
    border-radius: 999px;
    background: #2247c7;
    margin: 10px 0 18px 0;
}
.metric {
    background: linear-gradient(180deg, #2d3340 0%, #262b36 100%);
    padding: 14px;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.08);
    min-height: 116px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.12);
}
.metric-title {
    color: #b3bccd;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.metric-value {
    color: white;
    font-size: 21px;
    font-weight: 800;
    margin-top: 10px;
    line-height: 1.2;
}
.metric-sub {
    color: #c7cdd9;
    font-size: 11px;
    margin-top: 10px;
}
.panel {
    background: linear-gradient(180deg, #2b3140 0%, #242a36 100%);
    border-radius: 16px;
    padding: 14px;
    margin-top: 12px;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}
.panel-title {
    color: #ffffff;
    font-weight: 800;
    font-size: 14px;
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}
.small-note {
    color: #d1d5db;
    font-size: 12px;
    margin-top: 8px;
}
div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}
[data-testid="stSelectbox"] label {
    color: white !important;
    font-weight: 700 !important;
    font-size: 12px !important;
}
</style>
""", unsafe_allow_html=True)

uploads = load_uploads()
summary = load_latest_summary()
detail = load_latest_detail()

if summary.empty or detail.empty:
    st.warning(
        "Sem dados ainda. Vá primeiro na tela de upload e processe um arquivo.")
    st.stop()

summary = summary.copy()
detail = detail.copy()

summary["filial"] = summary["filial"].fillna("").astype(str).str.strip()
detail["filial"] = detail["filial"].fillna("").astype(str).str.strip()

summary["tipo_estoque"] = summary["tipo_estoque"].fillna(
    "NÃO CLASSIFICADO").astype(str).str.strip()
detail["tipo_estoque"] = detail["tipo_estoque"].fillna(
    "NÃO CLASSIFICADO").astype(str).str.strip()

detail["corte_animal"] = detail.get("corte_animal", "OUTROS").fillna(
    "OUTROS").astype(str).str.strip()

summary["peso_total"] = pd.to_numeric(
    summary["peso_total"], errors="coerce").fillna(0)
summary["capacidade_tipo"] = pd.to_numeric(
    summary["capacidade_tipo"], errors="coerce").fillna(0)
summary["capacidade_total"] = pd.to_numeric(
    summary.get("capacidade_total", 0), errors="coerce").fillna(0)
detail["peso_liquido"] = pd.to_numeric(detail.get(
    "peso_liquido", 0), errors="coerce").fillna(0)

summary["tipo_unidade"] = summary["filial"].apply(classificar_cd_fab)
detail["tipo_unidade"] = detail["filial"].apply(classificar_cd_fab)

if not uploads.empty:
    up = uploads.iloc[0]
    nome_arquivo = up.get("nome_arquivo", "")
    data_ref = up.get("data_referencia", "")
else:
    nome_arquivo = ""
    data_ref = ""

st.markdown(f"""
<div class="hero">
    <div class="hero-title">ESTOQUE X CAPACIDADE - PAINEL DIRETORIA</div>
    <div class="hero-subtitle">Arquivo: {nome_arquivo} | Data referência: {data_ref}</div>
</div>
<div class="top-line"></div>
""", unsafe_allow_html=True)

filiais_existentes = sorted(summary["filial"].dropna().unique().tolist())
filiais_cd_existentes = [
    f for f in filiais_existentes if classificar_cd_fab(f) == "CD"]
filiais_fab_existentes = [
    f for f in filiais_existentes if classificar_cd_fab(f) == "FAB"]

f1, f2, f3, f4 = st.columns(4)

visao_unidade = f1.selectbox("VISÃO OPERACIONAL", ["TODOS", "CD", "FAB"])

if visao_unidade == "CD":
    lista_filiais_filtro = ["TODAS"] + filiais_cd_existentes
elif visao_unidade == "FAB":
    lista_filiais_filtro = ["TODAS"] + filiais_fab_existentes
else:
    lista_filiais_filtro = ["TODAS"] + filiais_existentes

filial = f2.selectbox("FILIAL", lista_filiais_filtro)
tipo = f3.selectbox(
    "TIPO", ["TODOS"] + sorted(summary["tipo_estoque"].dropna().unique().tolist()))
grupo = f4.selectbox(
    "GRUPO", ["TODOS", "BOVINO", "SUINO", "AVE", "PET", "OUTROS"])

summary_f = summary.copy()
detail_f = detail.copy()

if visao_unidade != "TODOS":
    summary_f = summary_f[summary_f["tipo_unidade"] == visao_unidade]
    detail_f = detail_f[detail_f["tipo_unidade"] == visao_unidade]

if filial != "TODAS":
    summary_f = summary_f[summary_f["filial"] == filial]
    detail_f = detail_f[detail_f["filial"] == filial]

if tipo != "TODOS":
    summary_f = summary_f[summary_f["tipo_estoque"] == tipo]
    detail_f = detail_f[detail_f["tipo_estoque"] == tipo]

if grupo != "TODOS":
    detail_f = detail_f[detail_f["corte_animal"] == grupo]
    combinacoes = detail_f[["filial", "tipo_estoque"]].drop_duplicates()
    summary_f = summary_f.merge(
        combinacoes, on=["filial", "tipo_estoque"], how="inner")

summary_f = summary_f[summary_f["peso_total"] > 0].copy()
detail_f = detail_f[detail_f["peso_liquido"] > 0].copy()

if summary_f.empty:
    st.warning("Nenhum dado encontrado com os filtros selecionados.")
    st.stop()

total = summary_f["peso_total"].sum()
congelado = summary_f.loc[summary_f["tipo_estoque"].str.upper(
) == "CONGELADO", "peso_total"].sum()
resfriado = summary_f.loc[summary_f["tipo_estoque"].str.upper(
) == "RESFRIADO", "peso_total"].sum()
ambiente = summary_f.loc[summary_f["tipo_estoque"].str.upper(
) == "AMBIENTE", "peso_total"].sum()

capacidade_total = summary_f.groupby("filial", as_index=False)[
    "capacidade_total"].max()["capacidade_total"].sum()
ocupacao_total_pct = (total / capacidade_total *
                      100) if capacidade_total > 0 else 0

k1, k2, k3, k4, k5 = st.columns(5)

k1.markdown(
    f"<div class='metric'><div class='metric-title'>TOTAL ESTOQUE</div><div class='metric-value'>{fmt_num(total)}</div><div class='metric-sub'>Peso total filtrado</div></div>", unsafe_allow_html=True)
k2.markdown(
    f"<div class='metric'><div class='metric-title'>CONGELADO</div><div class='metric-value'>{fmt_num(congelado)}</div><div class='metric-sub'>Peso consolidado</div></div>", unsafe_allow_html=True)
k3.markdown(
    f"<div class='metric'><div class='metric-title'>RESFRIADO</div><div class='metric-value'>{fmt_num(resfriado)}</div><div class='metric-sub'>Peso consolidado</div></div>", unsafe_allow_html=True)
k4.markdown(
    f"<div class='metric'><div class='metric-title'>AMBIENTE</div><div class='metric-value'>{fmt_num(ambiente)}</div><div class='metric-sub'>Peso consolidado</div></div>", unsafe_allow_html=True)
k5.markdown(
    f"<div class='metric'><div class='metric-title'>OCUPAÇÃO GERAL</div><div class='metric-value'>{fmt_pct(ocupacao_total_pct)}</div><div class='metric-sub'>Estoque / Capacidade</div></div>", unsafe_allow_html=True)

st.markdown(
    f"<div class='small-note'>Visão atual: <b>{visao_unidade}</b> | Filial: <b>{filial}</b> | Tipo: <b>{tipo}</b> | Grupo: <b>{grupo}</b></div>",
    unsafe_allow_html=True
)

tipo_df = (
    summary_f.groupby("tipo_estoque", as_index=False)
    .agg(ESTOQUE=("peso_total", "sum"))
    .query("ESTOQUE > 0")
    .sort_values("ESTOQUE", ascending=False)
    .reset_index(drop=True)
)

grupo_df = (
    detail_f.groupby("corte_animal", as_index=False)
    .agg(ESTOQUE=("peso_liquido", "sum"))
    .query("ESTOQUE > 0")
    .sort_values("ESTOQUE", ascending=False)
    .reset_index(drop=True)
)

estoque_filial = (
    summary_f.groupby(["filial", "tipo_unidade"], as_index=False)
    .agg(ESTOQUE=("peso_total", "sum"))
    .query("ESTOQUE > 0")
)

capacidade_filial = (
    summary_f.groupby("filial", as_index=False)
    .agg(CAPACIDADE=("capacidade_total", "max"))
)

resumo_filial = estoque_filial.merge(
    capacidade_filial, on="filial", how="left")
resumo_filial = resumo_filial[(resumo_filial["ESTOQUE"] > 0) & (
    resumo_filial["CAPACIDADE"] > 0)].copy()
resumo_filial["% OCUPAÇÃO"] = resumo_filial.apply(
    lambda row: (row["ESTOQUE"] / row["CAPACIDADE"] *
                 100) if row["CAPACIDADE"] > 0 else 0,
    axis=1
)
resumo_filial = resumo_filial.sort_values(
    "% OCUPAÇÃO", ascending=False).reset_index(drop=True)

bar_filial = resumo_filial.copy()

cond_df = (
    detail_f.groupby(["tipo_estoque", "corte_animal"], as_index=False)
    .agg(OCUPAÇÃO=("peso_liquido", "sum"))
    .query("OCUPAÇÃO > 0")
)

cap_tipo = (
    summary_f.groupby("tipo_estoque", as_index=False)
    .agg(CAPACIDADE=("capacidade_tipo", "sum"))
)

cond_df = cond_df.merge(cap_tipo, on="tipo_estoque", how="left")
cond_df["CAPACIDADE"] = cond_df["CAPACIDADE"].fillna(0)
cond_df = cond_df[(cond_df["OCUPAÇÃO"] > 0) &
                  (cond_df["CAPACIDADE"] > 0)].copy()
cond_df["%"] = cond_df.apply(
    lambda row: (row["OCUPAÇÃO"] / row["CAPACIDADE"] *
                 100) if row["CAPACIDADE"] > 0 else 0,
    axis=1
)
cond_df = (
    cond_df.rename(
        columns={"tipo_estoque": "CONDIÇÃO", "corte_animal": "GRUPO"})
    .sort_values("OCUPAÇÃO", ascending=False)
    .reset_index(drop=True)
)

cd_fab_resumo = (
    summary_f.groupby("tipo_unidade", as_index=False)
    .agg(
        ESTOQUE=("peso_total", "sum"),
        CAPACIDADE=("capacidade_total", "max")
    )
)
cd_fab_resumo = cd_fab_resumo[(cd_fab_resumo["ESTOQUE"] > 0) & (
    cd_fab_resumo["CAPACIDADE"] > 0)].copy()
cd_fab_resumo["% OCUPAÇÃO"] = cd_fab_resumo.apply(
    lambda row: (row["ESTOQUE"] / row["CAPACIDADE"] *
                 100) if row["CAPACIDADE"] > 0 else 0,
    axis=1
)
cd_fab_resumo = (
    cd_fab_resumo.rename(columns={"tipo_unidade": "VISÃO"})
    .sort_values("ESTOQUE", ascending=False)
    .reset_index(drop=True)
)

c1, c2 = st.columns([1.05, 1.35])

with c1:
    st.markdown("<div class='panel'><div class='panel-title'>ESTOCAGEM X TIPO DE PRODUTO</div>",
                unsafe_allow_html=True)

    fig = px.pie(
        tipo_df,
        names="tipo_estoque",
        values="ESTOQUE",
        hole=0.55,
        color="tipo_estoque",
        color_discrete_map={
            "CONGELADO": "#3b82f6",
            "RESFRIADO": "#f59e0b",
            "AMBIENTE": "#9ca3af",
            "NÃO CLASSIFICADO": "#ef4444",
        }
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=True,
        height=360,
        legend=dict(orientation="h", y=-0.12)
    )
    st.plotly_chart(fig, use_container_width=True)

    tabela_tipos = tipo_df.copy()
    total_tipo = tabela_tipos["ESTOQUE"].sum()
    tabela_tipos["%"] = (tabela_tipos["ESTOQUE"] / total_tipo * 100)
    tabela_tipos["ESTOQUE"] = tabela_tipos["ESTOQUE"].apply(fmt_num)
    tabela_tipos["%"] = tabela_tipos["%"].apply(fmt_pct)
    tabela_tipos = tabela_tipos.rename(columns={"tipo_estoque": "TIPO"})
    st.dataframe(tabela_tipos[["TIPO", "ESTOQUE", "%"]],
                 use_container_width=True, hide_index=True)

    grupo_show = grupo_df.copy()
    total_grupo = grupo_show["ESTOQUE"].sum()
    grupo_show["%"] = (grupo_show["ESTOQUE"] / total_grupo * 100)
    grupo_show["ESTOQUE"] = grupo_show["ESTOQUE"].apply(fmt_num)
    grupo_show["%"] = grupo_show["%"].apply(fmt_pct)
    grupo_show = grupo_show.rename(columns={"corte_animal": "GRUPO"})
    st.dataframe(grupo_show[["GRUPO", "ESTOQUE", "%"]],
                 use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown("<div class='panel'><div class='panel-title'>CAPACIDADE X ESTOCAGEM</div>",
                unsafe_allow_html=True)

    if not bar_filial.empty:
        fig2 = px.bar(
            bar_filial,
            x="% OCUPAÇÃO",
            y="filial",
            orientation="h",
            color="tipo_unidade",
            text="% OCUPAÇÃO",
            color_discrete_map={"CD": "#2563eb", "FAB": "#16a34a"}
        )
        fig2.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            margin=dict(l=10, r=25, t=10, b=10),
            height=max(360, len(bar_filial) * 34),
            xaxis_title="% ocupação",
            yaxis_title="",
            yaxis=dict(autorange="reversed")
        )
        st.plotly_chart(fig2, use_container_width=True)

    tabela_bar = bar_filial.rename(
        columns={"filial": "FILIAL", "tipo_unidade": "VISÃO"}).copy()
    tabela_bar["ESTOQUE"] = tabela_bar["ESTOQUE"].apply(fmt_num)
    tabela_bar["CAPACIDADE"] = tabela_bar["CAPACIDADE"].apply(fmt_num)
    tabela_bar["% OCUPAÇÃO"] = tabela_bar["% OCUPAÇÃO"].apply(fmt_pct)
    st.dataframe(tabela_bar[["FILIAL", "VISÃO", "ESTOQUE", "CAPACIDADE",
                 "% OCUPAÇÃO"]], use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

r1, r2 = st.columns([1.1, 1.3])

with r1:
    st.markdown("<div class='panel'><div class='panel-title'>CONDIÇÃO X CAPACIDADE X OCUPAÇÃO</div>",
                unsafe_allow_html=True)

    cond_show = cond_df.copy()
    cond_show["CAPACIDADE"] = cond_show["CAPACIDADE"].apply(fmt_num)
    cond_show["OCUPAÇÃO"] = cond_show["OCUPAÇÃO"].apply(fmt_num)
    cond_show["%"] = cond_show["%"].apply(fmt_pct)
    st.dataframe(cond_show[["CONDIÇÃO", "GRUPO", "OCUPAÇÃO",
                 "CAPACIDADE", "%"]], use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with r2:
    st.markdown("<div class='panel'><div class='panel-title'>RESUMO POR FILIAL</div>",
                unsafe_allow_html=True)

    resumo_show = resumo_filial.rename(
        columns={"filial": "FILIAL", "tipo_unidade": "VISÃO"}).copy()
    resumo_show["ESTOQUE"] = resumo_show["ESTOQUE"].apply(fmt_num)
    resumo_show["CAPACIDADE"] = resumo_show["CAPACIDADE"].apply(fmt_num)
    resumo_show["% OCUPAÇÃO"] = resumo_show["% OCUPAÇÃO"].apply(fmt_pct)
    st.dataframe(resumo_show[["FILIAL", "VISÃO", "ESTOQUE", "CAPACIDADE",
                 "% OCUPAÇÃO"]], use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='panel'><div class='panel-title'>ESTOQUE X CAPACIDADE</div>",
            unsafe_allow_html=True)

capacidade_total_bloco = (
    summary_f.groupby("filial", as_index=False)["capacidade_total"]
    .max()["capacidade_total"]
    .sum()
)

estoque_total_bloco = summary_f["peso_total"].sum()

ocupacao_total_bloco = (
    (estoque_total_bloco / capacidade_total_bloco) * 100
    if capacidade_total_bloco > 0 else 0
)

bloco_estoque_capacidade = pd.DataFrame([{
    "ESTOQUE": fmt_num(estoque_total_bloco),
    "CAPACIDADE": fmt_num(capacidade_total_bloco),
    "% OCUPAÇÃO": fmt_pct(ocupacao_total_bloco)
}])

st.dataframe(
    bloco_estoque_capacidade,
    use_container_width=True,
    hide_index=True
)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

with st.expander("Ver detalhe dos itens"):
    cols_detalhe = [c for c in [
        "filial", "tipo_unidade", "tipo_estoque", "corte_animal",
        "grupo", "subgrupo", "id_produto", "descricao",
        "quantidade", "peso_liquido", "validade", "producao"
    ] if c in detail_f.columns]

    detalhe_show = detail_f[cols_detalhe].copy()
    detalhe_show = detalhe_show.rename(columns={
        "filial": "FILIAL",
        "tipo_unidade": "VISÃO",
        "tipo_estoque": "TIPO",
        "corte_animal": "GRUPO",
        "grupo": "GRUPO ORIGEM",
        "subgrupo": "SUBGRUPO",
        "id_produto": "ID PRODUTO",
        "descricao": "DESCRIÇÃO",
        "quantidade": "QUANTIDADE",
        "peso_liquido": "PESO LÍQUIDO",
        "validade": "VALIDADE",
        "producao": "PRODUÇÃO",
    })

    if "PESO LÍQUIDO" in detalhe_show.columns:
        detalhe_show["PESO LÍQUIDO"] = pd.to_numeric(
            detalhe_show["PESO LÍQUIDO"], errors="coerce").fillna(0)
        detalhe_show = detalhe_show[detalhe_show["PESO LÍQUIDO"] > 0].copy()
        detalhe_show = detalhe_show.sort_values(
            "PESO LÍQUIDO", ascending=False)
        detalhe_show["PESO LÍQUIDO"] = detalhe_show["PESO LÍQUIDO"].apply(
            fmt_num)

    st.dataframe(detalhe_show, use_container_width=True, hide_index=True)
