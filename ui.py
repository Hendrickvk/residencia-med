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

import json

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
    "badge-check": """
        <path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z" />
        <path d="m16 9-5.5 5.5L8 12" />
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
    border: 1px solid #D7E3E2;
    border-radius: 12px;
    background: #FFFFFF;
}
[data-testid="stVerticalBlockBorderWrapper"] > div > [data-testid="stVerticalBlock"] {
    gap: 0.9rem;
}

/* ---- Sidebar ------------------------------------------------------ */
[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    border-right: 1px solid #D7E3E2;
    position: relative;
    /* Anima a largura ao expandir/recolher (a troca de 4.6rem pra
       largura padrão, ou vice-versa, senão é instantânea/brusca). O
       conteúdo interno troca de estrutura na hora (ícone <-> ícone+
       rótulo) ANTES da largura terminar de animar — sem
       overflow-x:hidden + nowrap no texto (regra abaixo), o rótulo
       cheio ("Dashboard", "Praticar"...) tenta caber na largura ainda
       estreita e quebra linha, desfazendo a quebra conforme a largura
       cresce — o efeito de "letras se mexendo" que aparecia ao
       expandir. Com overflow-x:hidden o texto que não cabe ainda fica
       recortado (não quebra linha), e só aparece inteiro quando a
       largura já estabilizou — mais limpo. */
    overflow-x: hidden;
    transition: width 0.22s ease, min-width 0.22s ease;
}
[data-testid="stSidebar"] button p,
[data-testid="stSidebar"] .stMarkdownContainer p {
    white-space: nowrap;
}
[data-testid="stSidebar"] hr {
    border-color: #D7E3E2;
}
/* O app tem seu próprio botão de recolher/expandir (vira só ícone, não
   some de vez) — o botão nativo do Streamlit ("«" dentro da sidebar)
   fica bem em cima dele e some a sidebar inteira, o que confunde mais
   do que ajuda. Escondido; o botão flutuante de reabrir
   (stExpandSidebarButton) fica como saída de emergência caso a sidebar
   suma por outro motivo. */
[data-testid="stSidebarCollapseButton"] {
    display: none;
}

/* ---- Handle de expandir/recolher (st.container(key="toggle_handle")) ---- */
/* Ancorado na própria <section data-testid="stSidebar"> (não no
   "sidebar_header" — já tentamos isso, mas o usuário pediu de volta
   "na linha da divisória", não empilhado embaixo do cabeçalho).
   `top:50vh` em vez de `top:50%`: 50% seria relativo à altura da
   PRÓPRIA sidebar, que o Streamlit estica pra bater com a altura do
   conteúdo principal (às vezes bem mais alta que a tela visível) —
   nesse caso o centro "real" cai no meio da lista de ícones. `vh` é
   sempre relativo à altura da VIEWPORT, então o círculo fica
   centralizado na tela visível, na linha da borda, sem depender de
   quão "esticada" a sidebar ficou. `right:-5px` deixa o círculo
   encostado na borda, mas ainda por DENTRO da sidebar — o Streamlit
   tem uma faixa invisível de redimensionar (~8px, cursor col-resize)
   bem em cima da borda com z-index altíssimo (999995) que rouba o
   clique de qualquer coisa colocada sobre ela, então o círculo fica só
   de um lado (dentro), nunca a cavaleiro da borda. `width`/`height`/
   `display:flex` no wrapper evitam que ele fique maior que o botão em
   si (o stVerticalBlock por padrão sobra espaço à direita do
   conteúdo), o que desalinharia esse `right`. */
[data-testid="stSidebar"] .st-key-toggle_handle {
    position: absolute;
    top: 50vh;
    transform: translateY(-50%);
    right: -5px;
    z-index: 999;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
}
/* Nota: usa "button" descendente, não ">"— um botão com `help=` (é o
   caso aqui) vem envolvido pelo Streamlit num <span
   class="stTooltipHoverTarget"> extra entre .stButton e o <button>,
   então um seletor de filho direto (>) nunca casava e o botão ficava
   do tamanho padrão do Streamlit em vez do tamanho definido aqui. */
[data-testid="stSidebar"] .st-key-toggle_handle .stButton button {
    width: 32px !important;
    height: 32px !important;
    min-height: 32px !important;
    min-width: 32px !important;
    padding: 0 !important;
    border-radius: 50% !important;
    background: #0F766E !important;
    color: #FFFFFF !important;
    border: none !important;
    box-shadow: 0 1px 4px rgba(20, 37, 34, 0.18);
}
[data-testid="stSidebar"] .st-key-toggle_handle .stButton button:hover {
    background: #0B5D56 !important;
}

/* ---- Avatar / popover de perfil (st.popover, key="perfil_popover") --- */
[data-testid="stSidebar"] .st-key-perfil_popover {
    display: flex;
    justify-content: center;
}
[data-testid="stSidebar"] .st-key-perfil_popover button {
    width: 2.5rem;
    height: 2.5rem;
    min-width: 2.5rem;
    min-height: 2.5rem;
    border-radius: 50%;
    padding: 0;
    background: rgba(15, 118, 110, 0.16);
    color: #0F766E;
    border: none;
    font-weight: 700;
    font-size: 0.78rem;
}
/* st.popover adiciona sozinho um ícone de seta ("expand_more") no
   gatilho — sem isso, o botão vira uma "pílula" com seta que destoa
   dos outros ícones lisos da sidebar (é a "desconexão" percebida). */
[data-testid="stSidebar"] .st-key-perfil_popover [data-testid="stIconMaterial"] {
    display: none;
}
[data-testid="stSidebar"] .st-key-perfil_popover button:hover {
    background: rgba(15, 118, 110, 0.26);
}
.p-avatar {
    width: 1.8rem;
    height: 1.8rem;
    border-radius: 50%;
    background: rgba(15, 118, 110, 0.16);
    color: #0F766E;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.7rem;
}

/* Navegação lateral: cada página é um st.button (não mais st.radio) pra
   permitir o modo recolhido (só ícone) sem duas implementações
   separadas. `st.container(key="nav_area")` marca o wrapper com a
   classe "st-key-nav_area" (recurso nativo do Streamlit >=1.3x) — as
   regras abaixo só valem dentro dele, não afetam outros botões do app.
   Página ativa usa type="primary" (fundo sólido nativo do Streamlit);
   as demais usam "secondary", esvaziadas de borda/fundo aqui pra
   parecerem linhas de menu, não botões soltos. */
[data-testid="stSidebar"] .st-key-nav_area .stButton button {
    justify-content: flex-start;
    gap: 0.6rem;
    padding-left: 0.75rem;
}
[data-testid="stSidebar"] .st-key-nav_area .stButton button[kind="secondary"] {
    border-color: transparent;
    background: transparent;
    font-weight: 500;
    color: #142523;
}
[data-testid="stSidebar"] .st-key-nav_area .stButton button[kind="secondary"]:hover {
    background-color: rgba(15, 118, 110, 0.08);
    border-color: transparent;
    color: #0F766E;
}

/* ---- Botões --------------------------------------------------------- */
.stButton button, .stDownloadButton > button, .stLinkButton > a {
    border-radius: 8px;
    transition: all 0.15s ease;
}
.stButton button[kind="primary"] {
    font-weight: 600;
}

/* ---- Métricas como cartões ------------------------------------------ */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #D7E3E2;
    border-radius: 12px;
    padding: 1rem 1.2rem;
}

/* ---- Expanders / containers com borda -------------------------------- */
[data-testid="stExpander"] {
    border: 1px solid #D7E3E2;
    border-radius: 10px;
    background: #FFFFFF;
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
    background: linear-gradient(135deg, rgba(15, 118, 110, 0.16), rgba(21, 94, 117, 0.12));
    color: #0F766E;
}
.ph-title {
    font-size: 1.7rem;
    font-weight: 700;
    line-height: 1.2;
    color: #142523;
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
    background: linear-gradient(135deg, rgba(15, 118, 110, 0.14), rgba(21, 94, 117, 0.08));
    color: #0F766E;
}
.es-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #142523;
}
.es-subtitle {
    font-size: 0.9rem;
    color: #5A6C6A;
    margin-top: 0.3rem;
}

/* ---- Selo de autenticidade da questão (render_questao) ---------------- */
.qs-selo {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(15, 118, 110, 0.06);
    border: 1px solid #D7E3E2;
    border-radius: 10px;
    padding: 0.4rem 0.8rem;
    margin-bottom: 0.85rem;
}
.qs-selo-banca {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: #0F766E;
}
.qs-selo-banca svg { flex-shrink: 0; }
.qs-selo-ano {
    font-size: 0.75rem;
    color: #5A6C6A;
    white-space: nowrap;
}

/* ---- Rótulo de seção dentro de formulário (form_section_label) -------- */
.form-section-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: #5A6C6A;
    margin: 0.9rem 0 0.35rem;
}

/* ---- Badges semânticos (metric_badge) ---------------------------------- */
.metric-badge-row {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
}
.metric-badge {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    background: #FFFFFF;
    border: 1px solid #D7E3E2;
    border-left: 4px solid var(--mb-cor, #5A6C6A);
    border-radius: 8px;
    padding: 0.55rem 0.9rem;
}
.metric-badge-label {
    font-size: 0.88rem;
    color: #142523;
    font-weight: 500;
}
.metric-badge-value {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 700;
    font-size: 0.85rem;
    color: var(--mb-cor, #142523);
    white-space: nowrap;
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


def form_section_label(texto: str):
    """Rótulo de subseção dentro de um formulário (ex.: "Alternativas"),
    com peso visual próprio — no lugar de `st.write("Alternativas")`, que
    rendia com o mesmo peso de um parágrafo comum."""
    st.markdown(f'<div class="form-section-label">{texto}</div>', unsafe_allow_html=True)


def cor_semantica_pct(pct: float) -> str:
    """Cor semântica (vermelho/âmbar/verde) pra uma % de acerto — limiares
    alinhados ao que o Dashboard já trata como 'prioridade de revisão'
    (abaixo de 50% é crítico)."""
    if pct < 50:
        return "#DC2626"
    if pct < 75:
        return "#D97706"
    return "#16A34A"


def metric_badge_row(itens: list[dict]):
    """Lista de resultados em formato de cartão fino com barra lateral
    colorida — `itens`: [{"label": str, "valor": str, "cor": "#RRGGBB"}].
    Substitui listas onde números vinham embutidos numa frase de
    `st.write`/`st.success`, sem nenhum destaque visual."""
    partes = ['<div class="metric-badge-row">']
    for item in itens:
        cor = item.get("cor", "#5A6C6A")
        partes.append(
            f'<div class="metric-badge" style="--mb-cor:{cor};">'
            f'<span class="metric-badge-label">{item["label"]}</span>'
            f'<span class="metric-badge-value">{item["valor"]}</span>'
            f'</div>'
        )
    partes.append("</div>")
    st.markdown("".join(partes), unsafe_allow_html=True)


@st.dialog("Confirmar exclusão", icon=":material/warning:")
def _dialog_confirmar_exclusao(mensagem, on_confirmar):
    st.markdown(mensagem)
    col1, col2 = st.columns(2)
    if col1.button("Cancelar", use_container_width=True):
        st.rerun()
    if col2.button(
        "Excluir definitivamente", icon=":material/delete_forever:",
        type="primary", use_container_width=True,
    ):
        on_confirmar()
        st.rerun()


def confirmar_exclusao(mensagem: str, on_confirmar):
    """Abre um dialog nativo (`st.dialog`) pedindo confirmação antes de uma
    ação destrutiva, no lugar de excluir já no primeiro clique.
    `on_confirmar`: callable sem argumentos, chamado só se o usuário
    confirmar (normalmente uma lambda envolvendo a chamada de exclusão)."""
    _dialog_confirmar_exclusao(mensagem, on_confirmar)


def render_questao(
    q,
    *,
    modo: str,
    key: str | None = None,
    resposta_selecionada: str | None = None,
    index_pre_selecionado: int | None = None,
):
    """Renderiza uma questão de forma consistente — selo de autenticidade
    (quando há banca/ano), enunciado, imagem e alternativas — usado nas 4
    telas que mostram questão (Praticar, Revisão Espaçada, Simulado, Banco
    de Questões), que antes reimplementavam isso de 4 jeitos ligeiramente
    diferentes.

    `modo="interativa"`: mostra `st.radio` (sem alternativa pré-marcada por
    padrão, pra não induzir resposta — `index_pre_selecionado` só é usado
    pelo Simulado, que permite voltar numa questão já respondida) e
    devolve a letra escolhida (ou `None` se nada foi marcado ainda).

    `modo="leitura"`: alternativas como texto estático, com a correta
    marcada; se `resposta_selecionada` vier preenchida e for diferente da
    correta, marca ela como "(sua resposta)". Não devolve nada.
    """
    banca = q["banca"]
    if banca:
        ano = q["ano"]
        st.markdown(
            f"""
            <div class="qs-selo">
                <span class="qs-selo-banca">{icon_svg("badge-check", size=14)} {banca}</span>
                <span class="qs-selo-ano">{ano if ano else ""}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(f"### {q['enunciado']}")
    if q["imagem"]:
        st.image(bytes(q["imagem"]), use_container_width=True)

    alternativas = q["alternativas"]
    if isinstance(alternativas, str):
        alternativas = json.loads(alternativas)

    form_section_label("Alternativas")

    if modo == "interativa":
        opcoes = list(alternativas.keys())
        return st.radio(
            "Alternativas",
            options=opcoes,
            index=index_pre_selecionado,
            format_func=lambda k: f"{k}) {alternativas[k]}",
            key=key,
            label_visibility="collapsed",
        )

    for letra, texto in alternativas.items():
        correta = letra == q["resposta_correta"]
        marcador = ":material/check_circle:" if correta else ":material/radio_button_unchecked:"
        sufixo = ""
        if resposta_selecionada and letra == resposta_selecionada and not correta:
            sufixo = " *(sua resposta)*"
        st.write(f"{marcador} **{letra})** {texto}{sufixo}")
    return None
