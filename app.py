import streamlit as st
import pandas as pd
from datetime import datetime
import os
from sqlalchemy import text
from fpdf import FPDF
import re

# ── CONFIGURAÇÃO DA PÁGINA ───────────────────────────────────────────────────
st.set_page_config(page_title="Sistema de Requisição - Neon V11", layout="wide", page_icon="🏢")

# ── DEFINIÇÕES DE DESIGN ─────────────────────────────────────────────────────
COR_PRIMARIA = "#003049"
COR_SECUNDARIA = "#669BBC"
COR_FUNDO = "#EAF4F4"
COR_CARD = "#FFFFFF"
COR_BORDA = "#D8E2DC"
TEXTO_SEC = "#6C757D"

def aplicar_estilo():
    st.markdown(f"""
    <style>
    .stApp {{ background-color: {COR_FUNDO}; }}
    div[data-testid="stDecoration"] {{ display: none; }}
    .block-container {{ padding-top: 1.5rem !important; }}
    .header-container {{
        background: {COR_PRIMARIA}; padding: 25px 20px; border-radius: 12px 12px 0 0;
        text-align: center; color: white; margin-bottom: 0px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    .header-title {{ font-size: 32px; font-weight: 800; letter-spacing: 2px; margin-bottom: 5px; }}
    .header-subtitle {{ font-size: 14px; text-transform: uppercase; letter-spacing: 4px; opacity: 0.9; }}
    .header-quote {{ font-family: 'Georgia', serif; font-style: italic; font-size: 16px; margin-top: 15px; color: #fdf0d5; }}
    .endereco-box {{ background: #f0f4f8; padding: 12px; border-radius: 8px; border-left: 4px solid {COR_PRIMARIA}; margin: 15px 0; font-size: 13px; color: {TEXTO_SEC}; }}
    .stTabs [data-baseweb="tab-list"] {{ background-color: {COR_PRIMARIA}; padding: 5px 15px; border-radius: 0 0 12px 12px; gap: 10px; }}
    .stTabs [data-baseweb="tab"] {{ color: rgba(255,255,255,0.6) !important; background: transparent !important; }}
    .stTabs [aria-selected="true"] {{ color: white !important; border-bottom: 3px solid white !important; }}
    .card-secao {{ background: {COR_CARD}; padding: 25px; border-radius: 12px; border-left: 6px solid {COR_PRIMARIA}; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-top: 25px; margin-bottom: 25px; }}
    .card-titulo {{ font-size: 18px; font-weight: 700; color: {COR_PRIMARIA}; margin-bottom: 20px; border-bottom: 1px solid {COR_BORDA}; padding-bottom: 10px; }}
    div.stButton > button {{ width: 100%; background: linear-gradient(135deg, {COR_PRIMARIA} 0%, {COR_SECUNDARIA} 100%); color: white !important; border: none; padding: 12px; font-weight: 700; border-radius: 8px; }}
    .sidebar-footer {{ text-align: center; font-size: 12px; color: {TEXTO_SEC}; margin-top: 20px; padding-top: 15px; border-top: 1px solid {COR_BORDA}; }}
    </style>
    """, unsafe_allow_html=True)

# ── CONSTANTES ───────────────────────────────────────────────────────────────
ORGANIZACOES = {
    "CBTS": [
        "MIN. INFANTIL", "MIN. LIBRAS", "SECRETARIA ADM", "MIN. INTERCESSAO", 
        "MIN. CURA E LIBERTACAO", "MIN. BENEFICENCIA", "MIN. RECEPCAO", 
        "MIN. PROJECAO", "MIN. MIDIA", "MIN. EVENTOS", "MIN. VISISTAS", 
        "MIN. CAPELANIA", "MIN. LOUVOR", "MIN. PASTORAL", "MIN. PATRIMONIO", 
        "MIN. CELULAS FAMILIARES"
    ],
    "ASTS": [
        "CBP", "MARCENARIA", "BETHEL MUSIC", "CAT - VIDA NOVA", 
        "HIDROPONIA", "PRAÇA TERRA SANTA"
    ]
}

