import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import random
import io

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Requisição de Compras | ASTS & CBTS",
    page_icon="📋",
    layout="centered"
)

AZUL    = "#003049"
BEGE    = "#F5ECD7"
BEGE2   = "#EDE0C4"
DOURADO = "#C8A96E"

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;0,700;1,400&family=Inter:wght@400;500;600;700&display=swap');

  html, body, [class*="css"] {{
    background-color: {BEGE} !important;
    color: {AZUL} !important;
    font-family: 'Inter', sans-serif;
  }}
  .header-box {{
    background-color: {AZUL};
    padding: 28px 20px 20px;
    border-radius: 10px;
    text-align: center;
    margin-bottom: 28px;
    border-bottom: 4px solid {DOURADO};
  }}
  .header-title {{
    font-family: 'Crimson Pro', Georgia, serif;
    font-size: 28px;
    font-weight: 700;
    color: #F5ECD7;
    letter-spacing: 0.5px;
  }}
  .header-sub {{
    font-size: 11px;
    color: #A0B4C8;
    text-transform: uppercase;
    letter-spacing: 2.5px;
    margin-top: 6px;
  }}
  .header-versiculo {{
    font-family: 'Crimson Pro', Georgia, serif;
    font-size: 15px;
    color: {DOURADO};
    font-style: italic;
    margin-top: 12px;
  }}
  .secao {{
    background-color: {BEGE2};
    border: 1px solid #D4C4A0;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 18px;
  }}
  .secao-titulo {{
    font-family: 'Crimson Pro', Georgia, serif;
    font-size: 17px;
    font-weight: 700;
    color: {AZUL};
    border-bottom: 1px solid #C8B88A;
    padding-bottom: 8px;
    margin-bottom: 14px;
  }}
  .stTextInput > label,
  .stSelectbox > label,
  .stTextArea > label,
  .stNumberInput > label {{
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    color: {AZUL} !important;
    font-weight: 700 !important;
  }}
  .stTextInput input,
  .stTextArea textarea {{
    background-color: #FFFEF8 !important;
    border: 1.5px solid #C4B48A !important;
    color: {AZUL} !important;
    border-radius: 6px !important;
  }}
  .stTextInput input:focus,
  .stTextArea textarea:focus {{
    border-color: {AZUL} !important;
    box-shadow: 0 0 0 2px rgba(0,48,73,0.15) !important;
  }}
  div[data-baseweb="select"] > div {{
    background-color: #FFFEF8 !important;
    border: 1.5px solid #C4B48A !important;
    border-radius: 6px !important;
    color: {AZUL} !important;
  }}
  .stButton > button {{
    background-color: {AZUL} !important;
    color: #F5ECD7 !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    padding: 10px 28px !important;
    letter-spacing: 0.5px !important;
    width: 100%;
  }}
  .stButton > button:hover {{
    background-color: #014F7A !important;
  }}
  .stRadio > label {{
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    color: {AZUL} !important;
    font-weight: 700 !important;
  }}
  .stTabs [data-baseweb="tab-list"] {{
    background-color: {AZUL} !important;
    border-radius: 8px 8px 0 0;
    padding: 4px 6px 0;
    gap: 4px;
  }}
  .stTabs [data-baseweb="tab"] {{
    color: #A0B4C8 !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    border-radius: 6px 6px 0 0 !important;
    padding: 10px 20px !important;
  }}
  .stTabs [aria-selected="true"] {{
    background-color: {BEGE} !important;
    color: {AZUL} !important;
  }}
  .stTabs [data-baseweb="tab-panel"] {{
    background-color: {BEGE};
    border: 1px solid #D4C4A0;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 20px;
  }}
  .rodape {{
    background-color: {AZUL};
    color: #A0B4C8;
    text-align: center;
    padding: 12px;
    border-radius: 8px;
    border-top: 3px solid {DOURADO};
    margin-top: 32px;
    font-size: 12px;
  }}
  .rodape-nome {{
    font-family: 'Crimson Pro', Georgia, serif;
    font-size: 14px;
    color: #D0DDE8;
    margin-bottom: 3px;
  }}
  #MainMenu, footer, header {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

# ── CONSTANTES ────────────────────────────────────────────────────────────────
ORGANIZACOES = {
    "ASTS": ["CBP","BETHEL MUSIC","CAT VIDA NOVA","HIDROPONIA","MARCENARIA","PRAÇA TERRA SANTA"],
    "CBTS": [
        "MIN. LOUVOR","MIN. RECEPÇÃO","MIN. LIBRAS",
        "MIN. CURA E LIBERTAÇÃO","MIN. INTERCESSÃO","MIN. MÍDIA",
        "MIN. SONOPLASTIA","MIN. INFANTIL","MIN. PROJEÇÃO",
        "MIN. CAPELANIA","MIN. CÉLULAS","MIN. REDE JOVENS",
        "MIN. TEATRO","MIN. BENEFICÊNCIA","MIN. PREGAÇÃO",
        "MIN. PASTORAL","MIN. VISITAS"
    ]
}

