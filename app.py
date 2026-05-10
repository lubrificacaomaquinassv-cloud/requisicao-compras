import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import random
import os
import base64

# ── CONFIG GERAL ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Requisição de Compras | ASTS & CBTS",
    page_icon="📋",
    layout="centered"
)

# ── PALETA DE CORES PADRONIZADA ───────────────────────────────────────────────
COR_PRIMARIA = "#003049"  # Azul Marinho elegante para ambas as organizações
BEGE         = "#F5ECD7"
BEGE2        = "#EDE0C4"
DOURADO      = "#C8A96E"

# ── CONSTANTES ────────────────────────────────────────────────────────────────
ORGANIZACOES = {
    "ASTS": [
        "CBP", "BETHEL MUSIC", "CAT VIDA NOVA",
        "HIDROPONIA", "MARCENARIA", "PRAÇA TERRA SANTA"
    ],
    "CBTS": [
        "MIN. LOUVOR", "MIN. RECEPÇÃO", "MIN. LIBRAS",
        "MIN. CURA E LIBERTAÇÃO", "MIN. INTERCESSÃO", "MIN. MÍDIA",
        "MIN. SONOPLASTIA", "MIN. INFANTIL", "MIN. PROJEÇÃO",
        "MIN. CAPELANIA", "MIN. CÉLULAS", "MIN. REDE JOVENS",
        "MIN. TEATRO", "MIN. BENEFICÊNCIA", "MIN. PREGAÇÃO",
        "MIN. PASTORAL", "MIN. VISITAS"
    ]
}

NOMES_COMPLETOS = {
    "ASTS": "ASSOCIAÇÃO SOCIAL TERRA SANTA",
    "CBTS": "COMUNIDADE BATISTA TERRA SANTA"
}

LOGOS = {
    "ASTS": "logo_asts.png",
    "CBTS": "logo_cbts.png"
}
SHEET_NAME = "REQUISICAO_COMPRAS"
COLUNAS    = ["ID_REQUISICAO", "DATA", "ORGANIZACAO", "DESTINO",
              "SOLICITANTE", "PRIORIDADE", "JUSTIFICATIVA", "ITENS"]