NOMES_COMPLETOS = {
    "ASTS": "ASSOCIAÇÃO SOCIAL TERRA SANTA", 
    "CBTS": "COMUNIDADE BATISTA TERRA SANTA"
}

ENDERECOS = {
    "ASTS": "Rua José Vicenti Vitiriti - 801 Res. Modelo I",
    "CBTS": "Rua José Vicenti Vitiriti - 801 Res. Modelo I"
}

# ── FUNÇÃO PARA BUSCAR LOGO ──────────────────────────────────────────────────
def buscar_logo(org):
    nomes_arquivos = [f"logo_{org.lower()}.png", f"logo_{org.lower()}.jpg", f"{org.lower()}.png"]
    caminhos_possiveis = [".", "assets", "images", "upload"]
    for pasta in caminhos_possiveis:
        for nome in nomes_arquivos:
            caminho = os.path.join(pasta, nome)
            if os.path.exists(caminho):
                return caminho
    return None

# ── FUNÇÃO DE LIMPEZA DE TEXTO PARA PDF ──────────────────────────────────────
def limpar_texto(texto):
    if not texto: 
        return ""
    texto = str(texto).replace("🟢 ", "").replace("🟡 ", "").replace("🔴 ", "")
    texto = re.sub(r'[^\x00-\x7F]+', '', texto)
    return texto.strip()

# ── FUNÇÃO PARA GERAR NÚMERO DE REQUISIÇÃO ──────────────────────────────────
def gerar_numero_requisicao(conn):
    """Gera um número sequencial único para a requisição"""
    try:
        with conn.session as s:
            resultado = s.execute(text("SELECT MAX(id) as max_id FROM requisicoes")).first()
            max_id = resultado[0] if resultado and resultado[0] else 0
            numero = max_id + 1
            return f"REQ-{numero:06d}"
    except Exception as e:
        st.warning(f"Usando timestamp como fallback: {e}")
        return f"REQ-{int(datetime.now().timestamp())}"

# ── FUNÇÃO GERADORA DE PDF (OTIMIZADA) ───────────────────────────────────────
def gerar_pdf_otimizado(dados, itens, nome_org, numero_requisicao, endereco):
    """Gera PDF de forma rápida e eficiente"""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=10)
        
        # Cabeçalho
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 8, 'REQUISICAO DE COMPRAS / SERVICOS', 0, 1, 'C')
        pdf.ln(3)
        
        # Informações principais
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 6, f"NUMERO: {numero_requisicao}", 0, 1, 'R')
        
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(0, 6, f"INSTITUICAO: {limpar_texto(nome_org)}", 0, 1)
        pdf.cell(0, 6, f"ENDERECO: {limpar_texto(endereco)}", 0, 1)
        pdf.cell(0, 6, f"DATA: {dados['data'].strftime('%d/%m/%Y')}", 0, 1)
        pdf.ln(3)
        
        # Seção de informações gerais
        pdf.set_fill_color(200, 220, 220)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(0, 6, 'INFORMACOES GERAIS', 0, 1, 'L', True)
        
        pdf.set_font('Helvetica', '', 8)
        pdf.cell(95, 5, f"Solicitante: {limpar_texto(dados['solicitante'])}", 1, 0)
        pdf.cell(95, 5, f"Setor: {limpar_texto(dados['cbp'])}", 1, 1)
        pdf.cell(95, 5, f"Prioridade: {limpar_texto(dados['prioridade'])}", 1, 0)
        pdf.cell(95, 5, f"Fornecedor: {limpar_texto(dados['fornecedor'])}", 1, 1)
        pdf.ln(2)
        
        # Justificativa
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(0, 6, 'JUSTIFICATIVA', 0, 1, 'L', True)
        pdf.set_font('Helvetica', '', 8)
        pdf.multi_cell(0, 4, limpar_texto(dados['justificativa']), 0)
        pdf.ln(2)
        
        # Tabela de itens
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_fill_color(200, 220, 220)
        pdf.cell(70, 6, 'ITEM', 1, 0, 'L', True)
        pdf.cell(20, 6, 'QTD', 1, 0, 'C', True)
        pdf.cell(30, 6, 'VALOR UN.', 1, 0, 'R', True)
        pdf.cell(30, 6, 'TOTAL', 1, 1, 'R', True)
        
        pdf.set_font('Helvetica', '', 8)
        for item in itens:
            desc = limpar_texto(item['d'])[:40]
            pdf.cell(70, 5, desc, 1, 0)
            pdf.cell(20, 5, f"{item['q']} {limpar_texto(item['u'])}", 1, 0, 'C')
            pdf.cell(30, 5, f"R$ {item['v']:.2f}", 1, 0, 'R')
            pdf.cell(30, 5, f"R$ {item['t']:.2f}", 1, 1, 'R')
        
        # Total
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_fill_color(200, 220, 220)
        pdf.cell(120, 6, 'TOTAL GERAL', 1, 0, 'R', True)
        pdf.cell(30, 6, f"R$ {dados['valor_total']:.2f}", 1, 1, 'R', True)
        
        # Assinaturas
        pdf.ln(10)
        pdf.set_font('Helvetica', '', 8)
        pdf.cell(90, 0, '', 'T', 0)
        pdf.cell(10, 0, '', 0, 0)
        pdf.cell(90, 0, '', 'T', 1)
        pdf.cell(90, 8, 'Assinatura do Solicitante', 0, 0, 'C')
        pdf.cell(10, 8, '', 0, 0)
        pdf.cell(90, 8, 'Autorizacao / Diretoria', 0, 1, 'C')
        
        return bytes(pdf.output())
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {e}")
        return None

