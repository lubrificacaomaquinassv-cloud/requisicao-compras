"""Cria tabela requisicoes no Supabase. Rode uma vez: python setup_supabase.py"""
import os
import tomllib
import psycopg2

SECRETS = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")

with open(SECRETS, "rb") as f:
    cfg = tomllib.load(f)["connections"]["supabase"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS requisicoes (
    id                BIGSERIAL PRIMARY KEY,
    numero_requisicao VARCHAR(20)  UNIQUE NOT NULL,
    solicitante       VARCHAR(255) NOT NULL,
    data              DATE         NOT NULL DEFAULT CURRENT_DATE,
    destino           VARCHAR(50)  NOT NULL,
    cbp               VARCHAR(255) NOT NULL,
    prioridade        VARCHAR(50),
    justificativa     TEXT         NOT NULL,
    fornecedor        VARCHAR(255),
    item_descricao    TEXT,
    item_quantidade   INTEGER,
    item_unidade      VARCHAR(50),
    valor_unitario    NUMERIC(12, 2),
    valor_total       NUMERIC(12, 2) NOT NULL,
    criado_em         TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_requisicoes_data ON requisicoes (data DESC);
CREATE INDEX IF NOT EXISTS idx_requisicoes_numero ON requisicoes (numero_requisicao);
CREATE INDEX IF NOT EXISTS idx_requisicoes_destino ON requisicoes (destino);
"""

conn = psycopg2.connect(
    host=cfg["host"],
    port=cfg["port"],
    database=cfg["database"],
    user=cfg["username"],
    password=cfg["password"],
    sslmode="require",
)
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT 1")
print("Conexao OK")
cur.execute(SCHEMA)
print("Tabela criada/verificada")
cur.close()
conn.close()
