import pandas as pd
from services.rules import classify_group, normalize_text

# =========================
# DE/PARA DE FILIAIS
# CONSOLIDAR APENAS CURITIBA
# =========================
FILIAL_ALIAS = {
    "CURITIBA BMG": "CURITIBA",
    "CURITIBA - LINHA VERDE": "CURITIBA",
    "CURITIBA LINHA VERDE": "CURITIBA",
    "BMG40 - CURITIBA": "CURITIBA",

    "BMG03 - SAO JOSE": "SAO JOSE",
    "BMG07 - SAO LOURENCO": "SAO LOURENCO",
    "BMG18 - MARINGA": "MARINGA",
    "BMG41 - CAMPINAS": "CAMPINAS",
    "BMG20 - BRASILIA": "BRASILIA",
    "BMG13 - PORTO ALEGRE": "PORTO ALEGRE",
    "BMG15 - RIO DE JANEIRO": "RIO DE JANEIRO",
    "BMG21 - HORIZONTE": "HORIZONTE",
    "BMG26 - BELO HORIZONTE": "BELO HORIZONTE",
    "NBEF03 - SAO PAULO": "SAO PAULO",
    "NBEF06 - PONTA PORA": "PONTA PORA",
    "NBEF07 - CAMPO GRANDE": "CD CAMPO GRANDE",
}

FILIAL_ALIAS_NORM = {normalize_text(k): v for k, v in FILIAL_ALIAS.items()}


def canonical_filial(value: str) -> str:
    value = "" if value is None else str(value).strip()
    norm = normalize_text(value)
    return FILIAL_ALIAS_NORM.get(norm, value)


def normalizar_corte_animal(valor: str) -> str:
    valor = normalize_text(valor)

    if "BOVINO" in valor:
        return "BOVINO"
    if "SUI" in valor or "SUIN" in valor:
        return "SUINO"
    if "AVE" in valor or "FRANGO" in valor or "GALINHA" in valor:
        return "AVE"
    if "PET" in valor:
        return "PET"

    return "OUTROS"


