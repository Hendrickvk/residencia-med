"""
Sistema de design da plataforma — tokens, CSS global, ícones (Lucide,
MIT license) e componentes de layout compartilhados entre todas as
páginas. Reescrito por completo para o redesign visual "vocabulário de
laudo clínico" (ver REDESIGN.md): densidade de informação alta,
alinhamento rigoroso, números como protagonistas, cor só como sinal.

Ícones usam SVG embutido (Lucide) em vez de Material Symbols — dá
controle total de traço/tamanho/cor via CSS (`currentColor`) e evita
qualquer flash de fonte de ícone não carregada.
"""

import json

import streamlit as st

# ---------------------------------------------------------------------------
# Ícones (Lucide — https://lucide.dev, MIT license)
# ---------------------------------------------------------------------------
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
    "search": """
        <path d="m21 21-4.34-4.34" /><circle cx="11" cy="11" r="8" />
    """,
    "flame": """
        <path d="M12 3q1 4 4 6.5t3 5.5a1 1 0 0 1-14 0 5 5 0 0 1 1-3 1 1 0 0 0 5 0c0-2-1.5-3-1.5-5q0-2 2.5-4" />
    """,
    "sun": """
        <circle cx="12" cy="12" r="4" /><path d="M12 2v2" /><path d="M12 20v2" />
        <path d="m4.93 4.93 1.41 1.41" /><path d="m17.66 17.66 1.41 1.41" />
        <path d="M2 12h2" /><path d="M20 12h2" />
        <path d="m6.34 17.66-1.41 1.41" /><path d="m19.07 4.93-1.41 1.41" />
    """,
    "moon": """
        <path d="M20.985 12.486a9 9 0 1 1-9.473-9.472c.405-.022.617.46.402.803a6 6 0 0 0 8.268 8.268c.344-.215.825-.004.803.401" />
    """,
    "chevron-left": """<path d="m15 18-6-6 6-6" />""",
    "chevron-right": """<path d="m9 18 6-6-6-6" />""",
    "chevron-down": """<path d="m6 9 6 6 6-6" />""",
    "x": """<path d="M18 6 6 18" /><path d="m6 6 12 12" />""",
    "check": """<path d="M20 6 9 17l-5-5" />""",
    "flag": """
        <path d="M4 22V4a1 1 0 0 1 .4-.8A6 6 0 0 1 8 2c3 0 5 2 7.333 2q2 0 3.067-.8A1 1 0 0 1 20 4v10a1 1 0 0 1-.4.8A6 6 0 0 1 16 16c-3 0-5-2-8-2a6 6 0 0 0-4 1.528" />
    """,
    "triangle-alert": """
        <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3" />
        <path d="M12 9v4" /><path d="M12 17h.01" />
    """,
    "trash-2": """
        <path d="M10 11v6" /><path d="M14 11v6" />
        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" /><path d="M3 6h18" />
        <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    """,
    "filter": """
        <path d="M10 20a1 1 0 0 0 .553.895l2 1A1 1 0 0 0 14 21v-7a2 2 0 0 1 .517-1.341L21.74 4.67A1 1 0 0 0 21 3H3a1 1 0 0 0-.742 1.67l7.225 7.989A2 2 0 0 1 10 14z" />
    """,
    "external-link": """
        <path d="M15 3h6v6" /><path d="M10 14 21 3" />
        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
    """,
    "calendar": """
        <path d="M8 2v3" /><path d="M16 2v3" />
        <rect x="3" y="3" width="18" height="18" rx="2" /><path d="M3 9h18" />
    """,
    "target": """
        <circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="6" /><circle cx="12" cy="12" r="2" />
    """,
    "arrow-right": """<path d="M5 12h14" /><path d="m12 5 7 7-7 7" />""",
    "circle-user": """
        <circle cx="12" cy="12" r="10" /><circle cx="12" cy="10" r="3" />
        <path d="M7 20.662V19a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v1.662" />
    """,
    "sliders-horizontal": """
        <path d="M10 5H3" /><path d="M12 19H3" /><path d="M14 3v4" /><path d="M16 17v4" />
        <path d="M21 12h-9" /><path d="M21 19h-5" /><path d="M21 5h-7" /><path d="M8 10v4" /><path d="M8 12H3" />
    """,
    "list-checks": """
        <path d="M13 5h8" /><path d="M13 12h8" /><path d="M13 19h8" />
        <path d="m3 17 2 2 4-4" /><path d="m3 7 2 2 4-4" />
    """,
    "rotate-ccw": """<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" /><path d="M3 3v5h5" />""",
    "plus": """<path d="M5 12h14" /><path d="M12 5v14" />""",
    "upload": """
        <path d="M12 3v12" /><path d="m17 8-5-5-5 5" />
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    """,
    "download": """
        <path d="M12 15V3" /><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="m7 10 5 5 5-5" />
    """,
    "table-2": """<path d="M3 9h18" /><path d="M9 3v18" /><rect x="3" y="3" width="18" height="18" rx="2" />""",
    "clipboard-list": """
        <rect width="8" height="4" x="8" y="2" rx="1" ry="1" />
        <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
        <path d="M12 11h4" /><path d="M12 16h4" /><path d="M8 11h.01" /><path d="M8 16h.01" />
    """,
    "info": """<circle cx="12" cy="12" r="10" /><path d="M12 16v-4" /><path d="M12 8h.01" />""",
    "x-circle": """<circle cx="12" cy="12" r="10" /><path d="m15 9-6 6" /><path d="m9 9 6 6" />""",
    "panel-left-close": """
        <rect width="18" height="18" x="3" y="3" rx="2" /><path d="M9 3v18" /><path d="m16 15-3-3 3-3" />
    """,
    "panel-left-open": """
        <rect width="18" height="18" x="3" y="3" rx="2" /><path d="M9 3v18" /><path d="m14 9 3 3-3 3" />
    """,
    "log-out": """
        <path d="m16 17 5-5-5-5" /><path d="M21 12H9" /><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
    """,
    "clock": """<circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" />""",
    "settings": """
        <path d="M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915" />
        <circle cx="12" cy="12" r="3" />
    """,
    "shield-check": """
        <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" />
        <path d="m9 12 2 2 4-4" />
    """,
}


