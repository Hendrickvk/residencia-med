"""
Estilo visual compartilhado da plataforma: CSS injetado uma vez por
sessão, um pequeno conjunto de ícones SVG (Lucide, MIT license) para
os cabeçalhos de página, e helpers de layout — para manter a
aparência consistente entre as telas sem depender de nada além do
que o Streamlit já suporta nativamente.

Ícones de botões/expanders/mensagens usam o suporte nativo do
Streamlit a Material Symbols (`icon=":material/nome:"`), já que ele
mesmo usa essa fonte internamente — não precisa de CSS/JS extra pra
isso. Os ícones SVG abaixo são só para os cabeçalhos de página
(.ph-icon), onde o efeito visual maior compensa manter o SVG embutido
(sem risco de "flash" de fonte não carregada).
"""

import streamlit as st

# Conteúdo interno (paths) de cada ícone Lucide usado — baixados de
# https://cdn.jsdelivr.net/npm/lucide-static/icons/<nome>.svg
_ICONS = {
    "stethoscope": """
        <path d="M11 2v2" /><path d="M5 2v2" />
        <path d="M5 3H4a2 2 0 0 0-2 2v4a6 6 0 0 0 12 0V5a2 2 0 0 0-2-2h-1" />
        <path d="M8 15a6 6 0 0 0 12 0v-3" /><circle cx="20" cy="10" r="2" />
    """,
    "layout-dashboard": """
        <rect width="7" height="9" x="3" y="3" rx="1" />
        <rect width="7" height="5" x="14" y="3" rx="1" />
        <rect width="7" height="9" x="14" y="12" rx="1" />
        <rect width="7" height="5" x="3" y="16" rx="1" />
    """,
    "pencil-line": """
        <path d="M13 21h8" /><path d="m15 5 4 4" />
        <path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z" />
    """,
    "timer": """
        <line x1="10" x2="14" y1="2" y2="2" />
        <line x1="12" x2="15" y1="14" y2="11" />
        <circle cx="12" cy="14" r="8" />
    """,
    "square-plus": """
        <rect width="18" height="18" x="3" y="3" rx="2" />
        <path d="M8 12h8" /><path d="M12 8v8" />
    """,
    "file-up": """
        <path d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z" />
        <path d="M14 2v5a1 1 0 0 0 1 1h5" /><path d="M12 12v6" /><path d="m15 15-3-3-3 3" />
    """,
    "brain": """
        <path d="M12 18V5" />
        <path d="M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4" />
        <path d="M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5" />
        <path d="M17.997 5.125a4 4 0 0 1 2.526 5.77" />
        <path d="M18 18a4 4 0 0 0 2-7.464" />
        <path d="M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517" />
        <path d="M6 18a4 4 0 0 1-2-7.464" />
        <path d="M6.003 5.125a4 4 0 0 0-2.526 5.77" />
    """,
    "book-open": """
        <path d="M12 5v16" />
        <path d="M20.001 19A2 2 0 0022 17V5a2 2 0 00-1.999-2L16 3.002A5 5 0 0012 5a5 5 0 00-4-2H4a2 2 0 00-2 2v12a2 2 0 001.999 2H8a5 5 0 014 2 5 5 0 014-2z" />
    """,
    "folder-sync": """
        <path d="M9 20H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H20a2 2 0 0 1 2 2v.5" />
        <path d="M12 10v4h4" /><path d="m12 14 1.535-1.605a5 5 0 0 1 8 1.5" />
        <path d="M22 22v-4h-4" /><path d="m22 18-1.535 1.605a5 5 0 0 1-8-1.5" />
    """,
    "database": """
        <ellipse cx="12" cy="5" rx="9" ry="3" />
        <path d="M3 5V19A9 3 0 0 0 21 19V5" /><path d="M3 12A9 3 0 0 0 21 12" />
    """,
    "inbox": """
        <path d="M22 12h-6l-2 3h-4l-2-3H2" />
        <path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
    """,
    "circle-check": """
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
        <path d="m9 11 3 3L22 4" />
    """,
}


def icon_svg(name: str, size: int = 20) -> str:
    inner = _ICONS.get(name, "")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round">{inner}</svg>'
    )


_CUSTOM_CSS = """
<style>
#MainMenu, footer {visibility: hidden;}

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, sans-serif;
}

/* ---- Largura do conteúdo -------------------------------------------- */
/* layout="wide" dá espaço extra pra sidebar, mas formulários e listas
   esticados até a borda da tela ficam com campos enormes e vazios em
   monitores largos. Centraliza o conteúdo com uma largura confortável
   de leitura em vez de ocupar 100% da viewport. */
[data-testid="stAppViewContainer"] .block-container {
    max-width: 1180px;
    padding-top: 2rem;
}

/* ---- Cards (st.container(border=True)) ------------------------------- */
[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid #1E293B;
    border-radius: 12px;
    background: #0F1729;
}
[data-testid="stVerticalBlockBorderWrapper"] > div > [data-testid="stVerticalBlock"] {
    gap: 0.9rem;
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
    min-width: 3rem;
    height: 3rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    background: linear-gradient(135deg, rgba(45, 212, 191, 0.18), rgba(56, 189, 248, 0.12));
    color: #2DD4BF;
}
.ph-title {
    font-size: 1.7rem;
    font-weight: 700;
    line-height: 1.2;
    color: #E2E8F0;
}

/* ---- Estado vazio (ui.empty_state) ------------------------------------ */
.es-wrap {
    text-align: center;
    padding: 1.6rem 1rem 0.6rem;
}
.es-icon {
    width: 3.5rem;
    height: 3.5rem;
    margin: 0 auto 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: linear-gradient(135deg, rgba(45, 212, 191, 0.14), rgba(56, 189, 248, 0.08));
    color: #2DD4BF;
}
.es-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #E2E8F0;
}
.es-subtitle {
    font-size: 0.9rem;
    color: #8291AD;
    margin-top: 0.3rem;
}
</style>
"""


def inject_custom_css():
    st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)


def page_header(icon: str, title: str):
    st.markdown(
        f"""
        <div class="ph-wrap">
            <div class="ph-icon">{icon_svg(icon, size=24)}</div>
            <div class="ph-title">{title}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(
    title: str,
    subtitle: str = "",
    icon: str = "inbox",
    cta_label: str | None = None,
    cta_icon: str | None = None,
    cta_pagina: str | None = None,
):
    """Bloco visual pra listas/telas sem dados, no lugar de um st.info cru.
    Se `cta_label` + `cta_pagina` forem passados, mostra um botão que troca
    de página em vez de só sugerir por texto pra onde o usuário deveria ir.
    Não escreve direto em `st.session_state["nav_pagina"]` (o widget do
    menu já foi instanciado nesta execução, o que geraria
    StreamlitWidgetAlreadyInstantiatedError) — grava numa chave separada
    que o app.py consome antes de recriar o widget do menu na próxima
    execução."""
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="es-wrap">
                <div class="es-icon">{icon_svg(icon, size=28)}</div>
                <div class="es-title">{title}</div>
                {f'<div class="es-subtitle">{subtitle}</div>' if subtitle else ""}
            </div>
            """,
            unsafe_allow_html=True,
        )
        if cta_label and cta_pagina:
            _, col_meio, _ = st.columns([1, 1.4, 1])
            with col_meio:
                if st.button(
                    cta_label, icon=cta_icon, use_container_width=True,
                    key=f"es_cta_{abs(hash((title, cta_pagina)))}",
                ):
                    st.session_state["_forcar_pagina"] = cta_pagina
                    st.rerun()
