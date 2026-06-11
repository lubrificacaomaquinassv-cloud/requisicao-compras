import streamlit as st
import pandas as pd
from datetime import datetime
import os
from sqlalchemy import text
from fpdf import FPDF
import re

# ── CONFIGURAÇÃO ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sistema de Requisição",
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="collapsed",
)

NUMERO_INICIAL = 50  # primeira requisição do mês: REQ-06-00050

COR_PRIMARIA = "#003049"
COR_SECUNDARIA = "#669BBC"
COR_ACCENT = "#C1121F"
COR_FUNDO = "#F4F7F9"
COR_CARD = "#FFFFFF"
COR_BORDA = "#E2E8F0"
TEXTO_SEC = "#64748B"

ORGANIZACOES = {
    "CBTS": [
        "MIN. INFANTIL", "MIN. LIBRAS", "SECRETARIA ADM", "MIN. INTERCESSAO",
        "MIN. CURA E LIBERTACAO", "MIN. BENEFICENCIA", "MIN. RECEPCAO",
        "MIN. PROJECAO", "MIN. MIDIA", "MIN. EVENTOS", "MIN. VISISTAS",
        "MIN. CAPELANIA", "MIN. LOUVOR", "MIN. PASTORAL", "MIN. PATRIMONIO",
        "MIN. CELULAS FAMILIARES",
    ],
    "ASTS": [
        "CASA BOM PASTOR", "ADM - ASTS", "MARCENARIA", "BETHEL MUSIC",
        "CAT - VIDA NOVA", "HIDROPONIA", "PRAÇA TERRA SANTA",
    ],
}

NOMES_COMPLETOS = {
    "ASTS": "ASSOCIAÇÃO SOCIAL TERRA SANTA",
    "CBTS": "COMUNIDADE BATISTA TERRA SANTA",
}

ENDERECOS = {
    "ASTS": "Rua Bertoldo Borges - 50 JD Santa Maria",
    "CBTS": "Rua José Vicenti Vitiriti - 801 Res. Modelo I",
}

ORG_CORES = {
    "ASTS": "#1D4ED8",
    "CBTS": "#003049",
}