# ── CONEXÃO E FUNÇÕES ────────────────────────────────────────────────────────
def conectar():
    return st.connection("postgresql", type="sql")

def salvar_requisicao(conn, d, numero_req):
    try:
        with conn.session as s:
            query = text("""
                INSERT INTO requisicoes (
                    numero_requisicao, solicitante, data, destino, cbp, prioridade, justificativa,
                    fornecedor, item_descricao, item_quantidade, item_unidade, 
                    valor_unitario, valor_total
                ) VALUES (
                    :numero_requisicao, :solicitante, :data, :destino, :cbp, :prioridade, :justificativa,
                    :fornecedor, :item_descricao, :item_quantidade, :item_unidade,
                    :valor_unitario, :valor_total
                )
            """)
            d['numero_requisicao'] = numero_req
            s.execute(query, d)
            s.commit()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao salvar: {e}")
        return False

# ── INTERFACE ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏢 Instituição")
    org_tema = st.selectbox("Selecione a Organização", ["ASTS", "CBTS"])
    aplicar_estilo()
    logo_path = buscar_logo(org_tema)
    if logo_path: 
        st.image(logo_path, use_container_width=True)
    
    st.markdown("""
    <div class="sidebar-footer">
    <p><strong>System created on 23 Iyar</strong></p>
    </div>
    """, unsafe_allow_html=True)
    st.caption("v15.1 - Fast PDF")

st.markdown(f"""<div class="header-container"><div class="header-title">SISTEMA DE REQUISIÇÃO</div><div class="header-subtitle">CONTROLE FINANCEIRO E DE SUPRIMENTOS</div><div class="header-quote">"Jesus é tudo que você precisa!"</div></div>""", unsafe_allow_html=True)

conn = conectar()
aba1, aba2 = st.tabs(["📋 Nova Requisição", "📂 Histórico"])

