
from __future__ import annotations
import pandas as pd

def normalize_text(value: str) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().upper()


def classify_group(grupo: str, group_map: dict[str, str]) -> str:
    grupo_norm = normalize_text(grupo)

    if grupo_norm in group_map:
        return group_map[grupo_norm]

    if "CONGEL" in grupo_norm:
        return "CONGELADO"

    if "RESFRI" in grupo_norm:
        return "RESFRIADO"

    if any(k in grupo_norm for k in ["VEGETAIS", "TRIPA SECA", "JERKED", "PET"]):
        return "AMBIENTE"

    if any(k in grupo_norm for k in ["EMBUTIDOS", "MIUDOS", "SUINOS", "BOVINA", "BOVINO", "SUINA", "CHARQUE"]):
        return "CONGELADO"

    return "AMBIENTE"