def icon_svg(name: str, size: int = 20, stroke_width: float = 2) -> str:
    inner = _ICONS.get(name, "")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round">{inner}</svg>'
    )


# ---------------------------------------------------------------------------
# Tokens de design (ver REDESIGN.md, seção 2)
# ---------------------------------------------------------------------------
_TOKENS_LIGHT = {
    "ink-900": "#0D1B2A", "ink-700": "#1B2D42", "ink-500": "#46586E", "ink-300": "#8797AB",
    "line": "#E1E6EC", "canvas": "#F4F6F9", "surface": "#FFFFFF",
    "action": "#1F4FD8", "action-hover": "#1A43B8", "action-soft": "#EAF0FF",
    "correct": "#0F7A5A", "wrong": "#C2344B", "warn": "#B87309",
    "correct-soft": "#E7F4EF", "wrong-soft": "#FBEBEE", "warn-soft": "#FDF3E3",
    "scheme": "light",
}
_TOKENS_DARK = {
    "ink-900": "#0B1420", "ink-700": "#E6EBF2", "ink-500": "#9FB0C3", "ink-300": "#5B6B80",
    "line": "#22313F", "canvas": "#0B1420", "surface": "#121E2C",
    "action": "#5B8DFF", "action-hover": "#7FA3FF", "action-soft": "#1A2740",
    "correct": "#3FBD8F", "wrong": "#E8677F", "warn": "#E0A23B",
    "correct-soft": "#123227", "wrong-soft": "#341823", "warn-soft": "#332510",
    "scheme": "dark",
}


def _css_tokens(tokens: dict) -> str:
    return "\n".join(f"    --{k}: {v};" for k, v in tokens.items() if k != "scheme")


_CSS_TEMPLATE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {{
{tokens}
}}
html {{ color-scheme: {scheme}; }}

/* ---- Cromagem padrão do Streamlit ------------------------------------ */
#MainMenu, footer, header[data-testid="stHeader"],
[data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"] {{
    display: none !important;
}}
[data-testid="stSidebarCollapseButton"] {{ display: none; }}
[data-testid="collapsedControl"] {{ display: none; }}

