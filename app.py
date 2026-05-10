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

# ── PALETA DE CORES MODERNA ───────────────────────────────────────────────────
COR_PRIMARIA = "#003049"  # Azul Marinho Profundo
COR_FUNDO    = "#EAF4F4"  # Sugestão do usuário: Cinza-Azulado bem claro e limpo
COR_CARD     = "#FFFFFF"  # Branco puro para os cards
COR_BORDA    = "#D8E2DC"  # Borda suave
DOURADO      = "#C8A96E"
TEXTO_SEC    = "#6C757D"

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

# ── ESTILIZAÇÃO MODERNA ───────────────────────────────────────────────────────
def aplicar_estilo():
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;0,700;1,400&family=Inter:wght@400;500;600;700&display=swap');

        /* ── Reset Global ── */
        html, body, [class*="css"] {{
            background-color: {COR_FUNDO} !important;
            color: {COR_PRIMARIA} !important;
            font-family: 'Inter', sans-serif;
        }}

        .block-container {{
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max-width: 800px;
        }}

        /* ── Cabeçalho Principal (Moderno) ── */
        .header-container {{
            background-color: {COR_PRIMARIA};
            padding: 35px 20px;
            border-radius: 15px 15px 0 0;
            text-align: center;
            border-bottom: 5px solid {DOURADO};
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}

        .header-title {{
            color: #FFFFFF;
            text-transform: uppercase;
            letter-spacing: 4px;
            font-size: 18px;
            font-weight: 800;
            margin-bottom: 5px;
        }}

        .header-subtitle {{
            color: #A0B4C8;
            font-size: 12px;
            letter-spacing: 2px;
            font-weight: 500;
        }}

        .header-quote {{
            color: {DOURADO};
            font-style: italic;
            margin-top: 15px;
            font-family: 'Crimson Pro', serif;
            font-size: 22px;
        }}

        /* ── Tabs (Estilo Pílula) ── */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: {COR_PRIMARIA} !important;
            border-radius: 0 0 15px 15px;
            padding: 5px 15px 10px;
            gap: 10px;
        }}
        .stTabs [data-baseweb="tab"] {{
            color: rgba(255,255,255,0.6) !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 8px 16px !important;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {COR_FUNDO} !important;
            color: {COR_PRIMARIA} !important;
        }}

        /* ── Cards de Seção (O segredo do "preenchimento") ── */
        .card-secao {{
            background-color: {COR_CARD};
            border-radius: 12px;
            padding: 25px;
            margin-top: 25px;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            border-left: 6px solid {COR_PRIMARIA};
        }}

        .card-titulo {{
            font-family: 'Inter', sans-serif;
            font-size: 16px;
            font-weight: 700;
            color: {COR_PRIMARIA};
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        /* ── Inputs e Widgets ── */
        div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {{
            border-radius: 8px !important;
        }}
        
        .stTextInput input, .stSelectbox div, .stTextArea textarea {{
            background-color: #F8F9FA !important;
            border: 1px solid {COR_BORDA} !important;
        }}

        /* ── Botões ── */
        .stButton > button {{
            background: linear-gradient(135deg, {COR_PRIMARIA} 0%, #005073 100%) !important;
            color: white !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            padding: 16px !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(0,48,73,0.3);
            transition: all 0.3s ease;
        }}
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 18px rgba(0,48,73,0.4);
        }}

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {{
            background-color: #FFFFFF !important;
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
    st.markdown("### 🏢 Instituição")
    org_tema = st.selectbox("Selecione a Organização", ["ASTS", "CBTS"])
    
    aplicar_estilo()
    
    logo_path = LOGOS.get(org_tema)
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### ⚙️ Configurações")
    st.caption("v3.0 - Edição Moderna")

# ── CABEÇALHO PRINCIPAL (MODERNO) ───────────────────────────────────────────
st.markdown(f"""
<div class="header-container">
    <div class="header-title">SISTEMA DE REQUISIÇÃO</div>
    <div class="header-subtitle">CONTROLE DE COMPRAS E SUPRIMENTOS</div>
    <div class="header-quote">"Jesus é tudo que você precisa!"</div>
</div>
""", unsafe_allow_html=True)

# ── ABAS ──────────────────────────────────────────────────────────────────────
aba1, aba2 = st.tabs(["📋  Nova Requisição", "📂  Histórico de Registros"])

# ── ABA 1 — FORMULÁRIO ────────────────────────────────────────────────────────
with aba1:
    sheet = conectar_sheets()
    if not sheet: st.stop()

    nome_completo = NOMES_COMPLETOS.get(org_tema, org_tema)
    
    # Card de Identificação
    st.markdown(f"""
    <div class="card-secao">
        <div class="card-titulo">🏢 {nome_completo}</div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        solicitante = st.text_input("👤 Nome do Solicitante *", placeholder="Quem está pedindo?")
    with col2:
        st.date_input("📅 Data Emissão", value=datetime.now().date(), disabled=True)

    destino = st.selectbox(f"📍 Destino da Verba ({org_tema}) *", ORGANIZACOES[org_tema])

    st.write("⚖️ **Nível de Prioridade**")
    prioridade = st.radio("P", ["🟢 NORMAL", "🟡 URGENTE", "🔴 CRÍTICO"], horizontal=True, label_visibility="collapsed")

    justificativa = st.text_area("📝 Justificativa / Finalidade *", placeholder="Descreva detalhadamente a necessidade...", height=100)
    st.markdown('</div>', unsafe_allow_html=True)

    # Card de Itens
    st.markdown("""
    <div class="card-secao">
        <div class="card-titulo">📦 Itens da Requisição</div>
    """, unsafe_allow_html=True)
    
    if "num_itens" not in st.session_state: st.session_state.num_itens = 1
    
    itens_lista = []
    for i in range(st.session_state.num_itens):
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1: d = st.text_input("Descrição do Produto/Serviço", key=f"d_{i}", placeholder=f"Ex: Papel A4")
        with c2: q = st.text_input("Qtd", key=f"q_{i}", placeholder="0")
        with c3: u = st.text_input("Unid", key=f"u_{i}", placeholder="un")
        if d: itens_lista.append(f"{d} | {q} {u}")
    
    if st.button("＋ Adicionar outro item"): 
        st.session_state.num_itens += 1
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)

    # Botão de Ação Final
    if st.button("🚀  FINALIZAR E REGISTRAR REQUISIÇÃO"):
        if not solicitante or not justificativa or not itens_lista:
            st.error("⚠️ Por favor, preencha todos os campos obrigatórios (*)")
        else:
            with st.spinner("Processando registro..."):
                id_req, data_s = gerar_id(), datetime.now().strftime("%d/%m/%Y")
                itens_s = " / ".join(itens_lista)
                linha = [id_req, data_s, org_tema, destino, solicitante, prioridade, justificativa, itens_s]
                salvar_linha(sheet, linha)
                st.success(f"✅ Sucesso! Requisição {id_req} salva no sistema.")
                st.balloons()
                st.session_state.num_itens = 1
                st.rerun()

# ── ABA 2 — HISTÓRICO ─────────────────────────────────────────────────────────
with aba2:
    sheet = conectar_sheets()
    if sheet:
        df = carregar_dados(sheet)
        if not df.empty:
            st.markdown(f"### 📂 Registros Localizados (`{len(df)}`)")
            st.dataframe(df, use_container_width=True, hide_index=True)
            import io
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)
            st.download_button("⬇️ Exportar para Excel (.xlsx)", buf.getvalue(), "requisicoes.xlsx", "application/vnd.ms-excel")
        else:
            st.info("Nenhuma requisição encontrada no banco de dados.")

# ── RODAPÉ ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center; color:{TEXTO_SEC}; font-size:11px; margin-top:40px; padding:20px; border-top:1px solid {COR_BORDA};">
    <div style="font-weight:700; color:{COR_PRIMARIA}; margin-bottom:5px;">{nome_completo}</div>
    Rua José Vicenti Vitiriti, 801 — Residencial Modelo I &nbsp;|&nbsp; (67) 99682-2052<br>
    Desenvolvido para gestão eficiente de suprimentos.
</div>
""", unsafe_allow_html=True)
