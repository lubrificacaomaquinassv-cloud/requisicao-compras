import streamlit as st
import pandas as pd
from datetime import datetime
import random
import os

# ── CONFIGURAÇÃO DA PÁGINA ───────────────────────────────────────────────────
st.set_page_config(page_title="Sistema de Requisição - Neon.tech V2", layout="wide", page_icon="🏢")

# ── DEFINIÇÕES DE DESIGN (PALETA MODERNA) ────────────────────────────────────
COR_PRIMARIA = "#003049"    # Azul Marinho Profundo
COR_SECUNDARIA = "#669BBC"  # Azul Aço Suave
COR_FUNDO = "#EAF4F4"       # Cinza-Azulado
COR_CARD = "#FFFFFF"        # Branco Puro
COR_BORDA = "#D8E2DC"       # Borda Suave
TEXTO_PRIM = "#212529"      # Cinza Escuro
TEXTO_SEC = "#6C757D"       # Cinza Médio

# ── ESTILO CSS CUSTOMIZADO ──────────────────────────────────────────────────
def aplicar_estilo():
    st.markdown(f"""
    <style>
    .stApp {{ background-color: {COR_FUNDO}; }}
    div[data-testid="stDecoration"] {{ display: none; }}
    .block-container {{ padding-top: 1.5rem !important; }}

    .header-container {{
        background: {COR_PRIMARIA};
        padding: 25px 20px;
        border-radius: 12px 12px 0 0;
        text-align: center;
        color: white;
        margin-bottom: 0px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    .header-title {{ font-size: 32px; font-weight: 800; letter-spacing: 2px; margin-bottom: 5px; }}
    .header-subtitle {{ font-size: 14px; text-transform: uppercase; letter-spacing: 4px; opacity: 0.9; }}
    .header-quote {{ font-family: 'Georgia', serif; font-style: italic; font-size: 16px; margin-top: 15px; color: #fdf0d5; }}

    .stTabs [data-baseweb="tab-list"] {{
        background-color: {COR_PRIMARIA};
        padding: 5px 15px;
        border-radius: 0 0 12px 12px;
        gap: 10px;
    }}
    .stTabs [data-baseweb="tab"] {{ color: rgba(255,255,255,0.6) !important; background: transparent !important; }}
    .stTabs [aria-selected="true"] {{ color: white !important; border-bottom: 3px solid white !important; }}

    .card-secao {{
        background: {COR_CARD};
        padding: 25px;
        border-radius: 12px;
        border-left: 6px solid {COR_PRIMARIA};
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-top: 25px;
        margin-bottom: 25px;
    }}
    .card-titulo {{ font-size: 18px; font-weight: 700; color: {COR_PRIMARIA}; margin-bottom: 20px; border-bottom: 1px solid {COR_BORDA}; padding-bottom: 10px; }}

    div.stButton > button {{
        width: 100%;
        background: linear-gradient(135deg, {COR_PRIMARIA} 0%, {COR_SECUNDARIA} 100%);
        color: white !important;
        border: none;
        padding: 12px;
        font-weight: 700;
        border-radius: 8px;
        transition: all 0.3s ease;
    }}
    
    .stTextInput input, .stTextArea textarea, .stSelectbox select {{
        background-color: #f8f9fa !important;
        border-radius: 8px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# ── CONSTANTES E CONFIGURAÇÕES ───────────────────────────────────────────────
ORGANIZACOES = {
    "ASTS": ["CBP", "LUBRIFICAÇÃO", "ADMINISTRATIVO", "OUTROS"],
    "CBTS": ["MINISTÉRIO", "CBP", "MANUTENÇÃO", "EVENTOS"]
}

NOMES_COMPLETOS = {
    "ASTS": "ASSOCIAÇÃO SOCIAL TERRA SANTA",
    "CBTS": "COMUNIDADE BATISTA TERRA SANTA"
}

LOGOS = {
    "ASTS": "/home/ubuntu/upload/logo_asts.png",
    "CBTS": "/home/ubuntu/upload/logo_cbts.png"
}

# ── FUNÇÕES DE DADOS (POSTGRESQL - NEON.TECH) ────────────────────────────────
def conectar_postgres():
    try:
        conn = st.connection("postgresql", type="sql")
        return conn
    except Exception as e:
        st.error(f"❌ Erro ao conectar ao PostgreSQL: {e}")
        return None

def salvar_requisicao(conn, dados):
    try:
        query = """
        INSERT INTO requisicoes (
            solicitante, data, destino, cbp, prioridade, justificativa,
            fornecedor, item_descricao, item_quantidade, item_unidade, 
            valor_unitario, valor_total
        ) VALUES (
            :solicitante, :data, :destino, :cbp, :prioridade, :justificativa,
            :fornecedor, :item_descricao, :item_quantidade, :item_unidade,
            :valor_unitario, :valor_total
        );
        """
        conn.query(query, **dados).execute()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao salvar no banco de dados: {e}")
        return False

def carregar_dados(conn):
    try:
        df = conn.query("SELECT * FROM requisicoes ORDER BY data_criacao DESC;", ttl="10m")
        return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")
        return pd.DataFrame()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏢 Instituição")
    org_tema = st.selectbox("Selecione a Organização", ["ASTS", "CBTS"])
    aplicar_estilo()
    logo_path = LOGOS.get(org_tema)
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    st.markdown("---")
    st.markdown("### ⚙️ Configurações")
    st.caption("v6.0 - Edição Financeira Neon")

# ── CABEÇALHO PRINCIPAL ──────────────────────────────────────────────────────
st.markdown(f"""
<div class="header-container">
    <div class="header-title">SISTEMA DE REQUISIÇÃO</div>
    <div class="header-subtitle">CONTROLE FINANCEIRO E DE SUPRIMENTOS</div>
    <div class="header-quote">"Jesus é tudo que você precisa!"</div>
</div>
""", unsafe_allow_html=True)

conn = conectar_postgres()

aba1, aba2 = st.tabs(["📋  Nova Requisição", "📂  Histórico de Registros"])

# ── ABA 1 — FORMULÁRIO ────────────────────────────────────────────────────────
with aba1:
    if not conn:
        st.warning("⚠️ Sistema aguardando configuração do banco de dados (Neon.tech).")
        st.stop()
        
    nome_completo = NOMES_COMPLETOS.get(org_tema, org_tema)
    
    # Card de Identificação
    st.markdown(f"""<div class="card-secao"><div class="card-titulo">🏢 {nome_completo}</div>""", unsafe_allow_html=True)
    
    c1, c2 = st.columns([2, 1])
    with c1:
        solicitante = st.text_input("👤 Nome do Solicitante *", placeholder="Quem está pedindo?")
    with c2:
        data_emissao = st.date_input("📅 Data Emissão", value=datetime.now().date(), disabled=True)
    
    # Novo Campo: Fornecedor
    fornecedor = st.text_input("🏪 Fornecedor Sugerido / Real", placeholder="Ex: Leroy Merlin, Posto Central...")
    
    c3, c4 = st.columns(2)
    with c3:
        destino = st.selectbox(f"📍 Destino da Verba ({org_tema}) *", ORGANIZACOES[org_tema])
    with c4:
        st.write("⚖️ **Prioridade**")
        prioridade = st.radio("P", ["🟢 NORMAL", "🟡 URGENTE", "🔴 CRÍTICO"], horizontal=True, label_visibility="collapsed")
    
    justificativa = st.text_area("📝 Justificativa / Finalidade *", placeholder="Descreva a necessidade...", height=80)
    st.markdown('</div>', unsafe_allow_html=True)

    # Card de Itens com Valores
    st.markdown("""<div class="card-secao"><div class="card-titulo">📦 Itens e Valores</div>""", unsafe_allow_html=True)
    
    if "num_itens" not in st.session_state: st.session_state.num_itens = 1
    
    itens_lista = []
    valor_total_geral = 0.0
    
    for i in range(st.session_state.num_itens):
        col_d, col_q, col_u, col_v = st.columns([3, 1, 1, 2])
        with col_d:
            d = st.text_input("Descrição", key=f"d_{i}", placeholder="Produto/Serviço")
        with col_q:
            q = st.number_input("Qtd", key=f"q_{i}", min_value=1, step=1)
        with col_u:
            u = st.text_input("Un", key=f"u_{i}", placeholder="un")
        with col_v:
            v = st.number_input("Valor Unit. (R$)", key=f"v_{i}", min_value=0.0, format="%.2f")
        
        v_total_item = q * v
        st.caption(f"Total Item: R$ {v_total_item:,.2f}")
        
        if d:
            itens_lista.append({
                "descricao": d, "quantidade": q, "unidade": u, 
                "valor_unitario": v, "valor_total": v_total_item
            })
            valor_total_geral += v_total_item
    
    st.markdown(f"### 💰 Valor Total da Requisição: **R$ {valor_total_geral:,.2f}**")
    
    if st.button("＋ Adicionar outro item"): 
        st.session_state.num_itens += 1
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🚀  FINALIZAR E REGISTRAR REQUISIÇÃO"):
        if not solicitante or not justificativa or not itens_lista:
            st.error("⚠️ Preencha os campos obrigatórios e adicione itens.")
        else:
            with st.spinner("Registrando no PostgreSQL..."):
                itens_str = " / ".join([f"{i['descricao']} ({i['quantidade']} {i['unidade']})" for i in itens_lista])
                
                dados_req = {
                    "solicitante": solicitante,
                    "data": str(data_emissao),
                    "destino": org_tema,
                    "cbp": destino,
                    "prioridade": prioridade,
                    "justificativa": justificativa,
                    "fornecedor": fornecedor,
                    "item_descricao": itens_str,
                    "item_quantidade": sum([i['quantidade'] for i in itens_lista]),
                    "item_unidade": "diversos",
                    "valor_unitario": valor_total_geral / len(itens_lista) if itens_lista else 0, # Média para o campo unitário
                    "valor_total": valor_total_geral
                }
                
                if salvar_requisicao(conn, dados_req):
                    st.success(f"✅ Sucesso! Requisição de R$ {valor_total_geral:,.2f} registrada.")
                    st.balloons()
                    st.session_state.num_itens = 1
                    st.rerun()

# ── ABA 2 — HISTÓRICO ─────────────────────────────────────────────────────────
with aba2:
    if conn:
        df = carregar_dados(conn)
        if not df.empty:
            st.markdown(f"### 📂 Registros no PostgreSQL (`{len(df)}`)")
            df_display = df.copy()
            colunas_exibir = {
                'data': 'Data',
                'destino': 'Org',
                'fornecedor': 'Fornecedor',
                'solicitante': 'Solicitante',
                'valor_total': 'Valor Total (R$)',
                'item_descricao': 'Itens',
                'status': 'Status'
            }
            # Formatar coluna de valor para moeda
            if 'valor_total' in df_display.columns:
                df_display['valor_total'] = df_display['valor_total'].map('R$ {:,.2f}'.format)
                
            df_display = df_display[list(colunas_exibir.keys())].rename(columns=colunas_exibir)
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            import io
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df_display.to_excel(writer, index=False)
            st.download_button("⬇️ Exportar para Excel", buf.getvalue(), "requisicoes_financeiro.xlsx")
        else:
            st.info("Nenhuma requisição encontrada.")

# ── RODAPÉ ────────────────────────────────────────────────────────────────────
st.markdown(f"""<div style="text-align:center; color:{TEXTO_SEC}; font-size:11px; margin-top:40px; padding:20px; border-top:1px solid {COR_BORDA};">
<div style="font-weight:700; color:{COR_PRIMARIA}; margin-bottom:5px;">{nome_completo}</div>
Gestão Financeira Profissional baseada em PostgreSQL (Neon.tech).</div>""", unsafe_allow_html=True)