SHEET_NAME = "REQUISICAO_COMPRAS"
COLUNAS    = ["ID_REQUISICAO","DATA","ORGANIZACAO","DESTINO",
              "SOLICITANTE","PRIORIDADE","JUSTIFICATIVA","ITENS"]

# ── SHEETS ────────────────────────────────────────────────────────────────────
@st.cache_resource
def conectar_sheets():
    scope  = ["https://spreadsheets.google.com/feeds",
               "https://www.googleapis.com/auth/drive"]
    creds  = Credentials.from_service_account_info(
                 st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1

def carregar_dados(sheet):
    dados = sheet.get_all_records()
    if not dados:
        return pd.DataFrame(columns=COLUNAS)
    return pd.DataFrame(dados)

def salvar_linha(sheet, linha):
    sheet.append_row(linha, value_input_option="USER_ENTERED")

def gerar_id():
    d = datetime.now()
    return f"REQ-{d.strftime('%Y%m%d')}-{random.randint(1,999):03d}"

# ── SESSION STATE — controla reset do formulário ──────────────────────────────
def init_form():
    defaults = {
        "org": "Selecione...",
        "solicitante": "",
        "prioridade": "NORMAL",
        "justificativa": "",
        "num_itens": 1,
        "form_key": 0,   # força recriação dos widgets
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def resetar_form():
    st.session_state["org"]          = "Selecione..."
    st.session_state["solicitante"]  = ""
    st.session_state["prioridade"]   = "NORMAL"
    st.session_state["justificativa"]= ""
    st.session_state["num_itens"]    = 1
    st.session_state["form_key"]     = st.session_state.get("form_key", 0) + 1

init_form()

# ── CABEÇALHO ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-box">
  <div style="font-size:20px;color:#C8A96E;letter-spacing:6px;margin-bottom:6px;">✦ ✦ ✦</div>
  <div class="header-title">ASTS &amp; CBTS</div>
  <div class="header-sub">Sistema de Requisição de Compras</div>
  <div class="header-versiculo">"Jesus é tudo que você precisa!"</div>
</div>
""", unsafe_allow_html=True)

aba1, aba2 = st.tabs(["📋  Nova Requisição", "📂  Requisições Registradas"])

# ════════════════════════════════════════════════════════════════════════════
# ABA 1 — FORMULÁRIO
# ════════════════════════════════════════════════════════════════════════════
with aba1:
    try:
        sheet = conectar_sheets()
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Sheets: {e}")
        st.stop()

    fk = st.session_state["form_key"]  # chave dinâmica para reset

    st.markdown('<div class="secao"><div class="secao-titulo">Identificação</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        org = st.selectbox(
            "Organização *",
            ["Selecione...", "ASTS", "CBTS"],
            key=f"org_{fk}"
        )
    with col2:
        if org in ORGANIZACOES:
            label_destino = "Área de Destino *" if org == "ASTS" else "Ministério de Destino *"
            destino = st.selectbox(label_destino, ["Selecione..."] + ORGANIZACOES[org], key=f"destino_{fk}")
        else:
            destino = st.selectbox("Destino *", ["Selecione a organização primeiro"], key=f"destino_{fk}")

    solicitante   = st.text_input("Solicitante *", placeholder="Nome completo", key=f"sol_{fk}")
    prioridade    = st.radio("Prioridade", ["NORMAL","URGENTE","CRÍTICO"], horizontal=True, key=f"pri_{fk}")
    justificativa = st.text_area("Justificativa / Finalidade *",
                                  placeholder="Descreva a necessidade e para que será utilizado...",
                                  height=110, key=f"just_{fk}")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── ITENS ────────────────────────────────────────────────────────────────
    st.markdown('<div class="secao"><div class="secao-titulo">Itens Solicitados</div>', unsafe_allow_html=True)

    col_add, _ = st.columns([1, 4])
    with col_add:
        if st.button("＋ Adicionar Item"):
            st.session_state["num_itens"] += 1

    itens_lista = []
    for i in range(st.session_state["num_itens"]):
        st.markdown(f"**Item {i+1}**")
        c1, c2, c3 = st.columns([3,1,1])
        with c1:
            desc = st.text_input("Descrição", key=f"desc_{fk}_{i}", placeholder="Descrição do item", label_visibility="collapsed")
        with c2:
            qtd  = st.text_input("Qtd",       key=f"qtd_{fk}_{i}",  placeholder="Qtd",               label_visibility="collapsed")
        with c3:
            und  = st.text_input("Unidade",   key=f"und_{fk}_{i}",  placeholder="un / kg / cx",      label_visibility="collapsed")
        if desc.strip():
            itens_lista.append(f"{i+1}. {desc.strip()} — {qtd.strip()} {und.strip()}".strip(" —"))

    st.markdown('</div>', unsafe_allow_html=True)

    # ── REGISTRAR ────────────────────────────────────────────────────────────
    if st.button("✦  Registrar Requisição"):
        erros = []
        if org not in ORGANIZACOES:
            erros.append("Selecione a organização.")
        if not destino or destino.startswith("Selecione"):
            erros.append("Selecione o destino.")
        if not solicitante.strip():
            erros.append("Informe o solicitante.")
        if not justificativa.strip():
            erros.append("Informe a justificativa.")
        if not itens_lista:
            erros.append("Informe ao menos um item com descrição.")

        if erros:
            for e in erros:
                st.warning(e)
        else:
            id_req    = gerar_id()
            data      = datetime.now().strftime("%d/%m/%Y")
            itens_str = "  /  ".join(itens_lista)
            linha     = [id_req, data, org, destino,
                         solicitante.strip(), prioridade,
                         justificativa.strip(), itens_str]
            try:
                salvar_linha(sheet, linha)
                st.success(f"✅ Requisição **{id_req}** registrada com sucesso!")
                st.balloons()
                resetar_form()
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

# ════════════════════════════════════════════════════════════════════════════
# ABA 2 — LISTA + IMPRESSÃO
# ════════════════════════════════════════════════════════════════════════════
with aba2:
    try:
        sheet2 = conectar_sheets()
        df     = carregar_dados(sheet2)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.stop()

    st.markdown(f"### Requisições Registradas &nbsp; `{len(df)}`")

    if df.empty:
        st.info("Nenhuma requisição registrada ainda.")
    else:
        # Filtros
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_org = st.selectbox("Filtrar por Organização", ["Todas","ASTS","CBTS"], key="f_org")
        with col_f2:
            filtro_pri = st.selectbox("Filtrar por Prioridade", ["Todas","NORMAL","URGENTE","CRÍTICO"], key="f_pri")

        df_view = df.copy()
        if filtro_org != "Todas":
            df_view = df_view[df_view["ORGANIZACAO"] == filtro_org]
        if filtro_pri != "Todas":
            df_view = df_view[df_view["PRIORIDADE"] == filtro_pri]

        st.dataframe(
            df_view,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID_REQUISICAO": st.column_config.TextColumn("Nº Requisição", width="medium"),
                "DATA":          st.column_config.TextColumn("Data",          width="small"),
                "ORGANIZACAO":   st.column_config.TextColumn("Organização",   width="small"),
                "DESTINO":       st.column_config.TextColumn("Destino",       width="medium"),
                "SOLICITANTE":   st.column_config.TextColumn("Solicitante",   width="medium"),
                "PRIORIDADE":    st.column_config.TextColumn("Prioridade",    width="small"),
                "JUSTIFICATIVA": st.column_config.TextColumn("Justificativa", width="large"),
                "ITENS":         st.column_config.TextColumn("Itens",         width="large"),
            }
        )

        # ── EXPORTAR EXCEL ───────────────────────────────────────────────────
        st.markdown("---")
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df_view.to_excel(writer, index=False, sheet_name="Requisições")
        buf.seek(0)
        st.download_button(
            label="⬇ Exportar Excel (.xlsx)",
            data=buf,
            file_name="requisicoes_compras.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # ── IMPRESSÃO ────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 🖨️ Imprimir Requisição")

        id_sel = st.selectbox("Selecione o número da requisição para imprimir",
                               df["ID_REQUISICAO"].tolist(), key="id_print")

        if id_sel:
            req = df[df["ID_REQUISICAO"] == id_sel].iloc[0]

            # Monta linhas da tabela de itens
            linhas_itens = ""
            itens_raw = str(req["ITENS"]).split("  /  ")
            for idx_i, item in enumerate(itens_raw):
                partes = item.split(" — ", 1)
                desc_i = partes[0].strip()
                qtd_i  = partes[1].strip() if len(partes) > 1 else "—"
                bg_td  = "#FFFFFF" if idx_i % 2 == 0 else "#FAF7F0"
                linhas_itens += f"""
                <tr>
                  <td style="padding:8px 11px;border-bottom:1px solid #E0D8C8;width:36px;background:{bg_td}">{idx_i+1}</td>
                  <td style="padding:8px 11px;border-bottom:1px solid #E0D8C8;font-weight:700;background:{bg_td}">{desc_i}</td>
                  <td style="padding:8px 11px;border-bottom:1px solid #E0D8C8;background:{bg_td}">{qtd_i}</td>
                </tr>"""

            label_destino_imp = "Área de Destino" if req["ORGANIZACAO"] == "ASTS" else "Ministério de Destino"

            html_doc = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{req['ID_REQUISICAO']}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:Georgia,serif;color:#003049;padding:30px 36px;background:#fff;font-size:13px}}
  .topo{{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:2.5px solid #003049;padding-bottom:14px;margin-bottom:20px}}
  .titulo{{font-size:19px;font-weight:700;color:#003049}}
  .sub{{font-size:10px;color:#556;text-transform:uppercase;letter-spacing:1.5px;margin-top:3px}}
  .badge{{background:#003049;color:#fff;padding:7px 16px;border-radius:4px;font-size:13px;font-weight:700;white-space:nowrap;font-family:Arial,sans-serif}}
  .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-bottom:16px}}
  .campo{{background:#F5ECD7;border:1px solid #C4B48A;border-radius:4px;padding:9px 12px}}
  .cl{{font-size:9px;text-transform:uppercase;letter-spacing:1.5px;color:#778;margin-bottom:2px;font-family:Arial,sans-serif}}
  .cv{{font-size:13px;font-weight:700;color:#003049}}
  .just{{background:#fffef5;border-left:4px solid #003049;padding:10px 14px;margin-bottom:18px;font-size:12px;line-height:1.7}}
  .jl{{font-size:9px;text-transform:uppercase;letter-spacing:1.5px;color:#778;margin-bottom:4px;font-family:Arial,sans-serif}}
  table{{width:100%;border-collapse:collapse;margin-bottom:16px;font-family:Arial,sans-serif}}
  th{{background:#003049;color:#fff;padding:9px 11px;text-align:left;font-size:12px;font-weight:700}}
  td{{font-size:12px;color:#003049}}
  .assinaturas{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:36px;margin-top:54px}}
  .assl{{border-top:1.5px solid #003049;padding-top:8px;text-align:center;font-size:10px;color:#556;font-family:Arial,sans-serif}}
  .rodape{{text-align:center;font-size:10px;color:#aaa;margin-top:26px;border-top:1px solid #E0D8C8;padding-top:10px;font-family:Arial,sans-serif}}
  @media print{{body{{padding:20px 28px}}}}
</style>
<script>window.onload = function(){{ window.print(); }}</script>
</head><body>
<div class="topo">
  <div>
    <div class="titulo">ASTS &amp; CBTS — Requisição de Compras</div>
    <div class="sub">Documento de Controle Interno</div>
  </div>
  <div class="badge">{req['ID_REQUISICAO']}</div>
</div>
<div class="grid2">
  <div class="campo"><div class="cl">Data</div><div class="cv">{req['DATA']}</div></div>
  <div class="campo"><div class="cl">Organização</div><div class="cv">{req['ORGANIZACAO']}</div></div>
  <div class="campo"><div class="cl">{label_destino_imp}</div><div class="cv">{req['DESTINO']}</div></div>
  <div class="campo"><div class="cl">Solicitante</div><div class="cv">{req['SOLICITANTE']}</div></div>
  <div class="campo"><div class="cl">Prioridade</div><div class="cv">{req['PRIORIDADE']}</div></div>
</div>
<div class="just">
  <div class="jl">Justificativa / Finalidade</div>
  {req['JUSTIFICATIVA']}
</div>
<table>
  <thead><tr>
    <th>#</th>
    <th>Descrição do Item</th>
    <th>Qtd / Unidade</th>
  </tr></thead>
  <tbody>{linhas_itens}</tbody>
</table>
<div class="assinaturas">
  <div class="assl">Solicitante</div>
  <div class="assl">Responsável da Área</div>
  <div class="assl">Aprovação</div>
</div>
<div class="rodape">
  Documento gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} &nbsp;·&nbsp;
  ASTS &amp; CBTS &nbsp;·&nbsp; Rua José Vicenti Vitiriti, 801 — Residencial Modelo I &nbsp;·&nbsp; (67) 99682-2052
</div>
</body></html>"""

            st.download_button(
                label=f"🖨️ Abrir para Impressão — {id_sel}",
                data=html_doc.encode("utf-8"),
                file_name=f"{id_sel}.html",
                mime="text/html",
                help="Baixe o arquivo → clique duas vezes → abre no navegador → Ctrl+P → Salvar como PDF"
            )
            st.caption("💡 Baixe → abra no navegador → Ctrl+P → Salvar como PDF")

# ── RODAPÉ ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="rodape">
  <div class="rodape-nome">ASTS &amp; CBTS</div>
  <div>Rua José Vicenti Vitiriti, 801 — Residencial Modelo I &nbsp;|&nbsp; (67) 99682-2052</div>
</div>
""", unsafe_allow_html=True)
