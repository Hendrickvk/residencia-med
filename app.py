import streamlit as st
import pandas as pd
import json
import random
import datetime

import db
import repeticao_espacada as sr
import importador_questoes as imp_q
import mediafire_import as mf
import auth
import ui

st.set_page_config(
    page_title="Residência Med - Plataforma de Estudos",
    page_icon="🩺",
    layout="wide",
)

# Materiais/questões são um recurso compartilhado entre todos os usuários —
# ações destrutivas ficam restritas a quem está nessa lista.
ADMIN_EMAILS = {"hendrickvk@gmail.com"}

_NOME_DIA_SEMANA = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


# db.init_db() cria tabelas/índices/seed — precisa rodar uma vez, não a cada
# interação (custava ~1.6s por round-trip ao Postgres, em TODO clique).
@st.cache_resource
def _init_db_uma_vez():
    db.init_db()
    return True


_init_db_uma_vez()

if "usuario_id" not in st.session_state:
    ui.inject_theme_css("light")
    auth.render_login_signup()
    st.stop()

# Preferência de tema e data da prova alvo vêm do banco só uma vez por
# sessão de login — depois disso, session_state é a fonte da verdade (evita
# reconsultar o Postgres a cada rerun só pra saber a cor da página).
if "tema" not in st.session_state:
    _usuario_row = db.obter_usuario(st.session_state.usuario_id)
    st.session_state["tema"] = (_usuario_row["tema"] if _usuario_row else None) or "light"
    st.session_state["data_prova_alvo"] = _usuario_row["data_prova_alvo"] if _usuario_row else None

ui.inject_theme_css(st.session_state["tema"])

eh_admin = st.session_state.get("usuario_email") in ADMIN_EMAILS
usuario_id = st.session_state.usuario_id

# ---------------------------------------------------------------------------
# Navegação — grupos "Estudo"/"Acervo" (REDESIGN.md §3). Rótulo (exibido) e
# page_key (usado no roteamento abaixo) são desacoplados de propósito: um
# rename futuro do rótulo do menu não precisa tocar em nenhum `if pagina_atual
# == "..."`, só na tabela abaixo — lição da rodada anterior de redesign, onde
# renomear o rótulo quebrava sessões já abertas com o nome antigo em
# session_state. Ícones são Material Symbols (não os SVG Lucide do resto do
# app) porque `st.button(icon=...)` só aceita esse formato ou emoji — Lucide
# fica reservado para marcação própria (selo, badges, marca).
PAGINAS_NAV = [
    ("Estudo", "Painel", "dashboard", "painel"),
    ("Estudo", "Praticar", "edit_note", "praticar"),
    ("Estudo", "Simulado", "timer", "simulado"),
    ("Estudo", "Revisão espaçada", "psychology", "revisao"),
    ("Estudo", "Materiais", "menu_book", "materiais"),
    ("Acervo", "Banco de questões", "database", "banco"),
    ("Acervo", "Nova questão", "post_add", "nova_questao"),
    ("Acervo", "Importar planilha", "upload_file", "importar"),
    ("Acervo", "Sincronizar MediaFire", "sync", "sincronizar"),
]
LABEL_POR_KEY = {key: label for _, label, _, key in PAGINAS_NAV}


@st.cache_data(ttl=30)
def _contadores_rail():
    return db.contar_questoes(), db.contar_materiais()


@st.cache_data(ttl=60)
def _ofensiva_cache(uid):
    return db.calcular_ofensiva(usuario_id=uid)


# Widgets com `key` não podem ter seu session_state sobrescrito depois de já
# instanciados nesta execução — por isso `ui.empty_state` e os cliques na
# lista de erro do Painel gravam numa chave separada (_forcar_pagina),
# consumida aqui, antes de qualquer botão de navegação existir.
if "_forcar_pagina" in st.session_state:
    st.session_state["pagina_atual"] = st.session_state.pop("_forcar_pagina")
st.session_state.setdefault("pagina_atual", "painel")
st.session_state.setdefault("rail_expandida", True)

expandida = st.session_state["rail_expandida"]

