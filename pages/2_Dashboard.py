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
.stApp { background: linear-gradient(180deg, #1b1d24 0%, #232733 100%); }
.block-container { max-width: 98%; padding-top: 0.8rem; padding-bottom: 1rem; }
.hero {
    background: linear-gradient(135deg, #2d3340 0%, #262b36 100%);
    padding: 22px 24px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 14px; box-shadow: 0 10px 30px rgba(0,0,0,0.18);
}
.hero-title { color: white; font-size: 25px; font-weight: 800; letter-spacing: 0.3px; }
.hero-subtitle { color: #c7cdd9; font-size: 13px; margin-top: 6px; }
.top-line { height: 10px; border-radius: 999px; background: #2247c7; margin: 10px 0 18px 0; }
.panel {
    background: linear-gradient(180deg, #2c313d 0%, #262b36 100%);
    border-radius: 14px; padding: 14px; margin-top: 12px;
    border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}
.panel-title {
    color: #ffffff; font-weight: 800; font-size: 14px; margin-bottom: 10px;
    text-transform: uppercase; letter-spacing: 0.4px;
}
.metric {
    background: linear-gradient(180deg, #2d3340 0%, #272c37 100%);
    padding: 14px; border-radius: 14px; border: 1px solid rgba(255,255,255,0.08);
    min-height: 116px; box-shadow: 0 8px 20px rgba(0,0,0,0.12);
}
.metric-title { color: #b3bccd; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
.metric-value { color: white; font-size: 19px; font-weight: 800; margin-top: 10px; line-height: 1.2; }
.metric-sub { color: #c7cdd9; font-size: 11px; margin-top: 10px; }
.small-note { color: #d1d5db; font-size: 12px; margin-top: 8px; }
div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
[data-testid="stSelectbox"] label { color: white !important; font-weight: 700 !important; font-size: 12px !important; }
</style>
""", unsafe_allow_html=True)

uploads = load_uploads()
summary = load_latest_summary()
detail = load_latest_detail()

if summary.empty or detail.empty:
    st.warning("Sem dados ainda. Vá primeiro na tela de upload e processe um arquivo.")
    st.stop()

summary = summary.copy()
detail = detail.copy()

summary["filial"] = summary["filial"].fillna("").astype(str).str.strip()
detail["filial"] = detail["filial"].fillna("").astype(str).str.strip()
summary["tipo_estoque"] = summary["tipo_estoque"].fillna("NÃO CLASSIFICADO").astype(str).str.strip()
detail["tipo_estoque"] = detail["tipo_estoque"].fillna("NÃO CLASSIFICADO").astype(str).str.strip()
detail["corte_animal"] = detail.get("corte_animal", "OUTROS").fillna("OUTROS").astype(str).str.strip()
detail["grupo"] = detail["grupo"].fillna("").astype(str).str.strip()

summary["peso_total"] = pd.to_numeric(summary["peso_total"], errors="coerce").fillna(0)
summary["capacidade_tipo"] = pd.to_numeric(summary["capacidade_tipo"], errors="coerce").fillna(0)
detail["peso_liquido"] = pd.to_numeric(detail.get("peso_liquido", 0), errors="coerce").fillna(0)

summary["tipo_unidade"] = summary["filial"].apply(classificar_cd_fab)
detail["tipo_unidade"] = detail["filial"].apply(classificar_cd_fab)

if not uploads.empty:
    up = uploads.iloc[0]
    nome_arquivo = up["nome_arquivo"] if "nome_arquivo" in up else ""
    data_ref = up["data_referencia"] if "data_referencia" in up else ""
else:
    nome_arquivo = ""
    data_ref = ""

st.markdown(f"""
<div class="hero">
    <div class="hero-title">ESTOQUE X CAPACIDADE - CD's / FAB's</div>
    <div class="hero-subtitle">Arquivo: {nome_arquivo} | Data referência: {data_ref}</div>
</div>
<div class="top-line"></div>
""", unsafe_allow_html=True)

filiais_existentes = sorted(summary["filial"].dropna().unique().tolist())
filiais_cd_existentes = [f for f in filiais_existentes if classificar_cd_fab(f) == "CD"]
filiais_fab_existentes = [f for f in filiais_existentes if classificar_cd_fab(f) == "FAB"]

f1, f2, f3, f4, f5 = st.columns(5)

visao_unidade = f1.selectbox("VISÃO OPERACIONAL", ["TODOS", "CD", "FAB"])

if visao_unidade == "CD":
    lista_filiais_filtro = ["TODAS"] + filiais_cd_existentes
elif visao_unidade == "FAB":
    lista_filiais_filtro = ["TODAS"] + filiais_fab_existentes
else:
    lista_filiais_filtro = ["TODAS"] + filiais_existentes

filial = f2.selectbox("FILIAL", lista_filiais_filtro)
tipo = f3.selectbox("TIPO", ["TODOS"] + sorted(summary["tipo_estoque"].dropna().unique().tolist()))
especie = f4.selectbox("ESPÉCIE / CORTE", ["TODOS", "BOVINO", "SUINO", "AVE", "PET", "OUTROS"])
grupo = f5.selectbox("GRUPO", ["TODOS"] + sorted([g for g in detail["grupo"].dropna().unique().tolist() if str(g).strip() != ""]))

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

if especie != "TODOS":
    detail_f = detail_f[detail_f["corte_animal"] == especie]
    combinacoes = detail_f[["filial", "tipo_estoque"]].drop_duplicates()
    summary_f = summary_f.merge(combinacoes, on=["filial", "tipo_estoque"], how="inner")

if grupo != "TODOS":
    detail_f = detail_f[detail_f["grupo"] == grupo]
    combinacoes = detail_f[["filial", "tipo_estoque"]].drop_duplicates()
    summary_f = summary_f.merge(combinacoes, on=["filial", "tipo_estoque"], how="inner")

if summary_f.empty:
    st.warning("Nenhum dado encontrado com os filtros selecionados.")
    st.stop()

total = summary_f["peso_total"].sum()
congelado = summary_f.loc[summary_f["tipo_estoque"].str.upper() == "CONGELADO", "peso_total"].sum()
resfriado = summary_f.loc[summary_f["tipo_estoque"].str.upper() == "RESFRIADO", "peso_total"].sum()
ambiente = summary_f.loc[summary_f["tipo_estoque"].str.upper() == "AMBIENTE", "peso_total"].sum()

capacidade_total = summary_f["capacidade_tipo"].sum()
ocupacao_total_pct = (total / capacidade_total * 100) if capacidade_total > 0 else 0

k1, k2, k3, k4, k5 = st.columns(5)

k1.markdown(f"<div class='metric'><div class='metric-title'>TOTAL</div><div class='metric-value'>{fmt_num(total)}</div><div class='metric-sub'>Peso total filtrado</div></div>", unsafe_allow_html=True)
k2.markdown(f"<div class='metric'><div class='metric-title'>CONGELADO</div><div class='metric-value'>{fmt_num(congelado)}</div><div class='metric-sub'>Peso consolidado</div></div>", unsafe_allow_html=True)
k3.markdown(f"<div class='metric'><div class='metric-title'>RESFRIADO</div><div class='metric-value'>{fmt_num(resfriado)}</div><div class='metric-sub'>Peso consolidado</div></div>", unsafe_allow_html=True)
k4.markdown(f"<div class='metric'><div class='metric-title'>AMBIENTE</div><div class='metric-value'>{fmt_num(ambiente)}</div><div class='metric-sub'>Peso consolidado</div></div>", unsafe_allow_html=True)
k5.markdown(f"<div class='metric'><div class='metric-title'>OCUPAÇÃO</div><div class='metric-value'>{fmt_pct(ocupacao_total_pct)}</div><div class='metric-sub'>Estoque / Capacidade</div></div>", unsafe_allow_html=True)

st.markdown(
    f"<div class='small-note'>Visão atual: <b>{visao_unidade}</b> | Filial: <b>{filial}</b> | Tipo: <b>{tipo}</b> | Espécie: <b>{especie}</b> | Grupo: <b>{grupo}</b></div>",
    unsafe_allow_html=True
)

pie_df = summary_f.groupby("tipo_estoque", as_index=False)["peso_total"].sum()

estoque_filial = summary_f.groupby(["filial", "tipo_unidade"], as_index=False).agg(
    peso_total=("peso_total", "sum")
)

capacidade_filial = summary_f.groupby(["filial"], as_index=False).agg(
    capacidade_total=("capacidade_tipo", "sum")
)

bar_filial = estoque_filial.merge(capacidade_filial, on="filial", how="left")
bar_filial["%"] = bar_filial.apply(
    lambda row: (row["peso_total"] / row["capacidade_total"] * 100) if row["capacidade_total"] > 0 else 0,
    axis=1
)
bar_filial_validas = bar_filial[bar_filial["capacidade_total"] > 0].copy().sort_values("%", ascending=True)

resumo_filial = estoque_filial.merge(capacidade_filial, on="filial", how="left")
resumo_filial["% OCUPAÇÃO"] = resumo_filial.apply(
    lambda row: (row["peso_total"] / row["capacidade_total"] * 100) if row["capacidade_total"] > 0 else 0,
    axis=1
)

resumo_filial_tipo = summary_f.pivot_table(
    index=["filial", "tipo_unidade"],
    columns="tipo_estoque",
    values="peso_total",
    aggfunc="sum",
    fill_value=0
).reset_index()

resumo_final = resumo_filial.merge(resumo_filial_tipo, on=["filial", "tipo_unidade"], how="left")

for col in ["CONGELADO", "RESFRIADO", "AMBIENTE", "NÃO CLASSIFICADO"]:
    if col not in resumo_final.columns:
        resumo_final[col] = 0

resumo_final = resumo_final.rename(columns={
    "filial": "FILIAL",
    "tipo_unidade": "VISÃO",
    "peso_total": "ESTOQUE",
    "capacidade_total": "CAPACIDADE"
}).sort_values(["VISÃO", "FILIAL"])

c1, c2 = st.columns([1.05, 1.35])

with c1:
    st.markdown("<div class='panel'><div class='panel-title'>ESTOCAGEM X TIPO DE PRODUTO</div>", unsafe_allow_html=True)

    fig = px.pie(
        pie_df,
        names="tipo_estoque",
        values="peso_total",
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

    tabela_tipos = pie_df.copy()
    total_tipo = tabela_tipos["peso_total"].sum()
    tabela_tipos["%"] = (tabela_tipos["peso_total"] / total_tipo * 100)
    tabela_tipos["ESTOQUE"] = tabela_tipos["peso_total"].apply(fmt_num)
    tabela_tipos["%"] = tabela_tipos["%"].apply(fmt_pct)
    tabela_tipos = tabela_tipos.rename(columns={"tipo_estoque": "TIPO"})
    tabela_tipos = tabela_tipos[["TIPO", "ESTOQUE", "%"]]
    st.dataframe(tabela_tipos, use_container_width=True, hide_index=True)

    especie_df = detail_f.groupby("corte_animal", as_index=False).agg(
        ESTOQUE=("peso_liquido", "sum")
    )

    if not especie_df.empty:
        total_especie = especie_df["ESTOQUE"].sum()
        especie_df["%"] = (especie_df["ESTOQUE"] / total_especie * 100)
        especie_df["ESTOQUE"] = especie_df["ESTOQUE"].apply(fmt_num)
        especie_df["%"] = especie_df["%"].apply(fmt_pct)
        especie_df = especie_df.rename(columns={"corte_animal": "ESPÉCIE"})

        ordem = ["BOVINO", "SUINO", "AVE", "PET", "OUTROS"]
        especie_df["ordem"] = especie_df["ESPÉCIE"].apply(lambda x: ordem.index(x) if x in ordem else 99)
        especie_df = especie_df.sort_values("ordem").drop(columns="ordem")

        st.dataframe(especie_df, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown("<div class='panel'><div class='panel-title'>CAPACIDADE X ESTOCAGEM</div>", unsafe_allow_html=True)

    if not bar_filial_validas.empty:
        altura = max(360, len(bar_filial_validas) * 34)
        fig2 = px.bar(
            bar_filial_validas,
            x="%",
            y="filial",
            orientation="h",
            color="tipo_unidade",
            text="%",
            color_discrete_map={"CD": "#2563eb", "FAB": "#16a34a"}
        )
        fig2.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            margin=dict(l=10, r=25, t=10, b=10),
            height=altura,
            xaxis_title="% ocupação",
            yaxis_title=""
        )
        st.plotly_chart(fig2, use_container_width=True)

    tabela_bar = bar_filial_validas.rename(columns={
        "filial": "FILIAL",
        "tipo_unidade": "VISÃO",
        "peso_total": "ESTOQUE",
        "capacidade_total": "CAPACIDADE",
        "%": "% OCUPAÇÃO"
    }).copy()

    tabela_bar["ESTOQUE"] = tabela_bar["ESTOQUE"].apply(fmt_num)
    tabela_bar["CAPACIDADE"] = tabela_bar["CAPACIDADE"].apply(fmt_num)
    tabela_bar["% OCUPAÇÃO"] = tabela_bar["% OCUPAÇÃO"].apply(fmt_pct)

    st.dataframe(tabela_bar, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

r1, r2 = st.columns([1.1, 1.3])

with r1:
    st.markdown("<div class='panel'><div class='panel-title'>CONDIÇÃO X CAPACIDADE X OCUPAÇÃO</div>", unsafe_allow_html=True)

    # base detalhada para estoque por espécie
    ocup_especie = detail_f.groupby(["tipo_estoque", "corte_animal"], as_index=False).agg(
        OCUPAÇÃO=("peso_liquido", "sum")
    )

    # capacidade vem do resumo, sem duplicar por espécie
    cap_tipo = summary_f.groupby("tipo_estoque", as_index=False).agg(
        CAPACIDADE=("capacidade_tipo", "sum")
    )

    cond_df = ocup_especie.merge(cap_tipo, on="tipo_estoque", how="left")
    cond_df["CAPACIDADE"] = cond_df["CAPACIDADE"].fillna(0)
    cond_df["%"] = cond_df.apply(
        lambda row: (row["OCUPAÇÃO"] / row["CAPACIDADE"] * 100) if row["CAPACIDADE"] > 0 else 0,
        axis=1
    )

    cond_df = cond_df.rename(columns={"tipo_estoque": "CONDIÇÃO", "corte_animal": "ESPÉCIE"}).copy()
    cond_df["CAPACIDADE"] = cond_df["CAPACIDADE"].apply(fmt_num)
    cond_df["OCUPAÇÃO"] = cond_df["OCUPAÇÃO"].apply(fmt_num)
    cond_df["%"] = cond_df["%"].apply(fmt_pct)
    st.dataframe(cond_df, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with r2:
    st.markdown("<div class='panel'><div class='panel-title'>RESUMO POR FILIAL</div>", unsafe_allow_html=True)

    resumo_final_fmt = resumo_final.copy()
    resumo_final_fmt["ESTOQUE"] = resumo_final_fmt["ESTOQUE"].apply(fmt_num)
    resumo_final_fmt["CAPACIDADE"] = resumo_final_fmt["CAPACIDADE"].apply(fmt_num)
    resumo_final_fmt["% OCUPAÇÃO"] = resumo_final_fmt["% OCUPAÇÃO"].apply(fmt_pct)

    st.dataframe(resumo_final_fmt, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='panel'><div class='panel-title'>ESTOQUE X CAPACIDADE - CD X FAB</div>", unsafe_allow_html=True)

estoque_cdfab = summary_f.groupby("tipo_unidade", as_index=False).agg(ESTOQUE=("peso_total", "sum"))
cap_cdfab = summary_f.groupby("tipo_unidade", as_index=False).agg(CAPACIDADE=("capacidade_tipo", "sum"))
cd_fab_resumo = estoque_cdfab.merge(cap_cdfab, on="tipo_unidade", how="left")
cd_fab_resumo["% OCUPAÇÃO"] = cd_fab_resumo.apply(
    lambda row: (row["ESTOQUE"] / row["CAPACIDADE"] * 100) if row["CAPACIDADE"] > 0 else 0,
    axis=1
)
cd_fab_resumo = cd_fab_resumo.rename(columns={"tipo_unidade": "VISÃO"}).copy()
cd_fab_resumo["ESTOQUE"] = cd_fab_resumo["ESTOQUE"].apply(fmt_num)
cd_fab_resumo["CAPACIDADE"] = cd_fab_resumo["CAPACIDADE"].apply(fmt_num)
cd_fab_resumo["% OCUPAÇÃO"] = cd_fab_resumo["% OCUPAÇÃO"].apply(fmt_pct)
st.dataframe(cd_fab_resumo, use_container_width=True, hide_index=True)

st.markdown("</div>", unsafe_allow_html=True)

with st.expander("Ver detalhe dos itens"):
    cols_detalhe = [c for c in [
        "filial", "tipo_unidade", "tipo_estoque", "corte_animal", "grupo", "subgrupo",
        "id_produto", "descricao", "quantidade", "peso_liquido", "validade", "producao"
    ] if c in detail_f.columns]

    detalhe_show = detail_f[cols_detalhe].copy()
    detalhe_show = detalhe_show.rename(columns={
        "filial": "FILIAL",
        "tipo_unidade": "VISÃO",
        "tipo_estoque": "TIPO",
        "corte_animal": "ESPÉCIE",
        "grupo": "GRUPO",
        "subgrupo": "SUBGRUPO",
        "id_produto": "ID PRODUTO",
        "descricao": "DESCRIÇÃO",
        "quantidade": "QUANTIDADE",
        "peso_liquido": "PESO LÍQUIDO",
        "validade": "VALIDADE",
        "producao": "PRODUÇÃO",
    })
    if "PESO LÍQUIDO" in detalhe_show.columns:
        detalhe_show["PESO LÍQUIDO"] = pd.to_numeric(detalhe_show["PESO LÍQUIDO"], errors="coerce").fillna(0).apply(fmt_num)
    st.dataframe(detalhe_show, use_container_width=True, hide_index=True)