def prepare_data(
    df: pd.DataFrame,
    capacities_df: pd.DataFrame,
    group_map_df: pd.DataFrame,
    data_referencia: str | None,
    product_map_df: pd.DataFrame | None = None,
):
    # =========================
    # MAPA DE GRUPOS
    # =========================
    group_map = {
        normalize_text(row["grupo_original"]): normalize_text(row["tipo_estoque"])
        for _, row in group_map_df.iterrows()
    }

    # =========================
    # MAPA PRODUTO -> CORTE (Planilha3)
    # =========================
    produto_para_corte = {}
    if product_map_df is not None and not product_map_df.empty:
        mapa = product_map_df.copy()
        mapa.columns = [str(c).strip().upper() for c in mapa.columns]

        if "COD" in mapa.columns and "CORTE" in mapa.columns:
            mapa["COD"] = mapa["COD"].astype(str).str.strip()
            mapa["CORTE"] = mapa["CORTE"].astype(str).str.strip()

            produto_para_corte = {
                str(row["COD"]).strip(): normalizar_corte_animal(row["CORTE"])
                for _, row in mapa.iterrows()
            }

    # =========================
    # DETALHE
    # =========================
    detail = df.copy()

    detail["filial_original"] = detail["filial"].astype(str).str.strip()
    detail["filial"] = detail["filial_original"].apply(canonical_filial)
    detail["filial_norm"] = detail["filial"].apply(normalize_text)

    detail["grupo"] = detail["grupo"].astype(str).str.strip()
    detail["subgrupo"] = detail["subgrupo"].astype(str).str.strip()
    detail["descricao"] = detail["descricao"].astype(str).str.strip()
    detail["id_produto"] = detail["id_produto"].astype(str).str.strip()

    detail["quantidade"] = pd.to_numeric(
        detail["quantidade"], errors="coerce").fillna(0)
    detail["peso_liquido"] = pd.to_numeric(
        detail["peso_liquido"], errors="coerce").fillna(0)

    detail["tipo_estoque"] = detail["grupo"].apply(
        lambda x: classify_group(x, group_map))
    detail["data_referencia"] = data_referencia

    if "corte" in detail.columns:
        detail["corte"] = detail["corte"].fillna("").astype(str).str.strip()
    else:
        detail["corte"] = ""

    # 1) usa CORTE da FJ SISTEMA
    detail["corte_animal"] = detail["corte"].apply(normalizar_corte_animal)

    # 2) fallback pelo código do produto
    detail["corte_animal"] = detail.apply(
        lambda row: (
            produto_para_corte.get(str(row["id_produto"]).strip(), "OUTROS")
            if row["corte_animal"] in ["", "OUTROS"]
            else row["corte_animal"]
        ),
        axis=1
    )

    # 3) fallback por descrição/grupo
    detail["corte_animal"] = detail.apply(
        lambda row: normalizar_corte_animal(
            f"{row['descricao']} {row['grupo']}")
        if row["corte_animal"] in ["", "OUTROS"]
        else row["corte_animal"],
        axis=1
    )

    # =========================
    # CAPACIDADES
    # =========================
    capacities = capacities_df.copy()
    capacities["filial"] = capacities["filial"].astype(str).str.strip()
    capacities["filial"] = capacities["filial"].apply(canonical_filial)
    capacities["filial_norm"] = capacities["filial"].apply(normalize_text)

    capacities["capacidade_congelado"] = pd.to_numeric(
        capacities["capacidade_congelado"], errors="coerce").fillna(0)
    capacities["capacidade_resfriado"] = pd.to_numeric(
        capacities["capacidade_resfriado"], errors="coerce").fillna(0)
    capacities["capacidade_ambiente"] = pd.to_numeric(
        capacities["capacidade_ambiente"], errors="coerce").fillna(0)
    capacities["capacidade_total"] = pd.to_numeric(
        capacities["capacidade_total"], errors="coerce").fillna(0)

    # =========================
    # RESUMO - NÃO QUEBRAR POR CORTE_ANIMAL
    # =========================
    resumo = (
        detail.groupby(
            ["data_referencia", "filial", "filial_norm", "tipo_estoque"],
            dropna=False,
            as_index=False
        )
        .agg(
            peso_total=("peso_liquido", "sum"),
            quantidade_total=("quantidade", "sum"),
        )
    )

    cap_long = capacities.melt(
        id_vars=["filial", "filial_norm", "cod_filial", "capacidade_total"],
        value_vars=["capacidade_congelado",
                    "capacidade_resfriado", "capacidade_ambiente"],
        var_name="cap_col",
        value_name="capacidade_tipo",
    )

    cap_long["tipo_estoque"] = cap_long["cap_col"].map({
        "capacidade_congelado": "CONGELADO",
        "capacidade_resfriado": "RESFRIADO",
        "capacidade_ambiente": "AMBIENTE",
    })

    resumo = resumo.merge(
        cap_long[["filial_norm", "tipo_estoque", "capacidade_tipo"]],
        how="left",
        on=["filial_norm", "tipo_estoque"],
    )

    resumo["capacidade_tipo"] = resumo["capacidade_tipo"].fillna(0)
    resumo["ocupacao_percentual"] = resumo.apply(
        lambda row: (row["peso_total"] / row["capacidade_tipo"]
                     * 100) if row["capacidade_tipo"] > 0 else 0,
        axis=1,
    )

    detail = detail[
        [
            "data_referencia", "filial", "grupo", "subgrupo", "id_produto", "descricao",
            "quantidade", "peso_liquido", "validade", "producao", "tipo_estoque", "corte_animal"
        ]
    ]

    resumo = resumo[
        [
            "data_referencia", "filial", "tipo_estoque",
            "peso_total", "quantidade_total", "capacidade_tipo", "ocupacao_percentual"
        ]
    ]

    return detail, resumo
