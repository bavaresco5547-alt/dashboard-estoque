import re
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


# =========================
# PALAVRAS-CHAVE
# =========================
BOVINO_KEYWORDS = [
    "BOVINO", "BOVINA", "CORTE BOVINO", "CORTE BOVINA",
    "CARNE BOVINA", "CARNE BOVINO", "BOV",
    "BOI", "VACA", "NOVILHO", "GARROTE", "TOURO",
    "DIANTEIRO BOV", "TRASEIRO BOV", "MIUDOS BOV",
    "FIGADO BOV", "FIGADO", "RABO BOV", "BUCHO BOV", "BUCHO",
    "MOCOTO", "DOBRADINHA", "GLOTE", "CORACAO", "CORAÇÃO",
    "PATINHO", "ACEM", "ACÉM", "COXAO MOLE", "COXÃO MOLE",
    "COXAO DURO", "COXÃO DURO", "CONTRA FILE", "CONTRA FILÉ",
    "FILE MIGNON", "FILÉ MIGNON", "FRALDA", "PICANHA",
    "MAMINHA", "LAGARTO", "CUPIM", "PALETA BOV", "COSTELA BOV",
    "JERKED BEEF", "CHARQUE", "CARNE SECA", "PONTA DE AGULHA",
    "GORDURA ABATE", "SUB PRODUTO", "SUB PRODUTOS"
]

SUINO_KEYWORDS = [
    "SUINO", "SUINA", "SUÍNO", "SUÍNA", "CORTE SUINO", "CORTE SUÍNO",
    "CARNE SUINA", "CARNE SUÍNA", "PORCO",
    "PERNIL SU", "LOMBO SU", "COSTELA SU", "PALETA SU", "BARRIGA SU",
    "TOUCINHO", "BACON", "COPA LOMBO", "PANCETA",
    "PERNIL", "LOMBO", "COSTELA SUINA", "COSTELA SUÍNA",
    "EMBUTIDO", "EMBUTIDOS", "LINGUICA", "LINGUIÇA", "LINGUICA TOSCANA",
    "LINGUIÇA TOSCANA", "CALABRESA", "MY PORK", "KIT FEIJOADA"
]

AVE_KEYWORDS = [
    "AVE", "AVES", "FRANGO", "GALINHA", "GALO",
    "COXA", "SOBRECOXA", "ASA", "MEIO DA ASA", "DRUMET",
    "PEITO DE FRANGO", "FILE DE FRANGO", "FILÉ DE FRANGO",
    "CORAÇÃO DE FRANGO", "MOELA", "PE DE FRANGO", "PÉ DE FRANGO"
]

PET_KEYWORDS = [
    "PET", "RACAO PET", "RAÇÃO PET", "DOG", "CAT",
    "CAES", "CÃES", "GATOS", "BIFINHO PET", "SNACK PET"
]

OUTROS_FORCE_KEYWORDS = [
    "VEGETAIS", "BATATA", "EMBALAGEM", "CAIXA", "PLASTICO", "PLÁSTICO",
    "ETIQUETA", "PAPELAO", "PAPELÃO", "BANDEJA", "SACO", "FILME", "LACRE",
    "TRIPA", "TRIPA SECA", "ENVOLTORIO", "ENVOLT."
]


def contains_any(texto: str, keywords: list[str]) -> bool:
    return any(k in texto for k in keywords)


def classificar_por_nomenclatura(descricao: str, corte: str, familia: str, grupo: str, subgrupo: str) -> str:
    desc = normalize_text(descricao)
    corte_n = normalize_text(corte)
    fam = normalize_text(familia)
    grp = normalize_text(grupo)
    sub = normalize_text(subgrupo)

    texto = " ".join([desc, corte_n, fam, grp, sub]).strip()

    if not texto:
        return "OUTROS"

    # 1) força OUTROS primeiro apenas para materiais realmente não-cárneos
    if contains_any(texto, OUTROS_FORCE_KEYWORDS):
        # exceção: se tiver sinal muito forte de bovino/suíno, respeita a carne
        if contains_any(texto, BOVINO_KEYWORDS):
            return "BOVINO"
        if contains_any(texto, SUINO_KEYWORDS):
            return "SUINO"
        return "OUTROS"

    # 2) regras fortes por grupo/subgrupo
    if "JERKED BEEF" in grp or "CHARQUE" in grp or "CARNE PARA CHARQUE" in grp:
        return "BOVINO"

    if "MIUDOS" in grp or "MIUDOS CONG" in grp:
        return "BOVINO"

    if "SUB PRODUTOS" in grp or "SUB PRODUTO" in grp:
        return "BOVINO"

    if "EMBUTIDOS" in grp:
        return "SUINO"

    if "VEGETAIS CONGELADOS" in grp:
        return "OUTROS"

    # 3) palavras-chave
    if contains_any(texto, PET_KEYWORDS):
        return "PET"

    if contains_any(texto, AVE_KEYWORDS):
        return "AVE"

    if contains_any(texto, SUINO_KEYWORDS):
        return "SUINO"

    if contains_any(texto, BOVINO_KEYWORDS):
        return "BOVINO"

    # 4) regex de reforço
    if re.search(r"\bBOV(INO|INA)?\b", texto):
        return "BOVINO"

    if re.search(r"\bSUI(NO|NA)?\b|\bPORCO\b", texto):
        return "SUINO"

    if re.search(r"\bFRANGO\b|\bGALINHA\b|\bAVE(S)?\b", texto):
        return "AVE"

    if re.search(r"\bPET\b", texto):
        return "PET"

    return "OUTROS"


