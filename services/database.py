import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("data/estoque.db")


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def ensure_column(conn, table_name, column_name, column_type):
    cols = pd.read_sql(f"PRAGMA table_info({table_name})", conn)
    if column_name not in cols["name"].tolist():
        conn.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


def init_db():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_arquivo TEXT,
        data_referencia TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS estoque_resumo (
        upload_id INTEGER,
        data_referencia TEXT,
        filial TEXT,
        tipo_estoque TEXT,
        peso_total REAL,
        quantidade_total REAL,
        capacidade_tipo REAL,
        ocupacao_percentual REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS estoque_detalhe (
        upload_id INTEGER,
        data_referencia TEXT,
        filial TEXT,
        grupo TEXT,
        subgrupo TEXT,
        id_produto TEXT,
        descricao TEXT,
        quantidade REAL,
        peso_liquido REAL,
        validade TEXT,
        producao TEXT,
        tipo_estoque TEXT,
        corte_animal TEXT
    )
    """)

    conn.commit()

    # migrações automáticas
    ensure_column(conn, "estoque_resumo", "capacidade_total", "REAL")
    ensure_column(conn, "estoque_detalhe", "corte_animal", "TEXT")

    conn.commit()
    conn.close()


def save_upload(nome_arquivo, data_referencia):
    init_db()
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO uploads (nome_arquivo, data_referencia) VALUES (?, ?)",
        (nome_arquivo, data_referencia)
    )
    upload_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return upload_id


def save_resumo(df: pd.DataFrame, upload_id: int):
    init_db()
    conn = get_conn()
    df = df.copy()
    df["upload_id"] = upload_id
    df.to_sql("estoque_resumo", conn, if_exists="append", index=False)
    conn.close()


def save_detalhe(df: pd.DataFrame, upload_id: int):
    init_db()
    conn = get_conn()
    df = df.copy()
    df["upload_id"] = upload_id
    df.to_sql("estoque_detalhe", conn, if_exists="append", index=False)
    conn.close()


def load_uploads():
    init_db()
    conn = get_conn()
    try:
        df = pd.read_sql("""
            SELECT *
            FROM uploads
            ORDER BY id DESC
            LIMIT 1
        """, conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df


def load_latest_summary():
    init_db()
    conn = get_conn()
    try:
        df = pd.read_sql("""
            SELECT *
            FROM estoque_resumo
            WHERE upload_id = (
                SELECT MAX(id) FROM uploads
            )
        """, conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df


def load_latest_detail():
    init_db()
    conn = get_conn()
    try:
        df = pd.read_sql("""
            SELECT *
            FROM estoque_detalhe
            WHERE upload_id = (
                SELECT MAX(id) FROM uploads
            )
        """, conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df
