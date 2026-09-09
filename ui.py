"""
Estilo visual compartilhado da plataforma: CSS injetado uma vez por
sessão e pequenos helpers de layout (cabeçalho de página, cartão de
métrica) para manter a aparência consistente entre as telas, sem
depender de nada além do que o Streamlit já suporta nativamente.
"""

import streamlit as st

_CUSTOM_CSS = """
<style>
#MainMenu, footer {visibility: hidden;}

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, sans-serif;
}

/* ---- Sidebar ------------------------------------------------------ */
[data-testid="stSidebar"] {
    background-color: #0F1729;
    border-right: 1px solid #1E293B;
}
[data-testid="stSidebar"] hr {
    border-color: #1E293B;
}

/* Navegação lateral (st.radio) como "pills" em vez de radio cru.
   Estrutura real do BaseWeb (verificada via inspeção do DOM): o
   <input> fica dentro de um <span> escondível, mas o círculo visual é
   um <div> decorativo À PARTE (irmão do container que tem o texto,
   não filho do span do input) — por isso precisa de duas regras
   separadas pra sumir com o círculo e ainda esconder o input real. */
[data-testid="stSidebar"] [data-testid="stRadio"] > div {
    gap: 0.2rem;
}
[data-testid="stSidebar"] [data-testid="stRadioOption"] {
    padding: 0.5rem 0.75rem;
    border-radius: 8px;
    cursor: pointer;
    transition: background-color 0.15s ease;
    width: 100%;
}
[data-testid="stSidebar"] [data-testid="stRadioOption"]:hover {
    background-color: rgba(45, 212, 191, 0.08);
}
[data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input:checked) {
    background-color: rgba(45, 212, 191, 0.16);
}
[data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input:checked) p {
    color: #2DD4BF;
    font-weight: 600;
}
[data-testid="stSidebar"] [data-testid="stRadioOption"] span:has(input) {
    display: none;
}
[data-testid="stSidebar"] [data-testid="stRadioOption"] div:has(> [data-testid="stMarkdownContainer"]) > div:first-child {
    display: none;
}

/* ---- Botões --------------------------------------------------------- */
.stButton > button, .stDownloadButton > button, .stLinkButton > a {
    border-radius: 8px;
    transition: all 0.15s ease;
}
.stButton > button[kind="primary"] {
    font-weight: 600;
}

/* ---- Métricas como cartões ------------------------------------------ */
[data-testid="stMetric"] {
    background: #141B2E;
    border: 1px solid #1E293B;
    border-radius: 12px;
    padding: 1rem 1.2rem;
}

/* ---- Expanders / containers com borda -------------------------------- */
[data-testid="stExpander"] {
    border: 1px solid #1E293B;
    border-radius: 10px;
    background: #0F1729;
}

/* ---- Abas (tabs) ------------------------------------------------------ */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 1.5rem;
}

/* ---- Cabeçalho de página customizado (ui.page_header) ------------------ */
.ph-wrap {
    display: flex;
    align-items: center;
    gap: 0.9rem;
    margin-bottom: 1.4rem;
}
.ph-icon {
    font-size: 1.6rem;
    min-width: 3rem;
    height: 3rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    background: linear-gradient(135deg, rgba(45, 212, 191, 0.18), rgba(56, 189, 248, 0.12));
}
.ph-title {
    font-size: 1.7rem;
    font-weight: 700;
    line-height: 1.2;
    color: #E2E8F0;
}
</style>
"""


def inject_custom_css():
    st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)


def page_header(icon: str, title: str):
    st.markdown(
        f"""
        <div class="ph-wrap">
            <div class="ph-icon">{icon}</div>
            <div class="ph-title">{title}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