def normalizar_corte_animal(valor: str) -> str:
    valor = normalize_text(valor)

    if "BOVINO" in valor or "BOVINA" in valor or "CORTE BOV" in valor or re.search(r"\bBOV\b", valor):
        return "BOVINO"
    if "SUI" in valor or "SUIN" in valor or "PORCO" in valor:
        return "SUINO"
    if "AVE" in valor or "FRANGO" in valor or "GALINHA" in valor or "AVES" in valor:
        return "AVE"
    if "PET" in valor:
        return "PET"

    return "OUTROS"


def normalizar_tipo_estoque(valor: str) -> str:
    valor = normalize_text(valor)

    if "CONGEL" in valor:
        return "CONGELADO"
    if "RESFRI" in valor:
        return "RESFRIADO"
    if "AMBIENTE" in valor:
        return "AMBIENTE"

    return ""


def prepare_data(
    df: pd.DataFrame,
    capacities_df: pd.DataFrame,
    group_map_df: pd.DataFrame,
    data_referencia: str | None,
    product_map_df: pd.DataFrame | None = None,
    condition_map_df: pd.DataFrame | None = None,
):
    group_map = {
        normalize_text(row["grupo_original"]): normalize_text(row["tipo_estoque"])
        for _, row in group_map_df.iterrows()
    }

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

    produto_para_condicao = {}
    if condition_map_df is not None and not condition_map_df.empty:
        cond_map = condition_map_df.copy()
        cond_map.columns = [str(c).strip().upper() for c in cond_map.columns]

        codigo_col = None
        temperatura_col = None

        for c in cond_map.columns:
            if "CODIGO" in normalize_text(c) and "SISTEMA" in normalize_text(c):
                codigo_col = c
            if "TEMPERATURA" in normalize_text(c):
                temperatura_col = c

        if codigo_col and temperatura_col:
            cond_map[codigo_col] = cond_map[codigo_col].astype(str).str.strip()
            cond_map[temperatura_col] = cond_map[temperatura_col].astype(
                str).str.strip()

            produto_para_condicao = {
                str(row[codigo_col]).strip(): normalizar_tipo_estoque(row[temperatura_col])
                for _, row in cond_map.iterrows()
            }

    detail = df.copy()

    detail["filial_original"] = detail["filial"].astype(str).str.strip()
    detail["filial"] = detail["filial_original"].apply(canonical_filial)
    detail["filial_norm"] = detail["filial"].apply(normalize_text)

    detail["grupo"] = detail["grupo"].astype(str).str.strip()
    detail["subgrupo"] = detail["subgrupo"].astype(str).str.strip()
    detail["descricao"] = detail["descricao"].astype(str).str.strip()
    detail["id_produto"] = detail["id_produto"].astype(str).str.strip()

    detail["familia"] = detail.get(
        "familia", "").fillna("").astype(str).str.strip()
    detail["corte"] = detail.get("corte", "").fillna(
        "").astype(str).str.strip()
    detail["condicao"] = detail.get(
        "condicao", "").fillna("").astype(str).str.strip()

    detail["quantidade"] = pd.to_numeric(
        detail["quantidade"], errors="coerce").fillna(0)
    detail["peso_liquido"] = pd.to_numeric(
        detail["peso_liquido"], errors="coerce").fillna(0)

    # TIPO ESTOQUE
    detail["tipo_estoque"] = detail["condicao"].apply(normalizar_tipo_estoque)

    detail["tipo_estoque"] = detail.apply(
        lambda row: (
            produto_para_condicao.get(str(row["id_produto"]).strip(), "")
            if row["tipo_estoque"] == ""
            else row["tipo_estoque"]
        ),
        axis=1
    )

    detail["tipo_estoque"] = detail.apply(
        lambda row: (
            classify_group(row["grupo"], group_map)
            if row["tipo_estoque"] == ""
            else row["tipo_estoque"]
        ),
        axis=1
    )

    detail["data_referencia"] = data_referencia

    # GRUPO ANIMAL
    detail["corte_animal"] = detail["corte"].apply(normalizar_corte_animal)

    detail["corte_animal"] = detail.apply(
        lambda row: (
            produto_para_corte.get(str(row["id_produto"]).strip(), "OUTROS")
            if row["corte_animal"] in ["", "OUTROS"]
            else row["corte_animal"]
        ),
        axis=1
    )

    detail["corte_animal"] = detail.apply(
        lambda row: classificar_por_nomenclatura(
            descricao=row["descricao"],
            corte=row["corte"],
            familia=row["familia"],
            grupo=row["grupo"],
            subgrupo=row["subgrupo"],
        ) if row["corte_animal"] in ["", "OUTROS"] else row["corte_animal"],
        axis=1
    )

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
            "quantidade", "peso_liquido", "validade", "producao",
            "tipo_estoque", "corte_animal"
        ]
    ]

    resumo = resumo[
        [
            "data_referencia", "filial", "tipo_estoque",
            "peso_total", "quantidade_total", "capacidade_tipo", "ocupacao_percentual"
        ]
    ]

    return detail, resumo