def aplicar_estilo():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] {{ font-family: 'DM Sans', sans-serif; }}
        .stApp {{ background: linear-gradient(160deg, {COR_FUNDO} 0%, #E8EEF2 100%); }}
        [data-testid="stSidebar"] {{ display: none; }}
        [data-testid="stDecoration"] {{ display: none; }}
        .block-container {{
            padding: 1.2rem 2rem 2rem 2rem !important;
            max-width: 1400px !important;
        }}
        .hero {{
            background: linear-gradient(135deg, {COR_PRIMARIA} 0%, #1a4a6e 50%, {COR_SECUNDARIA} 100%);
            border-radius: 16px;
            padding: 28px 32px;
            color: white;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0,48,73,0.18);
        }}
        .hero h1 {{
            font-size: 1.75rem; font-weight: 700; margin: 0;
            letter-spacing: 0.04em;
        }}
        .hero p {{
            margin: 6px 0 0 0; opacity: 0.85; font-size: 0.85rem;
            text-transform: uppercase; letter-spacing: 0.12em;
        }}
        .hero em {{
            display: block; margin-top: 12px; font-style: italic;
            font-size: 0.95rem; opacity: 0.9; color: #fdf0d5;
        }}
        .painel-org {{
            background: {COR_CARD};
            border-radius: 14px;
            padding: 16px 14px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.05);
            border: 1px solid {COR_BORDA};
            position: sticky;
            top: 1rem;
            max-width: 220px;
        }}
        .painel-org h3 {{
            font-size: 0.68rem; text-transform: uppercase;
            letter-spacing: 0.1em; color: {TEXTO_SEC};
            margin: 0 0 10px 2px; font-weight: 600;
        }}
        .painel-org div.stButton > button {{
            padding: 6px 8px !important;
            font-size: 0.82rem !important;
            min-height: 36px !important;
        }}
        .card-org {{
            border: 2px solid {COR_BORDA};
            border-radius: 12px;
            padding: 14px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.2s ease;
            background: #FAFBFC;
        }}
        .card-org.ativo {{
            border-color: {COR_PRIMARIA};
            background: linear-gradient(135deg, #f0f7fa 0%, #e8f4f8 100%);
            box-shadow: 0 4px 12px rgba(0,48,73,0.12);
        }}
        .card-org .sigla {{
            font-size: 1.1rem; font-weight: 700; color: {COR_PRIMARIA};
        }}
        .card-org .nome {{
            font-size: 0.7rem; color: {TEXTO_SEC}; margin-top: 4px; line-height: 1.3;
        }}
        .logo-box {{
            margin-top: 12px;
            padding: 8px 6px;
            background: transparent;
            border-radius: 10px;
            text-align: center;
        }}
        .logo-box [data-testid="stImage"] {{
            display: flex;
            justify-content: center;
        }}
        .logo-box [data-testid="stImage"] img {{
            max-width: 118px !important;
            width: 118px !important;
            height: auto !important;
            margin: 0 auto;
            opacity: 0.95;
        }}
        .badge-supabase {{
            display: inline-block;
            background: #3ECF8E22;
            color: #1a7f4e;
            font-size: 0.65rem;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 20px;
            margin-top: 12px;
        }}
        .form-card {{
            background: {COR_CARD};
            border-radius: 16px;
            padding: 24px 28px;
            margin-bottom: 20px;
            box-shadow: 0 2px 16px rgba(0,0,0,0.04);
            border: 1px solid {COR_BORDA};
        }}
        .form-card h4 {{
            color: {COR_PRIMARIA};
            font-size: 1rem;
            font-weight: 700;
            margin: 0 0 18px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid {COR_BORDA};
        }}
        .org-header {{
            display: flex; align-items: center; gap: 12px;
            margin-bottom: 16px;
        }}
        .org-header .dot {{
            width: 10px; height: 10px; border-radius: 50%;
            background: {COR_SECUNDARIA};
        }}
        .endereco-tag {{
            background: #F1F5F9;
            border-left: 4px solid {COR_PRIMARIA};
            padding: 10px 14px;
            border-radius: 0 8px 8px 0;
            font-size: 0.85rem;
            color: {TEXTO_SEC};
            margin-bottom: 18px;
        }}
        .total-box {{
            background: linear-gradient(135deg, {COR_PRIMARIA}, {COR_SECUNDARIA});
            color: white;
            padding: 16px 24px;
            border-radius: 12px;
            font-size: 1.3rem;
            font-weight: 700;
            text-align: center;
            margin: 16px 0;
        }}
        div[data-testid="stTabs"] [data-baseweb="tab-list"] {{
            background: transparent;
            gap: 8px;
            border-bottom: 2px solid {COR_BORDA};
        }}
        div[data-testid="stTabs"] [data-baseweb="tab"] {{
            background: transparent !important;
            color: {TEXTO_SEC} !important;
            font-weight: 600;
            border-radius: 8px 8px 0 0;
        }}
        div[data-testid="stTabs"] [aria-selected="true"] {{
            color: {COR_PRIMARIA} !important;
            border-bottom: 3px solid {COR_ACCENT} !important;
        }}
        div.stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, {COR_PRIMARIA}, {COR_SECUNDARIA}) !important;
            border: none !important;
            font-weight: 700 !important;
            border-radius: 10px !important;
            padding: 12px 24px !important;
        }}
        div.stButton > button[kind="secondary"] {{
            border-radius: 10px !important;
            font-weight: 600 !important;
        }}
        .footer-info {{
            text-align: center;
            font-size: 0.7rem;
            color: {TEXTO_SEC};
            margin-top: 20px;
            padding-top: 14px;
            border-top: 1px solid {COR_BORDA};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource
def buscar_logo(org):
    nomes = [
        f"logo_{org.lower()}.png", f"logo_{org.lower()}.jpg",
        f"{org.lower()}.png", f"{org.lower()}.jpg",
    ]
    pastas = ["assets", "images", "/home/ubuntu/upload", "."]
    for pasta in pastas:
        for nome in nomes:
            caminho = os.path.join(pasta, nome)
            if os.path.exists(caminho):
                return caminho
    return None


def limpar_texto(texto):
    if not texto:
        return ""
    texto = str(texto).replace("🟢 ", "").replace("🟡 ", "").replace("🔴 ", "")
    texto = re.sub(r"[^\x00-\x7F]+", "", texto)
    return texto.strip()


def conectar():
    return st.connection("supabase", type="sql")


def gerar_numero_requisicao(conn):
    """
    Formato: REQ-MM-NNNNN
    Exemplo: REQ-06-00050 (mês 06, sequência a partir de 50)
    Reinicia a cada mês.
    """
    mes = datetime.now().strftime("%m")
    prefixo = f"REQ-{mes}-"
    padrao = f"^REQ-{mes}-[0-9]{{5}}$"

    try:
        with conn.session as s:
            resultado = s.execute(
                text("""
                    SELECT COALESCE(
                        MAX(CAST(SUBSTRING(numero_requisicao FROM 8) AS INTEGER)),
                        :inicial - 1
                    ) AS maximo
                    FROM requisicoes
                    WHERE numero_requisicao ~ :padrao
                """),
                {"padrao": padrao, "inicial": NUMERO_INICIAL},
            ).first()

            numero = (resultado[0] if resultado and resultado[0] is not None else NUMERO_INICIAL - 1) + 1
            if numero < NUMERO_INICIAL:
                numero = NUMERO_INICIAL

            while True:
                candidato = f"{prefixo}{numero:05d}"
                existe = s.execute(
                    text("SELECT 1 FROM requisicoes WHERE numero_requisicao = :n"),
                    {"n": candidato},
                ).first()
                if not existe:
                    return candidato
                numero += 1

    except Exception as e:
        st.warning(f"Numeração alternativa: {e}")
        return f"REQ-{mes}-{int(datetime.now().timestamp()) % 100000:05d}"


def salvar_requisicao(conn, d, numero_req):
    try:
        with conn.session as s:
            s.execute(
                text("""
                    INSERT INTO requisicoes (
                        numero_requisicao, solicitante, data, destino, cbp,
                        prioridade, justificativa, fornecedor, item_descricao,
                        item_quantidade, item_unidade, valor_unitario, valor_total
                    ) VALUES (
                        :numero_requisicao, :solicitante, :data, :destino, :cbp,
                        :prioridade, :justificativa, :fornecedor, :item_descricao,
                        :item_quantidade, :item_unidade, :valor_unitario, :valor_total
                    )
                """),
                {**d, "numero_requisicao": numero_req},
            )
            s.commit()
        return True, None
    except Exception as e:
        return False, str(e)


def parse_itens_descricao(descricao, valor_total):
    """Reconstrói itens a partir do texto salvo no banco para reimpressão."""
    if not descricao:
        return [{"d": "Item", "q": 1, "u": "un", "v": float(valor_total), "t": float(valor_total)}]

    itens = []
    for parte in str(descricao).split(" / "):
        parte = parte.strip()
        m = re.match(r"^(.+?)\s+\((\d+)\s+([^)]+)\)$", parte)
        if m:
            itens.append({"d": m.group(1), "q": int(m.group(2)), "u": m.group(3), "v": 0.0, "t": 0.0})
        elif parte:
            itens.append({"d": parte, "q": 1, "u": "un", "v": 0.0, "t": 0.0})

    if not itens:
        return [{"d": str(descricao), "q": 1, "u": "un", "v": float(valor_total), "t": float(valor_total)}]

    total = float(valor_total)
    if len(itens) == 1:
        itens[0]["v"] = total / itens[0]["q"] if itens[0]["q"] else total
        itens[0]["t"] = total
    else:
        parte_valor = total / len(itens)
        for item in itens:
            item["t"] = parte_valor
            item["v"] = parte_valor / item["q"] if item["q"] else parte_valor
    return itens


def buscar_requisicao(conn, numero):
    with conn.session as s:
        row = s.execute(
            text("""
                SELECT numero_requisicao, solicitante, data, destino, cbp, prioridade,
                       justificativa, fornecedor, item_descricao, item_quantidade,
                       item_unidade, valor_unitario, valor_total
                FROM requisicoes
                WHERE numero_requisicao = :numero
                LIMIT 1
            """),
            {"numero": numero},
        ).mappings().first()
    return dict(row) if row else None


def gerar_pdf_do_banco(row):
    """Gera PDF a partir de um registro salvo no Supabase."""
    destino = row["destino"]
    nome_org = NOMES_COMPLETOS.get(destino, destino)
    endereco = ENDERECOS.get(destino, "")
    data_val = row["data"]
    if not hasattr(data_val, "strftime"):
        data_val = pd.to_datetime(data_val).date()

    dados = {
        "solicitante": row["solicitante"],
        "data": data_val,
        "cbp": row["cbp"],
        "prioridade": row["prioridade"] or "NORMAL",
        "justificativa": row["justificativa"],
        "fornecedor": row["fornecedor"] or "",
        "valor_total": float(row["valor_total"]),
    }
    itens = parse_itens_descricao(row["item_descricao"], row["valor_total"])
    return gerar_pdf(dados, itens, nome_org, row["numero_requisicao"], endereco)


def gerar_pdf(dados, itens, nome_org, numero_requisicao, endereco):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=10)

        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 8, "REQUISICAO DE COMPRAS / SERVICOS", 0, 1, "C")
        pdf.ln(3)

        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, f"NUMERO: {numero_requisicao}", 0, 1, "R")
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 6, f"INSTITUICAO: {limpar_texto(nome_org)}", 0, 1)
        pdf.cell(0, 6, f"ENDERECO: {limpar_texto(endereco)}", 0, 1)
        pdf.cell(0, 6, f"DATA: {dados['data'].strftime('%d/%m/%Y')}", 0, 1)
        pdf.ln(3)

        pdf.set_fill_color(200, 220, 220)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 6, "INFORMACOES GERAIS", 0, 1, "L", True)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(95, 5, f"Solicitante: {limpar_texto(dados['solicitante'])}", 1, 0)
        pdf.cell(95, 5, f"Setor: {limpar_texto(dados['cbp'])}", 1, 1)
        pdf.cell(95, 5, f"Prioridade: {limpar_texto(dados['prioridade'])}", 1, 0)
        pdf.cell(95, 5, f"Fornecedor: {limpar_texto(dados['fornecedor'])}", 1, 1)
        pdf.ln(2)

        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 6, "JUSTIFICATIVA", 0, 1, "L", True)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(0, 4, limpar_texto(dados["justificativa"]), 0)
        pdf.ln(2)

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(200, 220, 220)
        pdf.cell(70, 6, "ITEM", 1, 0, "L", True)
        pdf.cell(20, 6, "QTD", 1, 0, "C", True)
        pdf.cell(30, 6, "VALOR UN.", 1, 0, "R", True)
        pdf.cell(30, 6, "TOTAL", 1, 1, "R", True)

        pdf.set_font("Helvetica", "", 8)
        for item in itens:
            pdf.cell(70, 5, limpar_texto(item["d"])[:40], 1, 0)
            pdf.cell(20, 5, f"{item['q']} {limpar_texto(item['u'])}", 1, 0, "C")
            pdf.cell(30, 5, f"R$ {item['v']:.2f}", 1, 0, "R")
            pdf.cell(30, 5, f"R$ {item['t']:.2f}", 1, 1, "R")

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(200, 220, 220)
        pdf.cell(120, 6, "TOTAL GERAL", 1, 0, "R", True)
        pdf.cell(30, 6, f"R$ {dados['valor_total']:.2f}", 1, 1, "R", True)

        pdf.ln(10)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(90, 0, "", "T", 0)
        pdf.cell(10, 0, "", 0, 0)
        pdf.cell(90, 0, "", "T", 1)
        pdf.cell(90, 8, "Assinatura do Solicitante", 0, 0, "C")
        pdf.cell(10, 8, "", 0, 0)
        pdf.cell(90, 8, "Autorizacao / Diretoria", 0, 1, "C")

        return bytes(pdf.output())
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {e}")
        return None