# ── ESTILIZAÇÃO DINÂMICA ──────────────────────────────────────────────────────
def aplicar_estilo():
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;0,700;1,400&family=Inter:wght@400;500;600;700&display=swap');

        /* ── Reset Global ── */
        html, body, [class*="css"] {{
            background-color: {BEGE} !important;
            color: {COR_PRIMARIA} !important;
            font-family: 'Inter', sans-serif;
        }}

        .block-container {{
            padding-top: 1.5rem !important;
            padding-bottom: 1rem !important;
        }}

        /* ── Cabeçalho Principal (Título maior e destacado) ── */
        .header-container {{
            background-color: {COR_PRIMARIA};
            padding: 30px 20px;
            border-radius: 12px 12px 0 0;
            text-align: center;
            border-bottom: 4px solid {DOURADO};
            margin-bottom: 0px !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }}

        .header-title {{
            color: #A0B4C8;
            text-transform: uppercase;
            letter-spacing: 3px;
            font-size: 16px; /* Aumentado para destacar */
            font-weight: 800;
        }}

        .header-quote {{
            color: {DOURADO};
            font-style: italic;
            margin-top: 12px;
            font-family: 'Crimson Pro', serif;
            font-size: 20px; /* Aumentado proporcionalmente */
        }}

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {{
            background-color: white !important;
            border-right: 1px solid #ddd;
        }}
        
        /* ── Tabs (Coladas no Header) ── */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: {COR_PRIMARIA} !important;
            border-radius: 0 0 12px 12px;
            padding: 0 10px;
            margin-top: 0px !important;
        }}
        .stTabs [data-baseweb="tab"] {{
            color: #A0B4C8 !important;
            font-weight: 700 !important;
            height: 48px !important;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {BEGE} !important;
            color: {COR_PRIMARIA} !important;
            border-radius: 6px 6px 0 0;
        }}

        /* ── Cards de seção ── */
        .secao {{
            background-color: {BEGE2};
            border: 1px solid #D4C4A0;
            border-radius: 10px;
            padding: 22px;
            margin-top: 25px;
            margin-bottom: 25px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        .secao-titulo {{
            font-family: 'Crimson Pro', Georgia, serif;
            font-size: 19px;
            font-weight: 700;
            color: {COR_PRIMARIA};
            border-bottom: 2px solid #C8B88A;
            padding-bottom: 10px;
            margin-bottom: 18px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        /* ── Botões ── */
        .stButton > button {{
            background-color: {COR_PRIMARIA} !important;
            color: white !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
            padding: 14px !important;
            width: 100%;
            border: none !important;
            transition: 0.3s ease;
        }}
        .stButton > button:hover {{
            filter: brightness(1.2);
            transform: translateY(-1px);
        }}

        /* ── Esconder lixo ── */
        #MainMenu, footer, header {{visibility: hidden;}}
        div[data-testid="stDecoration"] {{display: none;}}
    </style>
    """, unsafe_allow_html=True)

# ── CONEXÃO SHEETS ────────────────────────────────────────────────────────────
@st.cache_resource
def conectar_sheets():
    try:
        scope  = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds  = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open(SHEET_NAME).sheet1
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

def carregar_dados(sheet):
    dados = sheet.get_all_records()
    return pd.DataFrame(dados) if dados else pd.DataFrame(columns=COLUNAS)

def salvar_linha(sheet, linha):
    sheet.append_row(linha, value_input_option="USER_ENTERED")

def gerar_id():
    d = datetime.now()
    return f"REQ-{d.strftime('%Y%m%d')}-{random.randint(1, 999):03d}"

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏢 Seleção")
    org_tema = st.selectbox("Selecione a Organização", ["ASTS", "CBTS"])
    
    # Aplicar o estilo padronizado (independente da org)
    aplicar_estilo()
    
    # Exibe a Logo na Sidebar
    logo_path = LOGOS.get(org_tema)
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### ⚙️ Configurações")
    st.caption("v2.3 - Sistema de Requisição")

# ── CABEÇALHO PRINCIPAL (TÍTULO MAIOR) ───────────────────────────────────────
st.markdown(f"""
<div class="header-container">
    <div class="header-title">SISTEMA DE REQUISIÇÃO DE COMPRAS</div>
    <div class="header-quote">"Jesus é tudo que você precisa!"</div>
</div>
""", unsafe_allow_html=True)

# ── ABAS ──────────────────────────────────────────────────────────────────────
aba1, aba2 = st.tabs(["📋  Nova Requisição", "📂  Requisições Registradas"])

# ── ABA 1 — FORMULÁRIO ────────────────────────────────────────────────────────
with aba1:
    sheet = conectar_sheets()
    if not sheet: st.stop()

    nome_completo = NOMES_COMPLETOS.get(org_tema, org_tema)
    
    # Cabeçalho de seção simplificado com ícone de prédio 🏢
    st.markdown(
        f'<div class="secao"><div class="secao-titulo">🏢 {nome_completo}</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        solicitante = st.text_input("👤 Solicitante *", placeholder="Nome completo")
    with col2:
        st.date_input("📅 Data", value=datetime.now().date(), disabled=True)

    destino = st.selectbox(f"📍 Destino ({org_tema}) *", ORGANIZACOES[org_tema])

    st.write("⚖️ **Prioridade**")
    prioridade = st.radio("P", ["🟢 NORMAL", "🟡 URGENTE", "🔴 CRÍTICO"], horizontal=True, label_visibility="collapsed")

    justificativa = st.text_area("📝 Justificativa / Finalidade *", placeholder="Descreva a necessidade...", height=100)
    st.markdown('</div>', unsafe_allow_html=True)

    # Seção de Itens
    st.markdown('<div class="secao"><div class="secao-titulo">📦 ITENS SOLICITADOS</div>', unsafe_allow_html=True)
    if "num_itens" not in st.session_state: st.session_state.num_itens = 1
    if st.button("＋ Adicionar Item"): st.session_state.num_itens += 1

    itens_lista = []
    for i in range(st.session_state.num_itens):
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1: d = st.text_input("Descrição", key=f"d_{i}", placeholder=f"Item {i+1}")
        with c2: q = st.text_input("Qtd", key=f"q_{i}")
        with c3: u = st.text_input("Unid", key=f"u_{i}", placeholder="un")
        if d: itens_lista.append(f"{d} | {q} {u}")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🚀  REGISTRAR REQUISIÇÃO"):
        if not solicitante or not justificativa or not itens_lista:
            st.error("⚠️ Preencha todos os campos obrigatórios (*)")
        else:
            with st.spinner("Salvando..."):
                id_req, data_s = gerar_id(), datetime.now().strftime("%d/%m/%Y")
                itens_s = " / ".join(itens_lista)
                linha = [id_req, data_s, org_tema, destino, solicitante, prioridade, justificativa, itens_s]
                salvar_linha(sheet, linha)
                st.success(f"✅ Requisição {id_req} registrada!")
                st.balloons()
                st.session_state.num_itens = 1

# ── ABA 2 — HISTÓRICO ─────────────────────────────────────────────────────────
with aba2:
    sheet = conectar_sheets()
    if sheet:
        df = carregar_dados(sheet)
        if not df.empty:
            st.markdown(f"### Histórico — `{len(df)} registros`")
            st.dataframe(df, use_container_width=True, hide_index=True)
            import io
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)
            st.download_button("⬇️ Baixar Excel", buf.getvalue(), "requisicoes.xlsx", "application/vnd.ms-excel")
        else:
            st.info("Nenhum registro encontrado.")

# ── RODAPÉ ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background-color:{COR_PRIMARIA}; color:#A0B4C8; text-align:center; padding:15px; border-radius:8px; margin-top:25px; border-top:3px solid {DOURADO}; font-size:12px;">
    <div style="color:white; font-weight:bold; margin-bottom:5px;">{org_tema}</div>
    Rua José Vicenti Vitiriti, 801 — Residencial Modelo I &nbsp;|&nbsp; (67) 99682-2052
</div>
""", unsafe_allow_html=True)