if expandida:
    st.markdown(
        '<style>[data-testid="stSidebar"]{min-width:232px !important;width:232px !important;}</style>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { min-width: 64px !important; width: 64px !important; }
        [data-testid="stSidebarUserContent"] { padding-left: .3rem !important; padding-right: .3rem !important; }
        [data-testid="stSidebar"] .rail-group-label, [data-testid="stSidebar"] .rail-footer { display: none; }
        [data-testid="stSidebar"] .st-key-rail_cta .stButton button,
        [data-testid="stSidebar"] .st-key-nav_area .stButton button {
            width: 40px !important; padding-left: 0 !important; justify-content: center !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

with st.sidebar:
    with st.container(key="rail_header"):
        col_brand, col_toggle = st.columns([5, 1])
        with col_brand:
            st.markdown(
                f'<div class="rail-brand"><span class="rail-brand-mark"></span>'
                f'<span class="rail-brand-text">{"Residência Med" if expandida else ""}</span></div>',
                unsafe_allow_html=True,
            )
        with col_toggle:
            with st.container(key="rail_toggle"):
                icone_toggle = "left_panel_close" if expandida else "left_panel_open"
                if st.button("", icon=f":material/{icone_toggle}:", key="btn_rail_toggle",
                             help="Recolher menu" if expandida else "Expandir menu"):
                    st.session_state["rail_expandida"] = not expandida
                    st.rerun()

    with st.container(key="rail_cta"):
        if st.button(
            "Praticar agora" if expandida else "", icon=":material/arrow_forward:",
            key="cta_praticar", type="primary", use_container_width=True,
            help=None if expandida else "Praticar agora",
        ):
            st.session_state["pagina_atual"] = "praticar"
            st.rerun()

    st.markdown("---")

    grupos_ordem = []
    grupos = {}
    for grupo, label, icone, key in PAGINAS_NAV:
        if grupo not in grupos:
            grupos_ordem.append(grupo)
            grupos[grupo] = []
        grupos[grupo].append((label, icone, key))

    with st.container(key="nav_area"):
        for i, grupo in enumerate(grupos_ordem):
            if expandida:
                st.markdown(f'<div class="rail-group-label">{grupo}</div>', unsafe_allow_html=True)
            elif i > 0:
                st.markdown("---")
            for label, icone, key in grupos[grupo]:
                ativo = st.session_state["pagina_atual"] == key
                if st.button(
                    label if expandida else "", icon=f":material/{icone}:",
                    key=f"nav_{key}", type="primary" if ativo else "secondary",
                    use_container_width=True, help=None if expandida else label,
                ):
                    st.session_state["pagina_atual"] = key
                    st.rerun()

    pagina_atual = st.session_state["pagina_atual"]

    if expandida:
        n_questoes, n_materiais = _contadores_rail()
        st.markdown(
            f'<div class="rail-footer">{n_questoes} questões · {n_materiais} materiais</div>',
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Barra superior — contexto, busca, ofensiva, contagem regressiva, tema, avatar
# ---------------------------------------------------------------------------
with st.container(key="topbar"):
    col_titulo, col_busca, col_streak, col_prova, col_tema, col_avatar = st.columns(
        [2, 3, 1.1, 1.7, 0.5, 0.5]
    )
    with col_titulo:
        st.markdown(f'<div class="topbar-title">{LABEL_POR_KEY[pagina_atual]}</div>', unsafe_allow_html=True)
    with col_busca:
        st.text_input(
            "busca", placeholder="Buscar no Banco de Questões...",
            label_visibility="collapsed", key="busca_global",
        )
    with col_streak:
        streak, respondeu_hoje = _ofensiva_cache(usuario_id)
        cor_pill = "pill-correct" if respondeu_hoje else "pill-warn"
        st.markdown(
            f'<div class="pill {cor_pill}">{ui.icon_svg("flame", size=13)} '
            f'{streak} dia{"s" if streak != 1 else ""}</div>',
            unsafe_allow_html=True,
        )
    with col_prova:
        data_alvo = st.session_state.get("data_prova_alvo")
        if data_alvo:
            dias_restantes = (datetime.date.fromisoformat(data_alvo) - datetime.date.today()).days
            if dias_restantes >= 0:
                texto_prova = f"prova em {dias_restantes} dia{'s' if dias_restantes != 1 else ''}"
            else:
                texto_prova = "data da prova já passou"
        else:
            texto_prova = "prova alvo não definida"
        st.markdown(
            f'<div class="pill pill-neutral">{ui.icon_svg("calendar", size=13)} {texto_prova}</div>',
            unsafe_allow_html=True,
        )
    with col_tema:
        with st.container(key="theme_toggle"):
            icone_tema = "dark_mode" if st.session_state["tema"] == "light" else "light_mode"
            if st.button("", icon=f":material/{icone_tema}:", key="btn_tema", help="Alternar tema"):
                st.session_state["tema"] = "dark" if st.session_state["tema"] == "light" else "light"
                db.atualizar_tema_usuario(usuario_id, st.session_state["tema"])
                st.rerun()
    with col_avatar:
        email_usuario = st.session_state.get("usuario_email", "")
        iniciais = "".join(p[0] for p in email_usuario.replace("@", " ").split()[:1])[:2].upper() or "?"
        with st.popover(iniciais, key="avatar_popover"):
            st.markdown(
                f'<div style="font-size:0.85rem; margin-bottom:0.75rem; word-break:break-all;">{email_usuario}</div>',
                unsafe_allow_html=True,
            )
            valor_atual = datetime.date.fromisoformat(data_alvo) if data_alvo else None
            nova_data = st.date_input("Prova alvo", value=valor_atual, key="input_prova_alvo")
            col_salvar, col_limpar = st.columns(2)
            if col_salvar.button("Salvar", key="salvar_prova_alvo", use_container_width=True):
                db.definir_prova_alvo(usuario_id, nova_data.isoformat() if nova_data else None)
                st.session_state["data_prova_alvo"] = nova_data.isoformat() if nova_data else None
                st.rerun()
            if col_limpar.button("Limpar", key="limpar_prova_alvo", use_container_width=True):
                db.definir_prova_alvo(usuario_id, None)
                st.session_state["data_prova_alvo"] = None
                st.rerun()
            st.markdown("---")
            if st.button("Sair da conta", icon=":material/logout:", use_container_width=True, key="sair_avatar"):
                for chave in ("usuario_id", "usuario_email", "tema", "data_prova_alvo"):
                    st.session_state.pop(chave, None)
                st.rerun()


@st.cache_data(ttl=60)
def mapa_areas():
    return {a["nome"]: a["id"] for a in db.listar_areas()}


@st.cache_data(ttl=60)
def _listar_bancas_cache():
    return db.listar_bancas()


@st.cache_data(ttl=300)
def _listar_anos_cache():
    return db.listar_anos()


# TTL curto: o Painel muda a cada resposta, mas não precisa refletir isso em
# tempo real — cachear elimina os vários round-trips sequenciais ao Postgres
# que rodariam a cada clique em QUALQUER lugar do app (Streamlit reroda o
# script inteiro a cada interação).
@st.cache_data(ttl=15)
def _dash_combinado(uid):
    return db.desempenho_dashboard_combinado(usuario_id=uid)


@st.cache_data(ttl=15)
def _dash_evolucao_diaria(uid):
    return db.evolucao_diaria(usuario_id=uid)


def controle_paginacao(chave, total, por_pagina=50):
    """Widget de paginação reutilizável. Guarda a página atual em
    st.session_state[chave] e devolve (pagina_atual, offset)."""
    total_paginas = max(1, -(-total // por_pagina))
    if chave not in st.session_state:
        st.session_state[chave] = 0
    st.session_state[chave] = min(st.session_state[chave], total_paginas - 1)
    st.session_state[chave] = max(st.session_state[chave], 0)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("Anterior", key=f"{chave}_prev", icon=":material/arrow_back:", disabled=st.session_state[chave] <= 0):
            st.session_state[chave] -= 1
            st.rerun()
    with col2:
        st.markdown(
            f"<div style='text-align:center; color:var(--ink-500); font-size:0.85rem;'>Página "
            f"{st.session_state[chave] + 1} de {total_paginas} — {total} resultado(s)</div>",
            unsafe_allow_html=True,
        )
    with col3:
        if st.button("Próxima", key=f"{chave}_next", icon=":material/arrow_forward:", disabled=st.session_state[chave] >= total_paginas - 1):
            st.session_state[chave] += 1
            st.rerun()

    pagina_atual_pg = st.session_state[chave]
    return pagina_atual_pg, pagina_atual_pg * por_pagina


def resetar_paginacao_se_filtro_mudou(chave, assinatura_filtro):
    chave_assinatura = f"{chave}_assinatura"
    if st.session_state.get(chave_assinatura) != assinatura_filtro:
        st.session_state[chave_assinatura] = assinatura_filtro
        st.session_state[chave] = 0


def _formatar_tamanho(tamanho_bytes):
    if not tamanho_bytes:
        return "—"
    tamanho_bytes = float(tamanho_bytes)
    for unidade in ["B", "KB", "MB", "GB"]:
        if tamanho_bytes < 1024:
            return f"{tamanho_bytes:.0f} {unidade}" if unidade == "B" else f"{tamanho_bytes:.1f} {unidade}"
        tamanho_bytes /= 1024
    return f"{tamanho_bytes:.1f} TB"


def _form_questao(q, *, key_prefix):
    """Formulário de criar/editar questão, compartilhado entre 'Nova
    Questão' e o dialog de edição do Banco de Questões. `q=None` cria; `q`
    preenchido edita. Devolve 'salvo', 'cancelado' ou None."""
    areas_form = mapa_areas()
    if not areas_form:
        ui.empty_state("Cadastre uma área antes de criar questões.")
        return None

    nomes_area = list(areas_form.keys())
    area_atual_nome = next((n for n, i in areas_form.items() if i == q["area_id"]), None) if q else None
    col_area, col_sub = st.columns(2)
    area_nome_f = col_area.selectbox(
        "Área", nomes_area,
        index=nomes_area.index(area_atual_nome) if area_atual_nome in nomes_area else 0,
        key=f"{key_prefix}_area",
    )
    area_id_f = areas_form[area_nome_f]

    subtopicos_f = db.listar_subtopicos(area_id_f)
    sub_opcoes_f = {"(nenhum)": None}
    sub_opcoes_f.update({s["nome"]: s["id"] for s in subtopicos_f})
    nomes_sub = list(sub_opcoes_f.keys())
    sub_atual_nome = next((n for n, i in sub_opcoes_f.items() if i == q["subtopico_id"]), "(nenhum)") if q else "(nenhum)"
    sub_nome_f = col_sub.selectbox(
        "Subtópico", nomes_sub,
        index=nomes_sub.index(sub_atual_nome) if sub_atual_nome in nomes_sub else 0,
        key=f"{key_prefix}_sub",
    )
    subtopico_id_f = sub_opcoes_f[sub_nome_f]

    enunciado_f = st.text_area("Enunciado da questão", value=q["enunciado"] if q else "", key=f"{key_prefix}_enun")

    ui.form_section_label("Imagem da questão (opcional)")
    imagem_atual = q["imagem"] if q else None
    if imagem_atual:
        st.image(bytes(imagem_atual), width=300)
        if st.button("Remover imagem", icon=":material/delete:", key=f"{key_prefix}_rmimg"):
            db.remover_imagem_questao(q["id"])
            st.rerun()
    nova_imagem = st.file_uploader(
        "Substituir imagem" if imagem_atual else "Anexar imagem (raio-X, ECG, gráfico, foto clínica etc.)",
        type=["png", "jpg", "jpeg"], key=f"{key_prefix}_img",
    )
    if nova_imagem is not None and q is not None:
        db.definir_imagem_questao(q["id"], nova_imagem.getvalue(), nova_imagem.type)
        st.success("Imagem salva.", icon=":material/check_circle:")
        st.rerun()

    ui.form_section_label("Alternativas")
    letras = ["A", "B", "C", "D", "E"]
    alternativas_atuais = {}
    if q is not None:
        alternativas_atuais = q["alternativas"]
        if isinstance(alternativas_atuais, str):
            alternativas_atuais = json.loads(alternativas_atuais)
    valores_alt = {letra: alternativas_atuais.get(letra, "") for letra in letras}
    col_a, col_b = st.columns(2)
    valores_alt["A"] = col_a.text_input("A)", value=valores_alt["A"], key=f"{key_prefix}_alt_a")
    valores_alt["B"] = col_b.text_input("B)", value=valores_alt["B"], key=f"{key_prefix}_alt_b")
    col_c, col_d = st.columns(2)
    valores_alt["C"] = col_c.text_input("C)", value=valores_alt["C"], key=f"{key_prefix}_alt_c")
    valores_alt["D"] = col_d.text_input("D)", value=valores_alt["D"], key=f"{key_prefix}_alt_d")
    valores_alt["E"] = st.text_input("E) (opcional)", value=valores_alt["E"], key=f"{key_prefix}_alt_e")

    col_correta, col_banca, col_ano = st.columns([1, 2, 1])
    correta_atual = q["resposta_correta"] if q and q["resposta_correta"] in letras else "A"
    resposta_correta_f = col_correta.selectbox(
        "Alternativa correta", letras, index=letras.index(correta_atual), key=f"{key_prefix}_correta",
    )
    banca_f = col_banca.text_input(
        "Banca / Instituição (ex: ENAMED, USP-SP, UNIFESP)",
        value=(q["banca"] if q else "") or "", key=f"{key_prefix}_banca",
    )
    ano_f = col_ano.number_input(
        "Ano", min_value=1990, max_value=2100,
        value=(q["ano"] if q else None) or 2025, step=1, key=f"{key_prefix}_ano",
    )

    explicacao_f = st.text_area(
        "Explicação / comentário (opcional)",
        value=(q["explicacao"] if q else "") or "", key=f"{key_prefix}_exp",
    )

    if q is not None:
        col_salvar, col_cancelar = st.columns(2)
    else:
        col_salvar, col_cancelar = st.container(), None

    label_botao = "Salvar alterações" if q is not None else "Salvar questão"
    if col_salvar.button(label_botao, icon=":material/save:", type="primary", key=f"{key_prefix}_salvar"):
        nova_alternativas = {l: valores_alt[l] for l in letras if valores_alt[l].strip()}
        if not enunciado_f.strip() or not all(valores_alt[l].strip() for l in ["A", "B", "C", "D"]):
            st.error("Preencha ao menos o enunciado e as alternativas A a D.", icon=":material/cancel:")
        else:
            if q is not None:
                db.atualizar_questao(
                    q["id"], area_id_f, subtopico_id_f, enunciado_f, nova_alternativas,
                    resposta_correta_f, explicacao_f, banca_f, int(ano_f),
                )
                st.success("Questão atualizada.", icon=":material/check_circle:")
            else:
                novo_id = db.criar_questao(
                    area_id_f, subtopico_id_f, enunciado_f, nova_alternativas,
                    resposta_correta_f, explicacao_f, banca_f, int(ano_f),
                )
                if nova_imagem is not None:
                    db.definir_imagem_questao(novo_id, nova_imagem.getvalue(), nova_imagem.type)
                st.success("Questão cadastrada com sucesso!", icon=":material/check_circle:")
            return "salvo"

    if col_cancelar is not None and col_cancelar.button("Cancelar", icon=":material/close:", key=f"{key_prefix}_cancelar"):
        return "cancelado"

    return None


@st.dialog("Editar questão", width="large")
def _dialog_editar_questao(q):
    resultado = _form_questao(q, key_prefix=f"editq_{q['id']}")
    if resultado in ("salvo", "cancelado"):
        st.rerun()


@st.dialog("Finalizar simulado")
def _dialog_finalizar_simulado(simulado_id_dlg, em_branco):
    if em_branco:
        st.write(f"**{em_branco}** questão(ões) ficarão em branco. Essa ação não pode ser desfeita.")
    else:
        st.write("Todas as questões foram respondidas. Confirmar o encerramento?")
    col1, col2 = st.columns(2)
    if col1.button("Cancelar", use_container_width=True):
        st.rerun()
    if col2.button("Finalizar", type="primary", use_container_width=True):
        db.finalizar_simulado(simulado_id_dlg, usuario_id=usuario_id)
        consolidar_simulado_no_historico(simulado_id_dlg, usuario_id)
        st.rerun()


def consolidar_simulado_no_historico(simulado_id, uid):
    """Joga as respostas do simulado nos mesmos caminhos usados por
    'Praticar' (db.registrar_resposta + sr.registrar_revisao), para que o
    Painel e a fila de repetição espaçada considerem o simulado
    automaticamente. Chamar uma única vez, ao finalizar."""
    for item in db.listar_itens_simulado(simulado_id, usuario_id=uid):
        if item["resposta_dada"] is None:
            continue
        correta = bool(item["correta"])
        db.registrar_resposta(item["id"], item["resposta_dada"], correta, usuario_id=uid)
        sr.registrar_revisao(item["id"], 5 if correta else 1, usuario_id=uid)


def _render_resumo_pratica(uid):
    respondidas = st.session_state.get("prat_respondidas", [])
    inicio = datetime.datetime.fromisoformat(st.session_state["prat_inicio"])
    duracao_seg = (datetime.datetime.now() - inicio).total_seconds()
    n = len(respondidas)
    acertos = sum(1 for r in respondidas if r["correta"])
    erros_ids = [r["id"] for r in respondidas if not r["correta"]]
    tempo_medio = duracao_seg / n if n else 0

    ui.page_title("Resumo da sessão")
    col1, col2, col3 = st.columns(3)
    col1.metric("Acertos", f"{acertos}/{n}" if n else "0/0")
    col2.metric("% de acerto", f"{round(100 * acertos / n, 1)}%" if n else "—")
    col3.metric("Tempo médio por questão", f"{int(tempo_medio)}s" if n else "—")

    if respondidas:
        df_r = pd.DataFrame(respondidas)
        df_r["subtopico"] = df_r["subtopico"].fillna("(sem assunto)")
        resumo_sub = df_r.groupby("subtopico").agg(
            total=("correta", "count"), acertos=("correta", "sum"),
        ).reset_index()
        resumo_sub["pct_acerto"] = round(100 * resumo_sub["acertos"] / resumo_sub["total"], 1)
        st.markdown('<div class="form-section-label">Desempenho por assunto</div>', unsafe_allow_html=True)
        ui.faixa_row([
            {
                "label": r["subtopico"],
                "valor": f"{r['pct_acerto']}% ({int(r['acertos'])}/{int(r['total'])})",
                "cor": ui.cor_semantica_pct(r["pct_acerto"]),
            }
            for _, r in resumo_sub.iterrows()
        ])

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    col_erros, col_nova = st.columns(2)
    with col_erros:
        if erros_ids and st.button(
            f"Adicionar os {len(erros_ids)} erros à revisão espaçada",
            icon=":material/psychology:", key="add_erros_revisao", use_container_width=True,
        ):
            for eid in erros_ids:
                sr.registrar_revisao(eid, 1, usuario_id=uid)
            st.toast("Erros adicionados à revisão espaçada.", icon=":material/check_circle:")
    with col_nova:
        if st.button("Nova sessão", type="primary", icon=":material/refresh:", key="prat_nova_sessao", use_container_width=True):
            for chave in ("prat_fila", "prat_idx", "prat_respondidas", "prat_inicio", "prat_aguardando"):
                st.session_state.pop(chave, None)
            st.rerun()


# ---------------------------------------------------------------------------
# PAINEL
# ---------------------------------------------------------------------------
if pagina_atual == "painel":
    dash = _dash_combinado(usuario_id)
    desemp_area = dash["por_area"]

    if not desemp_area:
        ui.empty_state(
            "Ainda não há respostas registradas para montar seu diagnóstico.",
            cta_label="Ir para Praticar", cta_icon=":material/arrow_forward:", cta_pagina="praticar",
        )
    else:
        df_area = pd.DataFrame([dict(r) for r in desemp_area])
        total_resp = int(df_area["total"].sum())
        total_acertos = int(df_area["acertos"].sum())
        pct_geral = round(100 * total_acertos / total_resp, 1) if total_resp else 0
        pct_fmt = f"{pct_geral:.1f}".replace(".", ",")

        if total_resp < 50:
            frase = (
                f"Volume ainda baixo para conclusões. Responda "
                f"{50 - total_resp} questões para o diagnóstico ficar confiável."
            )
        else:
            pior = df_area.sort_values("pct_acerto").iloc[0]
            frase = f"{total_acertos} acertos em {total_resp} questões. {pior['area']} é a sua maior lacuna."

        evol = _dash_evolucao_diaria(usuario_id)
        ultimos14 = evol[-14:] if evol else []

        feitas_hoje = db.contar_respondidas_hoje(usuario_id=usuario_id)
        META_DIARIA = 20
        pct_meta = round(100 * min(feitas_hoje, META_DIARIA) / META_DIARIA)

        with st.container(key="diag_panel"):
            col1, col2, col3 = st.columns([0.40, 0.35, 0.25])
            with col1:
                st.markdown(
                    f'<div class="diag-display">{pct_fmt}%</div><div class="diag-frase">{frase}</div>',
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown('<div class="diag-caption">Últimos 14 dias</div>', unsafe_allow_html=True)
                if len(ultimos14) >= 3:
                    valores = [r["pct_acerto"] for r in ultimos14]
                    ultimo_pct = f"{valores[-1]:.1f}".replace(".", ",")
                    st.markdown(
                        f'<div class="spark-wrap">{ui.sparkline_svg(valores)}'
                        f'<span class="spark-value">{ultimo_pct}%</span></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div class="diag-sub">Histórico começa a aparecer no terceiro dia de estudo.</div>',
                        unsafe_allow_html=True,
                    )
            with col3:
                st.markdown(
                    f'<div class="diag-f3-wrap">{ui.anel_progresso(pct_meta, f"{feitas_hoje}/{META_DIARIA}")}'
                    f'<div class="diag-sub">Meta do dia</div></div>',
                    unsafe_allow_html=True,
                )
                if st.button("Continuar de onde parei", key="diag_continuar", use_container_width=True):
                    st.session_state["_forcar_pagina"] = "praticar"
                    st.rerun()

        st.markdown(
            '<div style="font-weight:600;color:var(--ink-700);font-size:15px;margin-bottom:0.6rem;">'
            'Onde você está errando</div>',
            unsafe_allow_html=True,
        )
        suficientes = df_area[df_area["total"] >= 5].sort_values("pct_acerto")
        insuficientes = df_area[df_area["total"] < 5]

        linhas = [
            {
                "area_id": int(r["area_id"]), "nome": r["area"], "pct": r["pct_acerto"],
                "acertos": r["acertos"], "total": r["total"],
            }
            for _, r in suficientes.iterrows()
        ]
        if linhas:
            area_clicada = ui.lista_erro_barra(linhas, key_prefix="err")
            if area_clicada:
                st.session_state["pratica_area_forcada"] = area_clicada
                st.session_state["_forcar_pagina"] = "praticar"
                st.rerun()
        else:
            ui.empty_state("Nenhuma área com volume suficiente ainda.")

        if len(insuficientes):
            with st.expander(f"Amostra insuficiente ({len(insuficientes)})", icon=":material/info:"):
                st.caption("Menos de 5 questões respondidas — percentual ainda não é confiável.")
                for _, r in insuficientes.iterrows():
                    st.markdown(
                        f'<div class="err-amostra">{r["area"]} — {r["pct_acerto"]}% '
                        f'({int(r["acertos"])}/{int(r["total"])})</div>',
                        unsafe_allow_html=True,
                    )

        st.markdown("<div style='height:1.4rem;'></div>", unsafe_allow_html=True)
        st.markdown(
            '<div style="font-weight:600;color:var(--ink-700);font-size:15px;margin-bottom:0.6rem;">'
            'Revisões de hoje</div>',
            unsafe_allow_html=True,
        )
        pendentes_hoje = sr.questoes_para_revisar_hoje(usuario_id=usuario_id)
        if not pendentes_hoje:
            ui.empty_state("Nenhuma revisão vencida hoje.")
        else:
            with st.container(border=True):
                st.write(f"{len(pendentes_hoje)} questõe(s) esperando revisão.")
                if st.button(
                    f"Revisar {len(pendentes_hoje)} itens", key="ir_revisar",
                    icon=":material/arrow_forward:", type="primary",
                ):
                    st.session_state["_forcar_pagina"] = "revisao"
                    st.rerun()

# ---------------------------------------------------------------------------
# PRATICAR
# ---------------------------------------------------------------------------
elif pagina_atual == "praticar":
    sessao_ativa = bool(st.session_state.get("prat_fila"))

    if not sessao_ativa:
        ui.page_title("Praticar")
        areas = mapa_areas()
        if not areas:
            ui.empty_state(
                "Cadastre uma área antes de responder questões.",
                cta_label="Ir para Nova questão", cta_icon=":material/arrow_forward:", cta_pagina="nova_questao",
            )
        else:
            nomes_area = ["Todas"] + list(areas.keys())
            area_forcada_id = st.session_state.pop("pratica_area_forcada", None)
            index_area_default = 0
            if area_forcada_id:
                nome_forcado = next((n for n, i in areas.items() if i == area_forcada_id), None)
                if nome_forcado:
                    index_area_default = nomes_area.index(nome_forcado)

            col1, col2 = st.columns(2)
            area_nome = col1.selectbox("Área (opcional)", nomes_area, index=index_area_default, key="prat_cfg_area")
            area_id = areas[area_nome] if area_nome != "Todas" else None

            sub_opcoes = {"Todos": None}
            if area_id:
                sub_opcoes.update({s["nome"]: s["id"] for s in db.listar_subtopicos(area_id)})
            sub_nome = col2.selectbox("Assunto (opcional)", list(sub_opcoes.keys()), key="prat_cfg_sub")
            subtopico_id = sub_opcoes[sub_nome]

            col3, col4 = st.columns(2)
            bancas_disp = _listar_bancas_cache()
            banca = None
            with col3:
                if bancas_disp:
                    banca_sel = st.selectbox("Banca (opcional)", ["Todas"] + bancas_disp, key="prat_cfg_banca")
                    banca = None if banca_sel == "Todas" else banca_sel
                else:
                    st.selectbox("Banca (opcional)", ["Todas"], key="prat_cfg_banca_vazio", disabled=True)
            anos_disp = _listar_anos_cache()
            ano = None
            with col4:
                if anos_disp:
                    ano_sel = st.selectbox("Ano (opcional)", ["Todos"] + anos_disp, key="prat_cfg_ano")
                    ano = None if ano_sel == "Todos" else ano_sel
                else:
                    st.selectbox("Ano (opcional)", ["Todos"], key="prat_cfg_ano_vazio", disabled=True)

            col5, col6 = st.columns(2)
            quantidade = col5.selectbox("Quantidade de questões", [10, 20, 30, 50], key="prat_cfg_qtd")
            with col6:
                apenas_erros = st.checkbox("Apenas questões que errei", key="prat_cfg_erros")
                excluir_respondidas = st.checkbox("Excluir questões já respondidas", key="prat_cfg_excl")

            filtros_ativos = []
            if area_nome != "Todas":
                filtros_ativos.append(area_nome)
            if sub_nome != "Todos":
                filtros_ativos.append(sub_nome)
            if banca:
                filtros_ativos.append(banca)
            if ano:
                filtros_ativos.append(str(ano))
            if apenas_erros:
                filtros_ativos.append("Apenas erros")
            if excluir_respondidas:
                filtros_ativos.append("Excluir respondidas")
            ui.chips(filtros_ativos)

            if st.button(
                f"Iniciar sessão de {quantidade} questões", type="primary",
                icon=":material/play_arrow:", key="prat_iniciar",
            ):
                ids = db.ids_questoes_filtro_pratica(
                    usuario_id=usuario_id, area_id=area_id, subtopico_id=subtopico_id,
                    banca=banca, ano=ano, apenas_erros=apenas_erros,
                    excluir_respondidas=excluir_respondidas,
                )
                random.shuffle(ids)
                ids = ids[:quantidade]
                if not ids:
                    st.error("Nenhuma questão encontrada para esses filtros.", icon=":material/cancel:")
                else:
                    st.session_state["prat_fila"] = ids
                    st.session_state["prat_idx"] = 0
                    st.session_state["prat_respondidas"] = []
                    st.session_state["prat_inicio"] = datetime.datetime.now().isoformat()
                    st.session_state.pop("prat_aguardando", None)
                    st.rerun()
    else:
        fila = st.session_state["prat_fila"]
        idx = st.session_state["prat_idx"]

        if idx >= len(fila):
            _render_resumo_pratica(usuario_id)
        else:
            q = db.obter_questao(fila[idx])
            aguardando = st.session_state.get("prat_aguardando")

            col_prog, col_flag, col_fim = st.columns([5, 0.6, 0.6])
            with col_prog:
                st.progress(idx / len(fila))
                st.caption(f"{idx + 1} de {len(fila)}")
            with col_flag:
                marcada = db.questao_esta_marcada(usuario_id, q["id"])
                if st.button(
                    "", icon=":material/flag:", key=f"marcar_{q['id']}_{idx}",
                    type="primary" if marcada else "secondary",
                    help="Desmarcar" if marcada else "Marcar para revisão",
                    use_container_width=True,
                ):
                    if marcada:
                        db.desmarcar_questao(usuario_id, q["id"])
                    else:
                        db.marcar_questao(usuario_id, q["id"])
                    st.rerun()
            with col_fim:
                if st.button(
                    "", icon=":material/stop_circle:", key="encerrar_sessao",
                    help="Encerrar sessão", use_container_width=True,
                ):
                    st.session_state["prat_idx"] = len(fila)
                    st.session_state.pop("prat_aguardando", None)
                    st.rerun()

            ui.render_cabecalho_questao(q)

            if aguardando is None:
                escolha = ui.render_alternativas_interativas(q, key=f"prat_resp_{q['id']}_{idx}")
                if st.button(
                    "Confirmar resposta", type="primary", icon=":material/check:",
                    disabled=escolha is None, key=f"prat_conf_{q['id']}_{idx}",
                ):
                    correta = escolha == q["resposta_correta"]
                    st.session_state["prat_aguardando"] = {"resposta": escolha, "correta": correta}
                    st.rerun()
            else:
                escolha = aguardando["resposta"]
                correta = aguardando["correta"]
                distribuicao = db.distribuicao_respostas_questao(q["id"], excluir_usuario_id=usuario_id)
                ui.render_alternativas_resultado(q, resposta_selecionada=escolha, distribuicao=distribuicao)

                if q["explicacao"]:
                    with st.expander("Comentário", expanded=True, icon=":material/lightbulb:"):
                        st.write(q["explicacao"])

                def _concluir_pratica(qualidade, confianca=None):
                    db.registrar_resposta(q["id"], escolha, correta, usuario_id=usuario_id, confianca=confianca)
                    sr.registrar_revisao(q["id"], qualidade, usuario_id=usuario_id)
                    st.session_state["prat_respondidas"].append({
                        "id": q["id"], "correta": correta,
                        "subtopico": q["subtopico"] if "subtopico" in q.keys() else None,
                    })
                    st.session_state.pop("prat_aguardando", None)
                    st.session_state["prat_idx"] += 1
                    st.rerun()

                if correta:
                    st.success("Correto!", icon=":material/check_circle:")
                    st.markdown('<div class="form-section-label">Como você chegou nessa resposta?</div>', unsafe_allow_html=True)
                    col_seg, col_chute = st.columns(2)
                    with col_seg:
                        if st.button("Acertei com segurança", key=f"seg_{q['id']}_{idx}", type="primary", use_container_width=True):
                            _concluir_pratica(5, confianca="seguro")
                    with col_chute:
                        if st.button("Acertei no chute", key=f"chute_{q['id']}_{idx}", use_container_width=True):
                            _concluir_pratica(3, confianca="chute")
                else:
                    st.error(f"Errado. A resposta correta é {q['resposta_correta']}.", icon=":material/cancel:")
                    if st.button("Continuar", key=f"cont_{q['id']}_{idx}", type="primary", icon=":material/arrow_forward:"):
                        _concluir_pratica(1)

# ---------------------------------------------------------------------------
# SIMULADO
# ---------------------------------------------------------------------------
elif pagina_atual == "simulado":
    simulado_id = st.session_state.get("simulado_id")

    if simulado_id is None:
        ui.page_title(
            "Simulado",
            "Monte uma prova no formato das provas de residência: número de questões, "
            "tempo limite e sem correção até o final.",
        )
        areas = mapa_areas()
        col1, col2 = st.columns(2)
        with col1:
            area_nome = st.selectbox("Área (opcional)", ["Todas"] + list(areas.keys()), key="sim_area")
            area_id = areas[area_nome] if area_nome != "Todas" else None
        with col2:
            bancas = _listar_bancas_cache()
            if bancas:
                banca = st.selectbox("Banca (opcional)", ["Todas"] + bancas, key="sim_banca")
                banca = None if banca == "Todas" else banca
            else:
                banca = None

        col3, col4 = st.columns(2)
        with col3:
            preset = st.selectbox("Número de questões", [10, 20, 30, 50, "Personalizado"], key="sim_preset")
            if preset == "Personalizado":
                num_questoes = st.number_input(
                    "Quantas questões?", min_value=1, max_value=200, value=15, step=1, key="sim_num_custom",
                )
            else:
                num_questoes = preset
        with col4:
            if st.session_state.get("sim_num_questoes_anterior") != num_questoes:
                st.session_state["sim_num_questoes_anterior"] = num_questoes
                st.session_state["sim_tempo"] = max(5, round(num_questoes * 1.5))
            tempo_limite_min = st.number_input(
                "Tempo limite (minutos)", min_value=1, max_value=600, step=1, key="sim_tempo",
            )

        disponiveis = db.contar_questoes_disponiveis(area_id, banca)
        if disponiveis < num_questoes:
            st.warning(
                f"Só há {disponiveis} questão(ões) disponível(is) para esse filtro "
                f"(pediu {num_questoes}). Ajuste os filtros ou a quantidade.",
                icon=":material/warning:",
            )

        if st.button(
            "Iniciar simulado", type="primary", icon=":material/play_arrow:",
            disabled=disponiveis == 0 or disponiveis < num_questoes,
        ):
            questoes = db.questoes_aleatorias(area_id, banca, limite=num_questoes)
            ids = [q["id"] for q in questoes]
            novo_id = db.criar_simulado(
                area_id, banca, len(ids), int(tempo_limite_min), ids, usuario_id=usuario_id,
            )
            st.session_state.simulado_id = novo_id
            st.session_state.simulado_questoes = ids
            st.session_state.simulado_idx = 0
            st.rerun()

        with st.expander("Histórico de simulados", icon=":material/history:"):
            historico = db.listar_simulados(10, usuario_id=usuario_id)
            if not historico:
                st.caption("Nenhum simulado concluído ainda.")
            else:
                df_hist = pd.DataFrame([dict(h) for h in historico])
                df_hist["area"] = df_hist["area"].fillna("Todas")
                st.dataframe(
                    df_hist[["finalizado_em", "area", "banca", "num_questoes", "acertos", "pct_acerto"]],
                    hide_index=True, row_height=40,
                )

    else:
        simulado = db.obter_simulado(simulado_id, usuario_id=usuario_id)
        if simulado is None:
            for chave in ("simulado_id", "simulado_questoes", "simulado_idx"):
                st.session_state.pop(chave, None)
            st.warning("Simulado não encontrado.")
            st.rerun()

        if simulado["finalizado_em"] is not None:
            acertos = simulado["acertos"] or 0
            total = simulado["num_questoes"]
            pct = round(100 * acertos / total, 1) if total else 0

            ui.page_title("Resultado do simulado")
            ui.faixa_row([
                {"label": "Acertos", "valor": f"{acertos}/{total}"},
                {"label": "% de acerto", "valor": f"{pct}%", "cor": ui.cor_semantica_pct(pct)},
                {"label": "Respondidas", "valor": str(simulado["total_respondidas"] or 0)},
            ])

            desemp = db.desempenho_simulado(simulado_id, usuario_id=usuario_id)
            if desemp:
                st.markdown('<div class="form-section-label">Desempenho por área (neste simulado)</div>', unsafe_allow_html=True)
                df_desemp = pd.DataFrame([dict(r) for r in desemp])
                ui.grafico_barras_horizontais(df_desemp, "area", "pct_acerto")

            st.markdown('<div class="form-section-label">Revisão completa</div>', unsafe_allow_html=True)
            itens = db.listar_itens_simulado(simulado_id, usuario_id=usuario_id)
            for item in itens:
                if item["resposta_dada"] is None:
                    marcador, icone_item = "não respondida", "radio_button_unchecked"
                elif item["correta"]:
                    marcador, icone_item = "correta", "check_circle"
                else:
                    marcador, icone_item = "errada", "cancel"
                with st.expander(
                    f"[{item['ordem'] + 1}] {marcador} — {item['enunciado'][:80]}...",
                    icon=f":material/{icone_item}:",
                ):
                    ui.render_cabecalho_questao(item)
                    ui.render_alternativas_resultado(item, resposta_selecionada=item["resposta_dada"])
                    if item["explicacao"]:
                        st.info(item["explicacao"], icon=":material/lightbulb:")

            if st.button("Novo simulado", type="primary", icon=":material/add:"):
                for chave in ["simulado_id", "simulado_questoes", "simulado_idx"]:
                    st.session_state.pop(chave, None)
                st.rerun()

        else:
            iniciado_em = datetime.datetime.fromisoformat(simulado["iniciado_em"])
            limite_seg = simulado["tempo_limite_min"] * 60
            decorrido_seg = (datetime.datetime.now() - iniciado_em).total_seconds()
            restante_seg = limite_seg - decorrido_seg

            if restante_seg <= 0:
                db.finalizar_simulado(simulado_id, usuario_id=usuario_id)
                consolidar_simulado_no_historico(simulado_id, usuario_id)
                st.warning("Tempo esgotado! Confira seu resultado abaixo.", icon=":material/schedule:")
                st.rerun()
            else:
                ids = st.session_state.get("simulado_questoes") or [
                    i["id"] for i in db.listar_itens_simulado(simulado_id, usuario_id=usuario_id)
                ]
                idx = st.session_state.get("simulado_idx", 0)
                idx = max(0, min(idx, len(ids) - 1))

                itens = db.listar_itens_simulado(simulado_id, usuario_id=usuario_id)
                respostas_dadas = {i["id"]: i["resposta_dada"] for i in itens}

                minutos, segundos = divmod(int(restante_seg), 60)
                if restante_seg < 60:
                    cor_tempo = "var(--wrong)"
                elif restante_seg < 600:
                    cor_tempo = "var(--warn)"
                else:
                    cor_tempo = "var(--ink-700)"

                col1, col2 = st.columns([1, 3])
                with col1:
                    st.markdown(
                        f'<div class="timer-hero" style="color:{cor_tempo}; border-color:{cor_tempo};">'
                        f'{ui.icon_svg("clock", size=18)} {minutos:02d}:{segundos:02d}</div>',
                        unsafe_allow_html=True,
                    )
                with col2:
                    st.progress((idx + 1) / len(ids))
                    st.caption(f"Questão {idx + 1} de {len(ids)}")

                q = db.obter_questao(ids[idx])
                alternativas_atuais = json.loads(q["alternativas"]) if isinstance(q["alternativas"], str) else q["alternativas"]
                opcoes = list(alternativas_atuais.keys())
                resposta_atual = respostas_dadas.get(q["id"])

                ui.render_cabecalho_questao(q)
                resposta = ui.render_alternativas_interativas(
                    q, key=f"sim_resp_{simulado_id}_{q['id']}",
                    index_pre_selecionado=opcoes.index(resposta_atual) if resposta_atual in opcoes else None,
                )
                if resposta is not None and resposta != resposta_atual:
                    db.registrar_resposta_simulado(simulado_id, q["id"], resposta, usuario_id=usuario_id)
                    respostas_dadas[q["id"]] = resposta

                col_a, col_b, col_c = st.columns([1, 1, 1])
                with col_a:
                    if st.button("Anterior", icon=":material/arrow_back:", disabled=idx <= 0, use_container_width=True):
                        st.session_state.simulado_idx = idx - 1
                        st.rerun()
                with col_c:
                    if st.button("Próxima", icon=":material/arrow_forward:", disabled=idx >= len(ids) - 1, use_container_width=True):
                        st.session_state.simulado_idx = idx + 1
                        st.rerun()

                st.markdown('<div class="form-section-label">Ir para questão</div>', unsafe_allow_html=True)
                with st.container(key="sim_grid"):
                    n_colunas = 10
                    for inicio in range(0, len(ids), n_colunas):
                        cols_grid = st.columns(n_colunas)
                        for offset, col_g in enumerate(cols_grid):
                            i = inicio + offset
                            if i >= len(ids):
                                continue
                            respondida_i = respostas_dadas.get(ids[i]) is not None
                            with col_g:
                                if st.button(
                                    str(i + 1), key=f"simnav_{simulado_id}_{i}",
                                    type="primary" if (i == idx or respondida_i) else "secondary",
                                    help="respondida" if respondida_i else "em branco",
                                ):
                                    st.session_state.simulado_idx = i
                                    st.rerun()

                st.markdown("---")
                em_branco = sum(1 for qid in ids if respostas_dadas.get(qid) is None)
                if st.button("Finalizar simulado", icon=":material/flag:", type="primary"):
                    _dialog_finalizar_simulado(simulado_id, em_branco)

# ---------------------------------------------------------------------------
# REVISÃO ESPAÇADA
# ---------------------------------------------------------------------------
elif pagina_atual == "revisao":
    ui.page_title(
        "Revisão espaçada",
        "Questões que você errou voltam mais rápido; as que domina voltam com intervalos cada vez maiores.",
    )

    if "rev_fila_ids" not in st.session_state:
        pendentes = sr.questoes_para_revisar_hoje(usuario_id=usuario_id)
        novas = sr.questoes_nunca_revisadas(usuario_id=usuario_id)
        marcadas = db.listar_questoes_marcadas(usuario_id=usuario_id)
        ids_ja_incluidos = {q["id"] for q in list(pendentes) + list(novas)}
        marcadas_extra = [q["id"] for q in marcadas if q["id"] not in ids_ja_incluidos]
        st.session_state["rev_fila_ids"] = (
            [q["id"] for q in pendentes] + [q["id"] for q in novas] + marcadas_extra
        )
        st.session_state["rev_idx"] = 0
        st.session_state["rev_revelado"] = False

    if st.button("Recomeçar fila", icon=":material/restart_alt:", key="rev_recomecar"):
        st.session_state.pop("rev_fila_ids", None)
        st.session_state["rev_idx"] = 0
        st.session_state["rev_revelado"] = False
        st.rerun()

    fila_ids = st.session_state["rev_fila_ids"]
    idx_rev = st.session_state["rev_idx"]
    restantes = max(len(fila_ids) - idx_rev, 0)
    st.caption(f"{restantes} ite{'m' if restantes == 1 else 'ns'} restante{'s' if restantes != 1 else ''}")

    if not fila_ids or idx_rev >= len(fila_ids):
        prox = sr.proxima_leva_revisao(usuario_id=usuario_id)
        if prox:
            dia_prox = datetime.date.fromisoformat(prox["dia"])
            nome_dia = _NOME_DIA_SEMANA[dia_prox.weekday()]
            texto_vazio = (
                f"Nenhuma revisão vencida hoje. As próximas {prox['total']} vencem {nome_dia}."
            )
        else:
            texto_vazio = "Nenhuma revisão vencida hoje."
        ui.empty_state(
            texto_vazio, cta_label="Praticar questões novas",
            cta_icon=":material/arrow_forward:", cta_pagina="praticar",
        )
    else:
        q = db.obter_questao(fila_ids[idx_rev])
        _, col_card, _ = st.columns([1, 3, 1])
        with col_card:
            with st.container(border=True):
                ui.render_cabecalho_questao(q)

                if not st.session_state["rev_revelado"]:
                    if st.button(
                        "Mostrar resposta", type="primary", icon=":material/visibility:",
                        use_container_width=True, key=f"rev_mostrar_{q['id']}_{idx_rev}",
                    ):
                        st.session_state["rev_revelado"] = True
                        st.rerun()
                else:
                    ui.render_alternativas_resultado(q)
                    if q["explicacao"]:
                        with st.expander("Comentário", expanded=True, icon=":material/lightbulb:"):
                            st.write(q["explicacao"])

                    st.markdown('<div class="form-section-label">Quão fácil foi lembrar?</div>', unsafe_allow_html=True)
                    opcoes_intervalo = [
                        ("Errei — 10 min", 1), ("Difícil — 1 dia", 3),
                        ("Bom — 4 dias", 4), ("Fácil — 10 dias", 5),
                    ]
                    cols_intervalo = st.columns(4)
                    for col_i, (label, qualidade) in zip(cols_intervalo, opcoes_intervalo):
                        with col_i:
                            if st.button(label, key=f"rev_{qualidade}_{q['id']}_{idx_rev}", use_container_width=True):
                                sr.registrar_revisao(q["id"], qualidade, usuario_id=usuario_id)
                                if qualidade == 1:
                                    # "Errei" volta a aparecer daqui a pouco NESTA sessão (o SM-2
                                    # por trás só agenda em dias inteiros — ver nota no wrap-up).
                                    nova_pos = min(idx_rev + 4, len(fila_ids))
                                    fila_ids.insert(nova_pos, q["id"])
                                elif db.questao_esta_marcada(usuario_id, q["id"]):
                                    db.desmarcar_questao(usuario_id, q["id"])
                                st.session_state["rev_idx"] += 1
                                st.session_state["rev_revelado"] = False
                                st.rerun()

# ---------------------------------------------------------------------------
# MATERIAIS DE ESTUDO
# ---------------------------------------------------------------------------
elif pagina_atual == "materiais":
    ui.page_title("Materiais")

    ultima = db.ultima_sincronizacao()
    if ultima:
        delta = datetime.datetime.now() - datetime.datetime.fromisoformat(ultima)
        if delta.days >= 1:
            texto_sync = f"Sincronizado há {delta.days} dia(s)"
        else:
            horas = int(delta.total_seconds() // 3600)
            texto_sync = f"Sincronizado há {horas}h" if horas else "Sincronizado agora há pouco"
    else:
        texto_sync = "Nunca sincronizado"
    col_sync_txt, col_sync_btn = st.columns([4, 1])
    with col_sync_txt:
        st.markdown(
            f'<div class="pill pill-neutral">{ui.icon_svg("clock", size=13)} {texto_sync}</div>',
            unsafe_allow_html=True,
        )
    with col_sync_btn:
        if st.button("Sincronizar agora", key="ir_sincronizar", use_container_width=True):
            st.session_state["_forcar_pagina"] = "sincronizar"
            st.rerun()

    st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)

    total_mat_atual = db.contar_materiais()
    if total_mat_atual and eh_admin:
        with st.expander("Zona de risco (admin)", icon=":material/warning:"):
            st.write(
                f"Isso apaga permanentemente **{total_mat_atual}** material(is) cadastrados, "
                "para **todos os usuários** da plataforma. Não tem como desfazer."
            )
            confirmar_excluir_todos = st.checkbox(
                f"Sim, quero excluir todos os {total_mat_atual} materiais cadastrados",
                key="confirmar_excluir_todos_materiais",
            )
            if st.button(
                "Excluir todos os materiais", icon=":material/delete_forever:",
                disabled=not confirmar_excluir_todos,
            ):
                db.excluir_todos_materiais()
                st.session_state.pop("confirmar_excluir_todos_materiais", None)
                st.success("Todos os materiais foram excluídos.", icon=":material/check_circle:")
                st.rerun()

    areas = mapa_areas()
    if not areas:
        ui.empty_state(
            "Cadastre uma área antes de adicionar materiais.",
            cta_label="Ir para Nova questão", cta_icon=":material/arrow_forward:", cta_pagina="nova_questao",
        )
    else:
        with st.expander("Adicionar novo material", icon=":material/add_circle:"):
            col_area, col_sub, col_tipo = st.columns(3)
            area_nome = col_area.selectbox("Área", list(areas.keys()), key="mat_area")
            area_id = areas[area_nome]
            subtopicos = db.listar_subtopicos(area_id)
            sub_opcoes = {"(nenhum)": None}
            sub_opcoes.update({s["nome"]: s["id"] for s in subtopicos})
            sub_nome = col_sub.selectbox("Subtópico", list(sub_opcoes.keys()), key="mat_sub")
            subtopico_id = sub_opcoes[sub_nome]

            tipo = col_tipo.selectbox(
                "Tipo de material", ["Apostila", "Videoaula", "Vídeo Bônus", "Vídeo Apostila", "Outro"],
            )
            col_titulo, col_link = st.columns(2)
            titulo = col_titulo.text_input("Título do material")
            link = col_link.text_input("Link do MediaFire")

            if st.button("Salvar material", icon=":material/save:", type="primary"):
                if titulo.strip() and link.strip():
                    db.criar_material(area_id, subtopico_id, tipo, titulo, link)
                    st.success("Material adicionado!", icon=":material/check_circle:")
                    st.rerun()
                else:
                    st.error("Preencha título e link.", icon=":material/cancel:")

        col_arvore, col_conteudo = st.columns([1, 3])
        with col_arvore:
            st.markdown('<div class="form-section-label">Áreas</div>', unsafe_allow_html=True)
            with st.container(height=420, border=True):
                area_sel = st.radio(
                    "Áreas", ["Todas"] + list(areas.keys()), key="mat_arvore_area", label_visibility="collapsed",
                )
            area_id_filtro = areas[area_sel] if area_sel != "Todas" else None

        with col_conteudo:
            col_tipo_f, col_busca_f = st.columns([1, 2])
            tipos_disponiveis = db.listar_tipos_materiais()
            tipo_filtro = col_tipo_f.selectbox("Tipo", ["Todos"] + tipos_disponiveis, key="mat_filtro_tipo")
            tipo_filtro = None if tipo_filtro == "Todos" else tipo_filtro
            busca = col_busca_f.text_input(
                "Buscar por título", key="mat_busca", placeholder="Buscar por título...",
            )

            assinatura = (area_id_filtro, tipo_filtro, busca)
            resetar_paginacao_se_filtro_mudou("mat_pagina", assinatura)
            total = db.contar_materiais_filtrados(area_id_filtro, None, tipo_filtro, busca)

            if total == 0:
                ui.empty_state("Nenhum material encontrado. Ajuste os filtros ou adicione um novo.")
            else:
                POR_PAGINA = 50
                _, offset = controle_paginacao("mat_pagina", total, POR_PAGINA)
                materiais = db.listar_materiais_paginado(
                    area_id_filtro, None, tipo_filtro, busca, limite=POR_PAGINA, offset=offset,
                )
                df_mat = pd.DataFrame([dict(m) for m in materiais])
                df_mat["Tamanho"] = df_mat["tamanho_bytes"].apply(_formatar_tamanho)
                df_mat["Assunto"] = df_mat["subtopico"].fillna("—")
                df_view = df_mat.rename(columns={
                    "id": "ID", "tipo": "Tipo", "titulo": "Título", "link_mediafire": "Abrir",
                })

                evento = st.dataframe(
                    df_view, hide_index=True, row_height=44, on_select="rerun", selection_mode="multi-row",
                    column_order=["Tipo", "Título", "Assunto", "Tamanho", "Abrir"],
                    column_config={"Abrir": st.column_config.LinkColumn("Abrir", display_text="Abrir ↗")},
                    key="mat_tabela",
                )
                linhas_sel = evento.selection.rows if evento is not None else []
                if eh_admin and linhas_sel:
                    ids_sel = df_view.iloc[linhas_sel]["ID"].tolist()
                    if st.button(
                        f"Excluir {len(ids_sel)} selecionado(s)", icon=":material/delete:",
                        key="mat_excluir_sel",
                    ):
                        ui.confirmar_exclusao(
                            f"Excluir **{len(ids_sel)}** material(is) selecionado(s)? "
                            "Eles somem do acervo compartilhado pra todos os usuários. "
                            "Essa ação não pode ser desfeita.",
                            lambda ids=tuple(int(i) for i in ids_sel): [db.excluir_material(i) for i in ids],
                        )

# ---------------------------------------------------------------------------
# SINCRONIZAR MEDIAFIRE
# ---------------------------------------------------------------------------
elif pagina_atual == "sincronizar":
    ui.page_title(
        "Sincronizar MediaFire",
        "Cole o link da sua pasta raiz compartilhada. O app varre automaticamente todas as "
        "subpastas (áreas → assuntos → arquivos) e cadastra tudo como material de estudo.",
    )

    with st.expander("Estrutura esperada da pasta", icon=":material/info:"):
        st.markdown(
            "Pasta raiz → pastas de área (ex: Cardiologia, Cirurgia, Dermatologia) → pastas "
            "de assunto → apostilas/vídeos (ou subpastas extras tipo 'Apostilas'/'Videoaulas' "
            "dentro do assunto, que também são lidas). Funciona apenas com pastas compartilhadas "
            "publicamente (aquelas com link `mediafire.com/folder/...`) e requer conexão com a internet."
        )

    link_raiz = st.text_input(
        "Link (ou chave) da pasta raiz do MediaFire",
        placeholder="https://www.mediafire.com/folder/xxxxxxxxxxxxx/NomeDaPasta",
    )

    if st.button("Sincronizar agora", type="primary", icon=":material/sync:", disabled=not link_raiz.strip()):
        status_area = st.empty()
        log_linhas = []

        def _progresso(msg):
            log_linhas.append(msg)
            status_area.text("\n".join(log_linhas[-8:]))

        try:
            with st.spinner("Varrendo a pasta do MediaFire... isso pode levar alguns minutos."):
                relatorio = mf.sincronizar_pasta_raiz(link_raiz, on_progress=_progresso)
        except mf.MediaFireError as e:
            st.error(f"Erro ao sincronizar: {e}", icon=":material/cancel:")
        else:
            status_area.empty()
            st.success("Sincronização concluída!", icon=":material/check_circle:")
            ui.faixa_row([
                {"label": "Áreas", "valor": str(relatorio["areas_criadas"])},
                {"label": "Assuntos", "valor": str(relatorio["subtopicos_criados"])},
                {"label": "Materiais novos", "valor": str(relatorio["materiais_novos"]), "cor": "var(--correct)"},
                {"label": "Já existiam", "valor": str(relatorio["materiais_duplicados"])},
            ])
            if relatorio["erros"]:
                with st.expander(f"{len(relatorio['erros'])} aviso(s)/erro(s)", icon=":material/warning:"):
                    df_erros_mf = pd.DataFrame({"Aviso": relatorio["erros"]})
                    st.dataframe(df_erros_mf, hide_index=True, row_height=36)
            st.caption(
                "Pode rodar a sincronização de novo sempre que adicionar arquivos novos na pasta "
                "— os que já foram importados não duplicam."
            )

# ---------------------------------------------------------------------------
# BANCO DE QUESTÕES
# ---------------------------------------------------------------------------
elif pagina_atual == "banco":
    ui.page_title("Banco de questões")

    areas = mapa_areas()
    col1, col2 = st.columns(2)
    area_nome = col1.selectbox("Filtrar por área", ["Todas"] + list(areas.keys()), key="bq_area")
    area_id = areas[area_nome] if area_nome != "Todas" else None
    busca = col2.text_input("Buscar no enunciado", key="bq_busca", placeholder="Buscar no enunciado...")

    resetar_paginacao_se_filtro_mudou("bq_pagina", (area_id, busca))
    total = db.contar_questoes_filtradas(area_id=area_id, busca=busca)

    if total == 0:
        ui.empty_state(
            "Nenhuma questão encontrada. Ajuste os filtros ou cadastre uma nova.",
            cta_label="Ir para Nova questão", cta_icon=":material/arrow_forward:", cta_pagina="nova_questao",
        )
    else:
        POR_PAGINA = 50
        _, offset = controle_paginacao("bq_pagina", total, POR_PAGINA)
        questoes = db.listar_questoes_paginado(area_id=area_id, busca=busca, limite=POR_PAGINA, offset=offset)
        df_q = pd.DataFrame([dict(q) for q in questoes])
        df_q["Enunciado"] = df_q["enunciado"].str.slice(0, 90) + "…"
        df_view = df_q.rename(columns={"id": "ID", "banca": "Banca", "ano": "Ano", "area": "Área"})

        evento = st.dataframe(
            df_view, hide_index=True, row_height=44, on_select="rerun", selection_mode="multi-row",
            column_order=["ID", "Banca", "Ano", "Área", "Enunciado"],
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "Ano": st.column_config.NumberColumn("Ano", width="small"),
            },
            key="bq_tabela",
        )
        linhas_sel = evento.selection.rows if evento is not None else []

        if eh_admin and linhas_sel:
            ids_sel = df_view.iloc[linhas_sel]["ID"].tolist()
            col_a, col_b = st.columns(2)
            with col_a:
                if len(ids_sel) == 1 and st.button(
                    "Editar selecionada", icon=":material/edit:", key="bq_editar_sel", use_container_width=True,
                ):
                    _dialog_editar_questao(db.obter_questao(int(ids_sel[0])))
            with col_b:
                if st.button(
                    f"Excluir {len(ids_sel)} selecionada(s)", icon=":material/delete:",
                    key="bq_excluir_sel", use_container_width=True,
                ):
                    ui.confirmar_exclusao(
                        f"Excluir **{len(ids_sel)}** questão(ões)? O histórico de respostas e "
                        "revisões associado a elas deixa de fazer sentido. Essa ação não pode ser desfeita.",
                        lambda ids=tuple(int(i) for i in ids_sel): [db.excluir_questao(i) for i in ids],
                    )

        if len(linhas_sel) == 1:
            qsel = db.obter_questao(int(df_view.iloc[linhas_sel[0]]["ID"]))
            with st.container(border=True):
                ui.render_cabecalho_questao(qsel)
                ui.render_alternativas_resultado(qsel)
                if qsel["explicacao"]:
                    st.info(qsel["explicacao"], icon=":material/lightbulb:")
                else:
                    st.caption("Sem explicação cadastrada ainda.")

# ---------------------------------------------------------------------------
# NOVA QUESTÃO
# ---------------------------------------------------------------------------
elif pagina_atual == "nova_questao":
    ui.page_title("Nova questão")

    with st.expander("Adicionar área ou assunto", icon=":material/add_circle:"):
        col1, col2 = st.columns(2)
        with col1:
            nova_area = st.text_input("Nova área (ex: Cardiologia)")
            if st.button("Adicionar área", icon=":material/add:") and nova_area:
                db.criar_area(nova_area)
                st.success(f"Área '{nova_area}' adicionada.", icon=":material/check_circle:")
                st.rerun()
        with col2:
            areas = mapa_areas()
            if areas:
                area_sub = st.selectbox("Área do novo subtópico", list(areas.keys()), key="area_sub_add")
                novo_sub = st.text_input("Novo subtópico (ex: Arritmias)")
                if st.button("Adicionar subtópico", icon=":material/add:") and novo_sub:
                    db.criar_subtopico(areas[area_sub], novo_sub)
                    st.success(f"Subtópico '{novo_sub}' adicionado.", icon=":material/check_circle:")
                    st.rerun()

    with st.container(key="form_col"):
        with st.container(border=True):
            if _form_questao(None, key_prefix="novaq") == "salvo":
                st.rerun()

# ---------------------------------------------------------------------------
# IMPORTAR PLANILHA
# ---------------------------------------------------------------------------
elif pagina_atual == "importar":
    ui.page_title(
        "Importar planilha",
        "Importe centenas de questões de uma vez a partir de uma planilha Excel (.xlsx) ou CSV.",
    )

    st.download_button(
        "Baixar planilha modelo (.xlsx)", icon=":material/download:",
        data=imp_q.gerar_template_bytes(), file_name="modelo_importacao_questoes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    with st.expander("Colunas aceitas", icon=":material/checklist:"):
        st.markdown("""
        - **area** *(obrigatório)*
        - **subtopico** *(opcional)*
        - **enunciado** *(obrigatório)*
        - **alternativa_a, alternativa_b, alternativa_c, alternativa_d** *(obrigatórias)*
        - **alternativa_e** *(opcional)*
        - **resposta_correta** *(obrigatório — letra da alternativa certa)*
        - **explicacao** *(opcional)*
        - **banca** *(opcional — ex: ENAMED, USP-SP, UNIFESP)*
        - **ano** *(opcional)*

        Variações como "Área", "Assunto", "Gabarito" também são reconhecidas
        automaticamente. Questões com enunciado idêntico já cadastrado na
        mesma área são ignoradas (não duplicam).
        """)

    arquivo = st.file_uploader("Selecione a planilha (.xlsx ou .csv)", type=["xlsx", "csv"])

    if arquivo is not None:
        try:
            df = imp_q.ler_planilha(arquivo, arquivo.name)
        except Exception as e:
            st.error(f"Não consegui ler o arquivo: {e}")
            df = None

        if df is not None:
            faltando = imp_q.validar_planilha(df)
            if faltando:
                st.error(f"Faltam colunas obrigatórias na planilha: {', '.join(faltando)}")
            else:
                st.success(f"Planilha lida com sucesso: {len(df)} linha(s) encontrada(s).", icon=":material/check_circle:")
                st.dataframe(df.head(10), hide_index=True, row_height=36)

                if st.button("Importar todas as questões", type="primary", icon=":material/upload_file:"):
                    with st.spinner("Importando..."):
                        relatorio = imp_q.importar(df)

                    st.success("Importação concluída!", icon=":material/check_circle:")
                    ui.faixa_row([
                        {"label": "Importadas", "valor": str(relatorio["importadas"]), "cor": "var(--correct)"},
                        {"label": "Duplicadas (ignoradas)", "valor": str(relatorio["duplicadas"])},
                        {"label": "Total na planilha", "valor": str(relatorio["total"])},
                    ])
                    if relatorio["erros"]:
                        st.warning(f"{len(relatorio['erros'])} linha(s) com problema:", icon=":material/warning:")
                        df_erros = pd.DataFrame(relatorio["erros"], columns=["Linha", "Motivo"])
                        st.dataframe(df_erros, hide_index=True, row_height=36)