/* ---- Base -------------------------------------------------------------- */
html, body, [class*="css"] {{
    font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}
[data-testid="stAppViewContainer"] {{
    background: var(--canvas);
}}
[data-testid="stAppViewContainer"] .block-container {{
    max-width: 1160px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}}
h1, h2, h3, h4, h5, h6 {{ color: var(--ink-700); font-weight: 600; }}
p, span, div, label {{ color: var(--ink-700); }}
.mono, [data-testid="stMetricValue"] {{
    font-family: 'IBM Plex Mono', monospace;
    font-variant-numeric: tabular-nums;
}}
a {{ color: var(--action); }}
hr {{ border-color: var(--line); }}

/* ---- Foco por teclado --------------------------------------------------- */
button:focus-visible, a:focus-visible, input:focus-visible, textarea:focus-visible,
[tabindex]:focus-visible {{
    outline: 2px solid var(--action) !important;
    outline-offset: 2px !important;
}}
@media (prefers-reduced-motion: reduce) {{
    * {{ animation-duration: 0.001ms !important; transition-duration: 0.001ms !important; }}
}}

/* ---- Rail (st.sidebar) -------------------------------------------------- */
[data-testid="stSidebar"] {{
    background: var(--ink-900);
    border-right: none;
    overflow-x: hidden;
    transition: width 0.18s cubic-bezier(0.2,0,0.2,1), min-width 0.18s cubic-bezier(0.2,0,0.2,1);
}}
[data-testid="stSidebar"] * {{ color: rgba(255,255,255,.86); }}
[data-testid="stSidebar"] button p, [data-testid="stSidebar"] .stMarkdownContainer p {{
    white-space: nowrap;
}}
[data-testid="stSidebarUserContent"] {{ padding-top: 1.1rem; }}

.rail-brand {{
    display: flex; align-items: center; gap: 0.55rem;
    padding: 0 0.9rem 1rem 0.9rem;
}}
.rail-brand-mark {{
    width: 3px; height: 16px; background: var(--action); border-radius: 2px; flex-shrink: 0;
}}
.rail-brand-text {{ font-size: 0.95rem; font-weight: 600; color: #FFFFFF; white-space: nowrap; }}

.rail-group-label {{
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase;
    color: rgba(255,255,255,.4); padding: 0.9rem 0.9rem 0.35rem;
}}
[data-testid="stSidebar"] hr {{
    border-color: rgba(255,255,255,.08); margin: 0.4rem 0;
}}

/* Botão "Praticar agora" (primário, largura total, sempre visível) */
[data-testid="stSidebar"] .st-key-rail_cta .stButton button {{
    background: var(--action) !important;
    border: none !important;
    color: #FFFFFF !important;
    font-weight: 500 !important;
    height: 40px !important;
    border-radius: 6px !important;
}}
[data-testid="stSidebar"] .st-key-rail_cta .stButton button:hover {{
    background: var(--action-hover) !important;
}}

/* Itens de navegação — st.button por página, restilizados como linhas de menu */
[data-testid="stSidebar"] .st-key-nav_area .stButton button {{
    justify-content: flex-start;
    gap: 0.6rem;
    height: 40px;
    padding-left: 0.75rem;
    border-radius: 6px;
    font-weight: 500;
    font-size: 0.86rem;
    transition: background 0.12s ease;
}}
[data-testid="stSidebar"] .st-key-nav_area .stButton button[kind="secondary"] {{
    background: transparent;
    border-color: transparent;
    color: rgba(255,255,255,.72) !important;
}}
[data-testid="stSidebar"] .st-key-nav_area .stButton button[kind="secondary"]:hover {{
    background: rgba(255,255,255,.06);
    color: #FFFFFF !important;
}}
[data-testid="stSidebar"] .st-key-nav_area .stButton button[kind="primary"] {{
    background: rgba(255,255,255,.10) !important;
    border: none !important;
    border-left: 3px solid var(--action) !important;
    color: #FFFFFF !important;
    padding-left: calc(0.75rem - 3px);
}}

.rail-footer {{
    padding: 0.6rem 0.9rem 0.2rem;
    font-size: 0.72rem;
    color: rgba(255,255,255,.4);
    white-space: nowrap;
}}

/* Botão de colapsar/expandir a rail */
[data-testid="stSidebar"] .st-key-rail_toggle .stButton button {{
    background: transparent !important;
    border: none !important;
    color: rgba(255,255,255,.55) !important;
    width: 32px !important; height: 32px !important;
    min-width: 32px !important; min-height: 32px !important;
    padding: 0 !important;
}}
[data-testid="stSidebar"] .st-key-rail_toggle .stButton button:hover {{
    background: rgba(255,255,255,.08) !important;
    color: #FFFFFF !important;
}}

/* ---- Topbar -------------------------------------------------------------- */
.st-key-topbar {{
    position: sticky; top: 0; z-index: 100;
    background: var(--surface);
    border-bottom: 1px solid var(--line);
    margin: -1.5rem 0 1.5rem;
    padding: 0.5rem 0 !important;
}}
.st-key-topbar [data-testid="stHorizontalBlock"] {{ align-items: center; }}
.topbar-title {{ font-size: 0.95rem; font-weight: 600; color: var(--ink-700); white-space: nowrap; }}
.st-key-topbar [data-testid="stTextInput"] input {{
    height: 34px; font-size: 0.85rem;
}}
.pill {{
    display: inline-flex; align-items: center; gap: 0.3rem;
    height: 30px; padding: 0 0.65rem; border-radius: 999px;
    font-size: 0.78rem; font-weight: 500; white-space: nowrap;
}}
.pill-warn {{ background: var(--warn-soft); color: var(--warn); }}
.pill-correct {{ background: var(--correct-soft); color: var(--correct); }}
.pill-neutral {{ background: var(--canvas); color: var(--ink-500); border: 1px solid var(--line); }}
.st-key-topbar .st-key-theme_toggle button, .st-key-topbar .st-key-avatar_popover button {{
    border-radius: 6px !important;
}}
.st-key-avatar_popover button {{
    width: 34px !important; height: 34px !important; min-width: 34px !important; min-height: 34px !important;
    border-radius: 50% !important; padding: 0 !important;
    background: var(--action-soft) !important; color: var(--action) !important;
    border: none !important; font-weight: 700 !important; font-size: 0.75rem !important;
}}
.st-key-avatar_popover [data-testid="stIconMaterial"] {{ display: none; }}
.st-key-theme_toggle button {{
    width: 34px !important; height: 34px !important; min-width: 34px !important; min-height: 34px !important;
    padding: 0 !important; background: transparent !important; border: 1px solid var(--line) !important;
    color: var(--ink-500) !important;
}}
.st-key-theme_toggle button:hover {{ border-color: var(--ink-300) !important; }}

/* ---- Botões -------------------------------------------------------------- */
.stButton button, .stDownloadButton button, .stLinkButton a, .stFormSubmitButton button {{
    border-radius: 6px;
    font-weight: 500;
    transition: background 0.12s ease, border-color 0.12s ease, transform 0.05s ease;
}}
.stButton button[kind="primary"], .stFormSubmitButton button[kind="primary"] {{
    background: var(--action); border-color: var(--action); color: #fff;
}}
.stButton button[kind="primary"]:hover, .stFormSubmitButton button[kind="primary"]:hover {{
    background: var(--action-hover); border-color: var(--action-hover);
}}
.stButton button[kind="primary"]:active {{ transform: translateY(1px); }}
.stButton button[kind="secondary"] {{
    background: var(--surface); border: 1px solid var(--line); color: var(--ink-700);
}}
.stButton button[kind="secondary"]:hover {{ border-color: var(--ink-300); }}
.stButton button:disabled {{
    background: var(--line) !important; color: var(--ink-300) !important;
    border-color: var(--line) !important; cursor: not-allowed;
}}
.stButton button:has(> div > svg), .stButton button {{ letter-spacing: 0; }}

/* ---- Campos de formulário ------------------------------------------------ */
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input, [data-baseweb="select"] > div,
[data-testid="stDateInput"] input {{
    border-radius: 6px !important;
    border: 1px solid var(--line) !important;
    background: var(--surface) !important;
    color: var(--ink-700) !important;
}}
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus,
[data-testid="stNumberInput"] input:focus {{
    border-color: var(--action) !important;
    box-shadow: 0 0 0 3px var(--action-soft) !important;
}}
[data-baseweb="select"]:focus-within > div {{
    border-color: var(--action) !important;
    box-shadow: 0 0 0 3px var(--action-soft) !important;
}}
label, [data-testid="stWidgetLabel"] p {{
    font-size: 0.83rem !important; font-weight: 500 !important; color: var(--ink-700) !important;
}}
[data-testid="stCaptionContainer"], .stCaption {{
    color: var(--ink-500) !important; font-size: 0.8rem !important;
}}

/* ---- Cards / painéis / expanders ----------------------------------------- */
[data-testid="stVerticalBlockBorderWrapper"] {{
    border: 1px solid var(--line);
    border-radius: 10px;
    background: var(--surface);
}}
[data-testid="stExpander"] {{
    border: 1px solid var(--line) !important;
    border-radius: 10px !important;
    background: var(--surface) !important;
}}
[data-testid="stExpander"] summary {{ color: var(--ink-700); font-weight: 500; }}
[data-testid="stMetric"] {{
    background: var(--surface); border: 1px solid var(--line); border-radius: 10px;
    padding: 0.9rem 1.1rem;
}}
[data-testid="stMetricLabel"] {{ color: var(--ink-500) !important; font-size: 0.78rem !important; }}
[data-testid="stMetricValue"] {{ color: var(--ink-700) !important; }}

/* ---- Alertas (st.success/error/warning/info) ------------------------------ */
[data-testid="stAlertContentSuccess"] {{ color: var(--correct) !important; }}
[data-testid="stAlertContentError"] {{ color: var(--wrong) !important; }}
[data-testid="stAlertContentWarning"] {{ color: var(--warn) !important; }}
div[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) {{
    background: var(--correct-soft); border: 1px solid var(--correct);
}}
div[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) {{
    background: var(--wrong-soft); border: 1px solid var(--wrong);
}}
div[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) {{
    background: var(--warn-soft); border: 1px solid var(--warn);
}}

/* ---- Modal (st.dialog) ---------------------------------------------------- */
/* O card do dialog não é pintado por nenhum data-testid/classe estável — cai
   no tema NATIVO do Streamlit (config.toml, sempre claro/estático, porque o
   [theme] do config.toml não pode responder à alternância de tema por
   usuário/sessão) em vez das variáveis --canvas/--surface daqui. Sem isso,
   o modal ficava sempre com fundo claro e texto na cor do tema atual —
   ilegível no escuro. `> div` é o card em si (filho direto de
   [data-testid="stDialog"], que é só o overlay/backdrop). */
[data-testid="stDialog"] > div {{
    background: var(--surface) !important;
}}
[data-testid="stDialog"] h2 {{ color: var(--ink-700); }}

/* ---- Tabelas (st.dataframe) ------------------------------------------------ */
[data-testid="stDataFrame"] {{ border: 1px solid var(--line); border-radius: 8px; }}

/* ---- Progresso ------------------------------------------------------------ */
[data-testid="stProgress"] > div > div {{ background: var(--action); }}
[data-testid="stProgress"] > div {{ background: var(--line); }}

/* =====================================================================
   COMPONENTES CUSTOM (marcação própria, ver REDESIGN.md seção 4)
   ===================================================================== */

/* ---- Chip removível (filtros ativos) --------------------------------- */
.chip-row {{ display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.5rem 0 0.9rem; }}
.chip {{
    display: inline-flex; align-items: center; gap: 0.35rem;
    background: var(--action-soft); color: var(--action);
    border-radius: 999px; padding: 0.25rem 0.7rem; font-size: 0.78rem; font-weight: 500;
}}

/* ---- Estado vazio (sem ilustração) ------------------------------------ */
.empty-state {{ padding: 1.6rem 0; }}
.empty-state-text {{ font-size: 0.92rem; color: var(--ink-500); margin-bottom: 0.9rem; }}

/* ---- Painel de diagnóstico (Painel / 4.1) ------------------------------ */
/* As 3 faixas são um st.columns([0.4,0.35,0.25]) real (não HTML puro),
   porque a faixa 3 precisa de um st.button de verdade embutido — CSS
   simula os divisores verticais nas bordas das colunas do Streamlit. */
.st-key-diag_panel {{
    background: var(--surface); border: 1px solid var(--line); border-radius: 10px;
    padding: 1.3rem 1.4rem; margin-bottom: 1.5rem;
}}
.st-key-diag_panel [data-testid="stHorizontalBlock"] {{ align-items: center; gap: 0; }}
.st-key-diag_panel [data-testid="stHorizontalBlock"] > div {{ min-width: 0; }}
.st-key-diag_panel [data-testid="stHorizontalBlock"] > div:not(:last-child) {{
    border-right: 1px solid var(--line); padding-right: 1.4rem;
}}
.st-key-diag_panel [data-testid="stHorizontalBlock"] > div:not(:first-child) {{ padding-left: 1.4rem; }}
.diag-f3-wrap {{ display: flex; flex-direction: column; align-items: center; gap: 0.5rem; }}
.diag-display {{
    font-size: 34px; line-height: 1.15; font-weight: 600; letter-spacing: -0.02em;
    color: var(--ink-700); font-family: 'IBM Plex Mono', monospace;
}}
.diag-frase {{ font-size: 15px; line-height: 1.55; color: var(--ink-700); margin-top: 0.5rem; }}
.diag-caption {{ font-size: 0.78rem; color: var(--ink-500); margin-bottom: 0.3rem; text-transform: uppercase; letter-spacing: 0.04em; font-weight: 600; }}
.diag-sub {{ font-size: 0.85rem; color: var(--ink-500); text-align: center; }}

/* Anel de progresso (meta do dia) via conic-gradient */
.ring {{
    --pct: 0;
    width: 76px; height: 76px; border-radius: 50%;
    background: conic-gradient(var(--action) calc(var(--pct) * 1%), var(--line) 0);
    display: flex; align-items: center; justify-content: center;
}}
.ring-inner {{
    width: 60px; height: 60px; border-radius: 50%; background: var(--surface);
    display: flex; align-items: center; justify-content: center;
    font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 0.95rem; color: var(--ink-700);
}}

/* Sparkline (14 dias) */
.spark-wrap {{ display: flex; align-items: flex-end; gap: 0.6rem; }}
.spark-value {{ font-family: 'IBM Plex Mono', monospace; font-size: 0.95rem; font-weight: 600; color: var(--ink-700); }}

/* ---- Lista "onde você está errando" (linha-barra) ---------------------- */
.err-row {{
    position: relative; display: flex; align-items: center; justify-content: space-between;
    height: 44px; padding: 0 0.9rem; border-radius: 6px; border: 1px solid transparent;
    margin-bottom: 0.4rem; overflow: hidden; cursor: pointer;
}}
.err-row-fill {{
    position: absolute; inset: 0; z-index: 0;
}}
.err-row-label, .err-row-value {{ position: relative; z-index: 1; font-size: 0.88rem; }}
.err-row-label {{ color: var(--ink-700); font-weight: 500; }}
.err-row-value {{ font-family: 'IBM Plex Mono', monospace; color: var(--ink-500); font-size: 0.82rem; white-space: nowrap; }}
.err-row:hover {{ border-color: var(--action); }}
.err-amostra {{ font-size: 0.82rem; color: var(--ink-500); }}

/* ---- Selo de autenticidade da questão ---------------------------------- */
.qs-selo {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.35rem 0 0.6rem; margin-bottom: 0.7rem; border-bottom: 1px solid var(--line);
}}
.qs-selo-banca {{
    display: flex; align-items: center; gap: 0.35rem;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;
    color: var(--action);
}}
.qs-selo-ano {{ font-size: 0.78rem; color: var(--ink-500); font-family: 'IBM Plex Mono', monospace; }}
.qs-metadados {{ font-size: 0.8rem; color: var(--ink-500); margin-bottom: 0.6rem; }}
.qs-enunciado {{ font-size: 17px; line-height: 1.65; color: var(--ink-700); max-width: 68ch; margin-bottom: 1rem; }}

/* ---- Alternativas interativas (st.radio restilizado) -------------------- */
/* Estrutura real do Streamlit: [role="radiogroup"] > label > (span com o
   <input> nativo dentro) + (div com o texto, via stMarkdownContainer).
   Não tem um "div da letra" pra estilizar — a letra é gerada via
   `label::before` (conteúdo por posição, nth-of-type) e o span nativo
   (círculo) é escondido. O seletor raiz usa `[class*=...]` porque a
   classe `st-key-<key>` do Streamlit vai no `.stElementContainer` que
   envolve o widget (não dá pra "abraçar" o radio com uma div própria via
   st.markdown — cada chamada de st.markdown/st.radio gera elementos
   IRMÃOS no DOM, uma tag aberta numa chamada nunca envolve a próxima). */
[class*="st-key-radioalt__"] [role="radiogroup"] {{ gap: 0 !important; }}
[class*="st-key-radioalt__"] [role="radiogroup"] > label {{
    display: flex !important; align-items: center !important;
    min-height: 52px; padding: 0.4rem 0.9rem 0.4rem 0.6rem;
    border: 1px solid var(--line); border-radius: 6px; margin-bottom: 0.5rem !important;
    background: var(--surface); transition: background 0.12s ease, border-color 0.12s ease;
    position: relative; cursor: pointer;
}}
[class*="st-key-radioalt__"] [role="radiogroup"] > label:hover {{
    background: var(--action-soft); border-color: var(--action);
}}
[class*="st-key-radioalt__"] [role="radiogroup"] > label:has(input:checked) {{
    border: 2px solid var(--action);
}}
[class*="st-key-radioalt__"] [role="radiogroup"] > label > span:first-child {{
    display: none;
}}
[class*="st-key-radioalt__"] [role="radiogroup"] > label::before {{
    width: 28px; height: 28px; min-width: 28px; border-radius: 6px; border: 1px solid var(--line);
    display: flex; align-items: center; justify-content: center; margin-right: 0.75rem;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; font-weight: 600; color: var(--ink-500);
    background: var(--canvas); flex-shrink: 0;
}}
[class*="st-key-radioalt__"] [role="radiogroup"] > label:has(input:checked)::before {{
    background: var(--action); border-color: var(--action); color: #fff;
}}
[class*="st-key-radioalt__"] [role="radiogroup"] > label:nth-of-type(1)::before {{ content: "A"; }}
[class*="st-key-radioalt__"] [role="radiogroup"] > label:nth-of-type(2)::before {{ content: "B"; }}
[class*="st-key-radioalt__"] [role="radiogroup"] > label:nth-of-type(3)::before {{ content: "C"; }}
[class*="st-key-radioalt__"] [role="radiogroup"] > label:nth-of-type(4)::before {{ content: "D"; }}
[class*="st-key-radioalt__"] [role="radiogroup"] > label:nth-of-type(5)::before {{ content: "E"; }}
[class*="st-key-radioalt__"] [role="radiogroup"] > label [data-testid="stMarkdownContainer"] p {{
    font-size: 15px; color: var(--ink-700);
}}

/* ---- Alternativas de resultado (estático, pós-confirmação) --------------- */
.alt-linha {{
    display: flex; align-items: center; gap: 0.75rem; min-height: 52px;
    padding: 0.4rem 0.9rem; border: 1px solid var(--line); border-radius: 6px;
    margin-bottom: 0.5rem; position: relative; overflow: hidden;
}}
.alt-linha.correta {{ background: var(--correct-soft); border-color: var(--correct); }}
.alt-linha.errada {{ background: var(--wrong-soft); border-color: var(--wrong); }}
.alt-letra {{
    width: 28px; height: 28px; min-width: 28px; border-radius: 6px; border: 1px solid var(--line);
    display: flex; align-items: center; justify-content: center; z-index: 1;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; font-weight: 600; color: var(--ink-500);
    background: var(--surface);
}}
.alt-linha.correta .alt-letra {{ background: var(--correct); border-color: var(--correct); color: #fff; }}
.alt-linha.errada .alt-letra {{ background: var(--wrong); border-color: var(--wrong); color: #fff; }}
.alt-texto {{ font-size: 15px; color: var(--ink-700); z-index: 1; flex: 1; }}
.alt-sufixo {{ font-size: 0.78rem; color: var(--ink-500); z-index: 1; white-space: nowrap; }}
.alt-peer-bar {{
    position: absolute; left: 0; bottom: 0; height: 3px; background: var(--ink-300); opacity: 0.5; z-index: 0;
}}

/* ---- Badge de faixa (usado em vários lugares para número em destaque) --- */
.faixa-row {{ display: flex; flex-direction: column; gap: 0.4rem; }}
.faixa-item {{
    display: flex; align-items: center; justify-content: space-between; gap: 0.75rem;
    background: var(--surface); border: 1px solid var(--line); border-left: 4px solid var(--fx-cor, var(--ink-300));
    border-radius: 6px; padding: 0.55rem 0.9rem;
}}
.faixa-label {{ font-size: 0.88rem; color: var(--ink-700); font-weight: 500; }}
.faixa-valor {{
    font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 0.85rem;
    color: var(--fx-cor, var(--ink-700)); white-space: nowrap;
}}

/* ---- Coluna única de formulário (Nova Questão, REDESIGN.md §4.6) --------- */
.st-key-form_col {{ max-width: 640px; }}

/* ---- Cronômetro em destaque (Simulado) ------------------------------------ */
.timer-hero {{
    display: inline-flex; align-items: center; gap: 0.5rem;
    font-family: 'IBM Plex Mono', monospace; font-size: 1.4rem; font-weight: 600;
    padding: 0.4rem 0.9rem; border-radius: 8px; border: 1px solid var(--line);
}}

/* ---- Grade de navegação do simulado ---------------------------------------- */
.st-key-sim_grid .stButton button {{
    min-width: 36px !important; height: 36px !important; padding: 0 !important;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem;
}}

/* ---- Rótulo de seção em formulário --------------------------------------- */
.form-section-label {{
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase;
    color: var(--ink-500); margin: 0.9rem 0 0.35rem;
}}

/* ---- Cabeçalho de página (título simples, sem ícone decorativo grande) --- */
.page-title {{ font-size: 24px; font-weight: 600; line-height: 1.25; letter-spacing: -0.01em; color: var(--ink-700); margin-bottom: 0.3rem; }}
.page-subtitle {{ font-size: 0.88rem; color: var(--ink-500); margin-bottom: 1.2rem; }}
</style>
"""


def inject_theme_css(tema: str = "light"):
    tokens = _TOKENS_DARK if tema == "dark" else _TOKENS_LIGHT
    st.markdown(
        _CSS_TEMPLATE.format(tokens=_css_tokens(tokens), scheme=tokens["scheme"]),
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Componentes de layout
# ---------------------------------------------------------------------------

def page_title(titulo: str, subtitulo: str = ""):
    st.markdown(f'<div class="page-title">{titulo}</div>', unsafe_allow_html=True)
    if subtitulo:
        st.markdown(f'<div class="page-subtitle">{subtitulo}</div>', unsafe_allow_html=True)


def empty_state(
    texto: str,
    cta_label: str | None = None,
    cta_icon: str | None = None,
    cta_pagina: str | None = None,
):
    """Estado vazio sem ilustração (REDESIGN.md §5): uma frase que orienta e,
    no máximo, um único botão de ação. `cta_pagina` grava em
    `st.session_state["_forcar_pagina"]` (chave separada, consumida pelo
    app.py antes de recriar os botões de navegação — widgets com `key` não
    podem ter o session_state sobrescrito depois de instanciados)."""
    st.markdown(
        f'<div class="empty-state"><div class="empty-state-text">{texto}</div></div>',
        unsafe_allow_html=True,
    )
    if cta_label and cta_pagina:
        if st.button(
            cta_label, icon=cta_icon, type="secondary",
            key=f"es_cta_{abs(hash((texto, cta_pagina)))}",
        ):
            st.session_state["_forcar_pagina"] = cta_pagina
            st.rerun()


def chips(itens: list[str]):
    if not itens:
        return
    partes = ['<div class="chip-row">']
    for texto in itens:
        partes.append(f'<span class="chip">{texto}</span>')
    partes.append("</div>")
    st.markdown("".join(partes), unsafe_allow_html=True)


def cor_semantica_pct(pct: float) -> str:
    """Cor semântica pra uma % de acerto (REDESIGN.md §4.1: <40 crítico,
    40-69 atenção, >=70 bom)."""
    if pct < 40:
        return "var(--wrong)"
    if pct < 70:
        return "var(--warn)"
    return "var(--correct)"


def _cor_semantica_fundo(pct: float) -> str:
    if pct < 40:
        return "var(--wrong-soft)"
    if pct < 70:
        return "var(--warn-soft)"
    return "var(--correct-soft)"


def faixa_row(itens: list[dict]):
    """Lista de resultados em linha fina com barra lateral colorida —
    `itens`: [{"label": str, "valor": str, "cor": "var(--x)"}]."""
    partes = ['<div class="faixa-row">']
    for item in itens:
        cor = item.get("cor", "var(--ink-300)")
        partes.append(
            f'<div class="faixa-item" style="--fx-cor:{cor};">'
            f'<span class="faixa-label">{item["label"]}</span>'
            f'<span class="faixa-valor">{item["valor"]}</span>'
            f'</div>'
        )
    partes.append("</div>")
    st.markdown("".join(partes), unsafe_allow_html=True)


def lista_erro_barra(linhas: list[dict], *, key_prefix: str):
    """"Onde você está errando" (REDESIGN.md §4.1) — cada linha é a própria
    barra (fundo preenchido proporcionalmente ao % de acerto), com botão
    "Praticar N desta área" que aparece rente à linha. `linhas`:
    [{"area_id":, "nome":, "pct":, "acertos":, "total":}]. Devolve o
    area_id clicado (para abrir a sessão de prática já filtrada), ou None.
    """
    clicado = None
    for item in linhas:
        pct = item["pct"]
        cor_fundo = _cor_semantica_fundo(pct)
        col_row, col_btn = st.columns([5, 1.3])
        with col_row:
            st.markdown(
                f"""
                <div class="err-row">
                    <div class="err-row-fill" style="background:{cor_fundo}; width:{max(pct, 3)}%;"></div>
                    <span class="err-row-label">{item['nome']}</span>
                    <span class="err-row-value">{pct}% · {int(item['acertos'])}/{int(item['total'])}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_btn:
            if st.button(
                f"Praticar 10", key=f"{key_prefix}_{item['area_id']}",
                use_container_width=True,
            ):
                clicado = item["area_id"]
    return clicado


def sparkline_svg(valores: list[float], altura: int = 48, largura: int = 220) -> str:
    """Minigráfico de linha sem eixos/grade, com o último ponto marcado e
    rotulado — usado no Painel (últimos 14 dias de % de acerto)."""
    if not valores or len(valores) < 2:
        return ""
    vmin, vmax = min(valores), max(valores)
    span = (vmax - vmin) or 1
    n = len(valores)
    pontos = []
    for i, v in enumerate(valores):
        x = (i / (n - 1)) * (largura - 8) + 4
        y = altura - 4 - ((v - vmin) / span) * (altura - 8)
        pontos.append((x, y))
    path = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pontos)
    ux, uy = pontos[-1]
    return f"""
    <svg width="{largura}" height="{altura}" viewBox="0 0 {largura} {altura}" style="overflow:visible;">
        <path d="{path}" fill="none" stroke="var(--action)" stroke-width="2"
              stroke-linecap="round" stroke-linejoin="round" />
        <circle cx="{ux:.1f}" cy="{uy:.1f}" r="3.5" fill="var(--action)" />
    </svg>
    """


def anel_progresso(pct: float, rotulo: str) -> str:
    pct = max(0, min(100, pct))
    return f"""
    <div class="ring" style="--pct:{pct};">
        <div class="ring-inner">{rotulo}</div>
    </div>
    """


def grafico_barras_horizontais(df, categoria_col: str, valor_col: str, *, cor: str = "#1F4FD8", sufixo: str = "%"):
    """Barras horizontais com rótulo de valor na ponta (REDESIGN.md §6) —
    substitui `st.bar_chart` (que não permite orientação horizontal nem
    tema customizado). Requer `altair` (dependência do próprio Streamlit)."""
    import altair as alt

    base = alt.Chart(df).encode(
        y=alt.Y(f"{categoria_col}:N", sort="-x", title=None,
                axis=alt.Axis(labelColor="#46586E", labelFontSize=12, domain=False, ticks=False)),
        x=alt.X(f"{valor_col}:Q", title=None,
                axis=alt.Axis(grid=True, gridColor="#E1E6EC", gridOpacity=0.5, labels=False, domain=False, ticks=False)),
    )
    barras = base.mark_bar(color=cor, cornerRadiusEnd=3, height=16)
    rotulos = base.mark_text(align="left", dx=5, color="#1B2D42", fontSize=12).encode(
        text=alt.Text(f"{valor_col}:Q", format=".1f"),
    )
    chart = (barras + rotulos).properties(height=max(28 * len(df), 80)).configure_view(strokeWidth=0)
    st.altair_chart(chart, use_container_width=True)


def form_section_label(texto: str):
    st.markdown(f'<div class="form-section-label">{texto}</div>', unsafe_allow_html=True)


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
    _dialog_confirmar_exclusao(mensagem, on_confirmar)


# ---------------------------------------------------------------------------
# Questão — selo, enunciado, alternativas (interativas ou de resultado)
# ---------------------------------------------------------------------------

def render_cabecalho_questao(q):
    """Selo de autenticidade (banca/ano) + metadados discretos + enunciado
    + imagem. Não inclui alternativas — ver `render_alternativas_*`."""
    banca = q["banca"]
    if banca:
        ano = q["ano"]
        st.markdown(
            f"""
            <div class="qs-selo">
                <span class="qs-selo-banca">{icon_svg("badge-check", size=13)} {banca}</span>
                <span class="qs-selo-ano">{ano if ano else ""}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    metadados = []
    if "area" in q.keys() and q["area"]:
        metadados.append(q["area"])
    if "subtopico" in q.keys() and q["subtopico"]:
        metadados.append(q["subtopico"])
    if metadados:
        st.markdown(f'<div class="qs-metadados">{" · ".join(metadados)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="qs-enunciado">{q["enunciado"]}</div>', unsafe_allow_html=True)
    if q["imagem"]:
        st.image(bytes(q["imagem"]), use_container_width=True)


def _alternativas_dict(q):
    alternativas = q["alternativas"]
    if isinstance(alternativas, str):
        alternativas = json.loads(alternativas)
    return alternativas


def render_alternativas_interativas(q, *, key: str, index_pre_selecionado: int | None = None):
    """Alternativas como linhas clicáveis (st.radio restilizado via CSS —
    ver `[class*="st-key-radioalt__"]` acima). Devolve a letra escolhida ou
    None. O prefixo fixo `radioalt__` no key é o que a CSS usa pra achar
    esse widget especificamente (Streamlit aplica a classe `st-key-<key>`
    no container do próprio widget)."""
    alternativas = _alternativas_dict(q)
    opcoes = list(alternativas.keys())
    return st.radio(
        "Alternativas", options=opcoes, index=index_pre_selecionado,
        format_func=lambda k: alternativas[k], key=f"radioalt__{key}", label_visibility="collapsed",
    )


def render_alternativas_resultado(q, *, resposta_selecionada: str | None = None, distribuicao: dict | None = None):
    """Alternativas estáticas pós-confirmação: a correta em verde, a
    escolhida errada em vermelho, as demais neutras. `distribuicao`
    (opcional): {"A": 42.0, ...} — desenha a barra fina de % dos demais
    usuários dentro de cada linha."""
    alternativas = _alternativas_dict(q)
    correta_letra = q["resposta_correta"]
    partes = []
    for letra, texto in alternativas.items():
        classe = ""
        sufixo = ""
        if letra == correta_letra:
            classe = "correta"
        elif resposta_selecionada and letra == resposta_selecionada:
            classe = "errada"
            sufixo = '<span class="alt-sufixo">sua resposta</span>'
        pct_barra = (distribuicao or {}).get(letra, 0)
        barra_html = f'<div class="alt-peer-bar" style="width:{pct_barra}%;"></div>' if pct_barra else ""
        partes.append(
            f'<div class="alt-linha {classe}">{barra_html}'
            f'<div class="alt-letra">{letra}</div>'
            f'<div class="alt-texto">{texto}</div>{sufixo}</div>'
        )
    st.markdown("".join(partes), unsafe_allow_html=True)
