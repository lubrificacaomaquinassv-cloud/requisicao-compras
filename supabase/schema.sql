-- Execute no SQL Editor do Supabase (nova base, histórico fica no Neon)
-- Formato de numeração: REQ-MM-NNNNN (ex: REQ-06-00050)

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

CREATE INDEX IF NOT EXISTS idx_requisicoes_data   ON requisicoes (data DESC);
CREATE INDEX IF NOT EXISTS idx_requisicoes_numero ON requisicoes (numero_requisicao);
CREATE INDEX IF NOT EXISTS idx_requisicoes_destino ON requisicoes (destino);

ALTER TABLE requisicoes ENABLE ROW LEVEL SECURITY;

-- Streamlit usa conexão direta postgres (bypass RLS); política para API futura
CREATE POLICY "requisicoes_leitura_publica"
    ON requisicoes FOR SELECT
    TO authenticated, anon
    USING (true);

CREATE POLICY "requisicoes_insercao_servico"
    ON requisicoes FOR INSERT
    TO authenticated, service_role
    WITH CHECK (true);
