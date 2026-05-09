import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import random
import os

# ── CONFIG GERAL ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Requisição de Compras | ASTS & CBTS",
    page_icon="📋",
    layout="centered"
)

# ── PALETA DE CORES ───────────────────────────────────────────────────────────
AZUL_ASTS = "#2E3192"  # Azul da logo ASTS
AZUL_CBTS = "#003049"  # Azul original do sistema
BEGE      = "#F5ECD7"
BEGE2     = "#EDE0C4"
DOURADO   = "#C8A96E"

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

LOGOS = {
    "ASTS": "logo_asts.png",
    "CBTS": "logo_cbts.png"
}

SHEET_NAME = "REQUISICAO_COMPRAS"
COLUNAS    = ["ID_REQUISICAO","DATA","ORGANIZACAO","DESTINO",
              "SOLICITANTE","PRIORIDADE","JUSTIFICATIVA","ITENS"]

# ── ESTILIZAÇÃO DINÂMICA ──────────────────────────────────────────────────────
def aplicar_estilo(cor_primaria):
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;0,700;1,400&family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {{
            background-color: {BEGE} !important;
            color: {cor_primaria} !important;
            font-family: 'Inter', sans-serif;
        }}

        /* Cabeçalho principal */
        .header-box {{
            background-color: {cor_primaria};
            padding: 28px 20px 20px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 28px;
            border-bottom: 4px solid {DOURADO};
        }}
        
        .logo-img {{
            max-width: 280px;
            background-color: white;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}

        /* Cards de seção */
        .secao {{
            background-color: {BEGE2};
            border: 1px solid #D4C4A0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 18px;
        }}
        .secao-titulo {{
            font-family: 'Crimson Pro', Georgia, serif;
            font-size: 18px;
            font-weight: 700;
            color: {cor_primaria};
            border-bottom: 1px solid #C8B88A;
            padding-bottom: 8px;
            margin-bottom: 14px;
        }}

        /* Botão primário */
        .stButton > button {{
            background-color: {cor_primaria} !important;
            color: #F5ECD7 !important;
            border: none !important;
            border-radius: 6px !important;
            font-weight: 700 !important;
            font-size: 15px !important;
            padding: 12px 28px !important;
            width: 100%;
            transition: 0.3s;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            filter: brightness(1.2);
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: {cor_primaria} !important;
            border-radius: 8px 8px 0 0;
            padding: 4px 6px 0;
        }}
        .stTabs [data-baseweb="tab"] {{
            color: #A0B4C8 !important;
            font-weight: 700 !important;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {BEGE} !important;
            color: {cor_primaria} !important;
        }}

        /* Esconde menu padrão streamlit */
        #MainMenu, footer, header {{visibility: hidden;}}
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
    return f"REQ-{d.strftime('%Y%m%d')}-{random.randint(1,999):03d}"

# ── LÓGICA DE INTERFACE ───────────────────────────────────────────────────────

# Seleção de Organização na Sidebar para definir o tema
with st.sidebar:
    st.markdown("### ⚙️ Configurações")
    org_tema = st.selectbox("Selecione a Organização", ["ASTS", "CBTS"])
    cor_tema = AZUL_ASTS if org_tema == "ASTS" else AZUL_CBTS
    aplicar_estilo(cor_tema)
    st.markdown("---")
    st.caption("v2.0 - Sistema de Requisição")

# Cabeçalho Dinâmico
st.markdown('<div class="header-box">', unsafe_allow_html=True)
logo_file = LOGOS.get(org_tema)
if os.path.exists(logo_file):
    st.image(logo_file, width=280)
else:
    st.markdown(f"<h1 style='color:white; margin:0;'>{org_tema}</h1>", unsafe_allow_html=True)

st.markdown(f"""
    <div style="color:#A0B4C8; text-transform:uppercase; letter-spacing:2.5px; font-size:11px; margin-top:8px;">Sistema de Requisição de Compras</div>
    <div style="color:{DOURADO}; font-style:italic; margin-top:12px; font-family:'Crimson Pro', serif; font-size:16px;">"Jesus é tudo que você precisa!"</div>
</div>
""", unsafe_allow_html=True)

# Abas
aba1, aba2 = st.tabs(["📋  Nova Requisição", "📂  Requisições Registradas"])

# ABA 1 - FORMULÁRIO
with aba1:
    sheet = conectar_sheets()
    if not sheet: st.stop()

    st.markdown(f'<div class="secao"><div class="secao-titulo">🆔 Identificação - {org_tema}</div>', unsafe_allow_html=True)
    
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

    st.markdown('<div class="secao"><div class="secao-titulo">📦 Itens Solicitados</div>', unsafe_allow_html=True)
    if "num_itens" not in st.session_state: st.session_state.num_itens = 1
    
    if st.button("＋ Adicionar Item"): st.session_state.num_itens += 1

    itens_lista = []
    for i in range(st.session_state.num_itens):
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1: d = st.text_input(f"Descrição", key=f"d_{i}", placeholder=f"Item {i+1}")
        with c2: q = st.text_input(f"Qtd", key=f"q_{i}")
        with c3: u = st.text_input(f"Unid", key=f"u_{i}", placeholder="un")
        if d: itens_lista.append(f"{d} | {q} {u}")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🚀  REGISTRAR REQUISIÇÃO"):
        if not solicitante or not justificativa or not itens_lista:
            st.error("⚠️ Preencha todos os campos obrigatórios (*)")
        else:
            with st.spinner('Salvando...'):
                id_req = gerar_id()
                data_s = datetime.now().strftime("%d/%m/%Y")
                itens_s = " / ".join(itens_lista)
                linha = [id_req, data_s, org_tema, destino, solicitante, prioridade, justificativa, itens_s]
                salvar_linha(sheet, linha)
                st.success(f"✅ Requisição {id_req} registrada!")
                st.balloons()
                st.session_state.num_itens = 1

# ABA 2 - HISTÓRICO
with aba2:
    sheet = conectar_sheets()
    if sheet:
        df = carregar_dados(sheet)
        if not df.empty:
            st.markdown(f"### Histórico `{len(df)} registros`")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Exportar
            import io
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)
            st.download_button("⬇️ Baixar Excel", buf.getvalue(), "requisicoes.xlsx", "application/vnd.ms-excel")
        else:
            st.info("Nenhum registro encontrado.")

# RODAPÉ
st.markdown(f"""
<div style="background-color:{cor_tema}; color:#A0B4C8; text-align:center; padding:15px; border-radius:8px; margin-top:30px; border-top:3px solid {DOURADO}; font-size:12px;">
    <div style="color:white; font-weight:bold; margin-bottom:5px;">{org_tema}</div>
    Rua José Vicenti Vitiriti, 801 — Residencial Modelo I &nbsp;|&nbsp; (67) 99682-2052
</div>
""", unsafe_allow_html=True)
