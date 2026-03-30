
from __future__ import annotations
import io
import pandas as pd
import re

EXPECTED_COLUMNS = [
    "Filial", "Grupo", "Subgrupo", "Id Prod.", "Descricao",
    "Quantidade", "Peso Liquido", "Validade", "Producao"
]


def extract_report_date(file_bytes: bytes) -> str | None:
    raw = pd.read_excel(io.BytesIO(file_bytes), sheet_name="FJ Sistemas", header=None, nrows=4)
    line = str(raw.iloc[2, 0]) if len(raw) >= 3 else ""
    match = re.search(r"(\d{2}/\d{2}/\d{4})", line)
    if match:
        return pd.to_datetime(match.group(1), dayfirst=True).strftime("%Y-%m-%d")
    return None


def read_inventory_excel(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_excel(io.BytesIO(file_bytes), sheet_name="FJ Sistemas", header=3)
    df = df[EXPECTED_COLUMNS].copy()

    rename_map = {
        "Filial": "filial",
        "Grupo": "grupo",
        "Subgrupo": "subgrupo",
        "Id Prod.": "id_produto",
        "Descricao": "descricao",
        "Quantidade": "quantidade",
        "Peso Liquido": "peso_liquido",
        "Validade": "validade",
        "Producao": "producao",
    }
    df.rename(columns=rename_map, inplace=True)

    df = df[df["filial"].notna()].copy()

    for col in ["filial", "grupo", "subgrupo", "id_produto", "descricao"]:
        df[col] = df[col].astype(str).str.strip().str.upper()

    for col in ["quantidade", "peso_liquido"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    for col in ["validade", "producao"]:
        df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")

    return df