with aba1:
    nome_completo = NOMES_COMPLETOS.get(org_tema)
    endereco = ENDERECOS.get(org_tema, "Endereço não configurado")
    
    st.markdown(f"""<div class="card-secao"><div class="card-titulo">🏢 {nome_completo}</div>""", unsafe_allow_html=True)
    
    # Exibir endereço
    st.markdown(f"""<div class="endereco-box">📍 <strong>{endereco}</strong></div>""", unsafe_allow_html=True)
    
    c1, c2 = st.columns([2, 1])
    with c1: 
        solicitante = st.text_input("👤 Solicitante *")
    with c2: 
        data_emissao = st.date_input("📅 Data", value=datetime.now().date(), disabled=True)
    
    fornecedor = st.text_input("🏪 Fornecedor")
    
    c3, c4 = st.columns(2)
    with c3: 
        destino = st.selectbox(f"📍 Destino ({org_tema}) *", ORGANIZACOES[org_tema])
    with c4: 
        prioridade = st.radio("Prioridade", ["🟢 NORMAL", "🟡 URGENTE", "🔴 CRÍTICO"], horizontal=True)
    
    justificativa = st.text_area("📝 Justificativa *")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""<div class="card-secao"><div class="card-titulo">📦 Itens e Valores</div>""", unsafe_allow_html=True)
    if "n_itens" not in st.session_state: 
        st.session_state.n_itens = 1
    
    itens = []
    total_geral = 0.0
    
    for i in range(st.session_state.n_itens):
        col_d, col_q, col_u, col_v = st.columns([3, 1, 1, 2])
        with col_d: 
            d = st.text_input("Descrição", key=f"d_{i}")
        with col_q: 
            q = st.number_input("Qtd", key=f"q_{i}", min_value=1)
        with col_u: 
            u = st.text_input("Un", key=f"u_{i}")
        with col_v: 
            v = st.number_input("R$ Unit.", key=f"v_{i}", min_value=0.0)
        
        if d:
            total_item = q * v
            itens.append({"d": d, "q": q, "u": u, "v": v, "t": total_item})
            total_geral += total_item
    
    st.markdown(f"### 💰 Total: **R$ {total_geral:,.2f}**")
    
    if st.button("＋ Item"): 
        st.session_state.n_itens += 1
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🚀 REGISTRAR REQUISIÇÃO"):
        if not solicitante or not justificativa or not itens:
            st.error("❌ Preencha os campos obrigatórios.")
        else:
            with st.spinner("⏳ Processando requisição..."):
                numero_requisicao = gerar_numero_requisicao(conn)
                
                itens_str = " / ".join([f"{i['d']} ({i['q']} {i['u']})" for i in itens])
                dados = {
                    "solicitante": solicitante, 
                    "data": data_emissao, 
                    "destino": org_tema,
                    "cbp": destino, 
                    "prioridade": prioridade, 
                    "justificativa": justificativa,
                    "fornecedor": fornecedor, 
                    "item_descricao": itens_str, 
                    "item_quantidade": sum([i['q'] for i in itens]),
                    "item_unidade": "diversos", 
                    "valor_unitario": total_geral/len(itens) if itens else 0, 
                    "valor_total": total_geral
                }
                
                if salvar_requisicao(conn, dados, numero_requisicao):
                    st.success(f"✅ Requisição {numero_requisicao} registrada com sucesso!")
                    st.balloons()
                    
                    pdf_final = gerar_pdf_otimizado(dados, itens, nome_completo, numero_requisicao, endereco)
                    
                    if pdf_final:
                        st.download_button(
                            label="📄 BAIXAR REQUISIÇÃO EM PDF",
                            data=pdf_final,
                            file_name=f"{numero_requisicao}_{solicitante}_{datetime.now().strftime('%d%m%Y')}.pdf",
                            mime="application/pdf"
                        )
                    
                    st.session_state.n_itens = 1

with aba2:
    try:
        df = conn.query("SELECT numero_requisicao, data, fornecedor, solicitante, valor_total, item_descricao FROM requisicoes ORDER BY data DESC LIMIT 100", ttl=0)
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else: 
            st.info("📭 Sem registros.")
    except Exception as e: 
        st.error(f"Erro ao carregar histórico: {e}")