def render_painel_selecao(org_atual):
    st.markdown('<div class="painel-org"><h3>Instituição</h3>', unsafe_allow_html=True)

    bc_asts, bc_cbts = st.columns(2, gap="small")
    for col, org in [(bc_asts, "ASTS"), (bc_cbts, "CBTS")]:
        with col:
            if st.button(
                org,
                key=f"btn_org_{org}",
                use_container_width=True,
                type="primary" if org == org_atual else "secondary",
                help=NOMES_COMPLETOS[org],
            ):
                st.session_state.org_tema = org
                st.rerun()

    st.markdown('<div class="logo-box">', unsafe_allow_html=True)
    logo = buscar_logo(org_atual)
    if logo:
        st.image(logo, width=118)
    else:
        st.markdown(
            f'<p style="color:{TEXTO_SEC};font-size:0.8rem;">Logo {org_atual}<br>'
            f'<small>Coloque em assets/logo_{org_atual.lower()}.png</small></p>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    mes_atual = datetime.now().strftime("%m")
    st.markdown(
        f'<span class="badge-supabase">Supabase · REQ-{mes_atual}-{NUMERO_INICIAL:05d}+</span>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="footer-info"><strong>System created on 23 Iyar</strong><br>v16.2 · Nova base</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


# ── INICIALIZAÇÃO ─────────────────────────────────────────────────────────────
aplicar_estilo()

if "org_tema" not in st.session_state:
    st.session_state.org_tema = "CBTS"

org_tema = st.session_state.org_tema
nome_completo = NOMES_COMPLETOS[org_tema]
endereco = ENDERECOS[org_tema]

st.markdown(
    """
    <div class="hero">
        <h1>SISTEMA DE REQUISIÇÃO</h1>
        <p>Controle Financeiro e de Suprimentos</p>
        <em>"Jesus é tudo que você precisa!"</em>
    </div>
    """,
    unsafe_allow_html=True,
)

col_painel, col_main = st.columns([0.75, 3.5], gap="medium")

with col_painel:
    render_painel_selecao(org_tema)

with col_main:
    try:
        conn = conectar()
    except Exception as e:
        st.error(
            f"Não foi possível conectar ao Supabase. "
            f"Configure os secrets (veja `.streamlit/secrets.toml.example`).\n\nDetalhe: {e}"
        )
        st.stop()

    aba_nova, aba_hist = st.tabs(["Nova Requisição", "Histórico"])

    with aba_nova:
        st.markdown('<div class="form-card">', unsafe_allow_html=True)
        st.markdown(
            f'<div class="org-header"><span class="dot"></span>'
            f'<h4 style="margin:0;border:none;padding:0;">{nome_completo}</h4></div>',
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="endereco-tag">📍 {endereco}</div>', unsafe_allow_html=True)

        c1, c2 = st.columns([2, 1])
        with c1:
            solicitante = st.text_input("Solicitante *", placeholder="Nome completo")
        with c2:
            data_emissao = st.date_input("Data", value=datetime.now().date(), disabled=True)

        fornecedor = st.text_input("Fornecedor", placeholder="Nome do fornecedor")

        c3, c4 = st.columns(2)
        with c3:
            destino = st.selectbox(f"Destino ({org_tema}) *", ORGANIZACOES[org_tema])
        with c4:
            prioridade = st.radio(
                "Prioridade",
                ["NORMAL", "URGENTE", "CRITICO"],
                horizontal=True,
                format_func=lambda x: {"NORMAL": "🟢 Normal", "URGENTE": "🟡 Urgente", "CRITICO": "🔴 Crítico"}[x],
            )

        justificativa = st.text_area("Justificativa *", placeholder="Descreva o motivo da requisição...", height=100)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="form-card"><h4>Itens e Valores</h4>', unsafe_allow_html=True)

        if "n_itens" not in st.session_state:
            st.session_state.n_itens = 1

        itens = []
        total_geral = 0.0

        for i in range(st.session_state.n_itens):
            col_d, col_q, col_u, col_v = st.columns([3, 1, 1, 2])
            with col_d:
                d = st.text_input("Descrição", key=f"d_{i}", placeholder="Item ou serviço")
            with col_q:
                q = st.number_input("Qtd", key=f"q_{i}", min_value=1)
            with col_u:
                u = st.text_input("Un", key=f"u_{i}", placeholder="un")
            with col_v:
                v = st.number_input("R$ Unit.", key=f"v_{i}", min_value=0.0, format="%.2f")

            if d:
                total_item = q * v
                itens.append({"d": d, "q": q, "u": u, "v": v, "t": total_item})
                total_geral += total_item

        st.markdown(f'<div class="total-box">Total: R$ {total_geral:,.2f}</div>', unsafe_allow_html=True)

        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("＋ Adicionar item", use_container_width=True):
                st.session_state.n_itens += 1
                st.rerun()
        with bc2:
            registrar = st.button("Registrar Requisição", type="primary", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

        if registrar:
            if not solicitante or not justificativa or not itens:
                st.error("Preencha solicitante, justificativa e ao menos um item.")
            else:
                with st.spinner("Processando..."):
                    numero = gerar_numero_requisicao(conn)
                    itens_str = " / ".join(f"{i['d']} ({i['q']} {i['u']})" for i in itens)
                    dados = {
                        "solicitante": solicitante,
                        "data": data_emissao,
                        "destino": org_tema,
                        "cbp": destino,
                        "prioridade": prioridade,
                        "justificativa": justificativa,
                        "fornecedor": fornecedor or "",
                        "item_descricao": itens_str,
                        "item_quantidade": sum(i["q"] for i in itens),
                        "item_unidade": "diversos",
                        "valor_unitario": total_geral / len(itens) if itens else 0,
                        "valor_total": total_geral,
                    }

                    ok, erro = salvar_requisicao(conn, dados, numero)
                    if ok:
                        st.session_state.n_itens = 1
                        st.session_state.ultima_requisicao = numero
                        st.success(
                            f"Requisição **{numero}** salva no Supabase. "
                            f"Baixe o PDF abaixo para imprimir."
                        )
                        st.balloons()

                        try:
                            pdf = gerar_pdf(dados, itens, nome_completo, numero, endereco)
                            if pdf:
                                st.session_state.pdf_cache = {
                                    "numero": numero,
                                    "solicitante": solicitante,
                                    "bytes": pdf,
                                }
                            else:
                                st.warning(
                                    f"Requisição **{numero}** salva, mas o PDF não foi gerado. "
                                    f"Reimprima pela aba **Histórico**."
                                )
                        except Exception as e:
                            st.warning(
                                f"Requisição **{numero}** salva. Erro no PDF: {e}. "
                                f"Reimprima pela aba **Histórico**."
                            )
                    else:
                        st.error(f"Não foi possível salvar: {erro}")

        if st.session_state.get("pdf_cache"):
            cache = st.session_state.pdf_cache
            st.markdown("---")
            st.markdown("#### Imprimir requisição gerada")
            st.caption("Baixe o PDF e use Ctrl+P no visualizador para imprimir.")
            st.download_button(
                f"Baixar PDF — {cache['numero']}",
                data=cache["bytes"],
                file_name=f"{cache['numero']}_{cache['solicitante']}_{datetime.now().strftime('%d%m%Y')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="dl_pdf_ultima",
            )

    with aba_hist:
        st.markdown("#### Reimprimir requisição")
        st.caption("Selecione uma requisição salva, baixe o PDF e imprima quando quiser.")

        try:
            df = conn.query(
                """
                SELECT numero_requisicao, data, destino, solicitante,
                       fornecedor, valor_total, item_descricao, cbp
                FROM requisicoes
                ORDER BY data DESC, criado_em DESC
                LIMIT 100
                """,
                ttl=0,
            )
            if df.empty:
                st.info("Nenhuma requisição registrada ainda na nova base Supabase.")
            else:
                opcoes = df["numero_requisicao"].tolist()
                labels = {
                    row["numero_requisicao"]: (
                        f"{row['numero_requisicao']} — {row['solicitante']} — "
                        f"R$ {float(row['valor_total']):,.2f}"
                    )
                    for _, row in df.iterrows()
                }
                sel = st.selectbox(
                    "Escolha a requisição",
                    opcoes,
                    format_func=lambda n: labels.get(n, n),
                )

                if st.button("Gerar PDF para impressão", type="primary", use_container_width=True):
                    try:
                        registro = buscar_requisicao(conn, sel)
                        if registro is None:
                            st.error("Requisição não encontrada.")
                        else:
                            pdf_hist = gerar_pdf_do_banco(registro)
                            if pdf_hist:
                                st.download_button(
                                    f"Baixar PDF — {sel}",
                                    data=pdf_hist,
                                    file_name=f"{sel}_{registro.get('solicitante', 'requisicao')}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True,
                                    key=f"dl_hist_{sel}",
                                )
                            else:
                                st.error("Não foi possível gerar o PDF. A requisição continua salva.")
                    except Exception as e:
                        st.error(f"Erro ao gerar PDF: {e}. A requisição continua salva no banco.")

                st.markdown("---")
                st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Erro ao carregar histórico: {e}")
