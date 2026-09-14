import streamlit as st
import pandas as pd
import json
import datetime

import db
import importador_questoes as imp_q
import mediafire_import as mf
import auth
import ui

st.set_page_config(
    page_title="Conduta - Plataforma de Estudos",
    page_icon="🩺",
    layout="wide",
)

# Materiais/questões são um recurso compartilhado entre todos os usuários —
# ações destrutivas ficam restritas a quem está nessa lista.
ADMIN_EMAILS = {"hendrickvk@gmail.com"}


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
# Navegação — grupo "Acervo" (REDESIGN.md §3). Rótulo (exibido) e
# page_key (usado no roteamento abaixo) são desacoplados de propósito: um
# rename futuro do rótulo do menu não precisa tocar em nenhum `if pagina_atual
# == "..."`, só na tabela abaixo — lição da rodada anterior de redesign, onde
# renomear o rótulo quebrava sessões já abertas com o nome antigo em
# session_state. Ícones são Material Symbols (não os SVG Lucide do resto do
# app) porque `st.button(icon=...)` só aceita esse formato ou emoji — Lucide
# fica reservado para marcação própria (selo, badges, marca).
PAGINAS_NAV = [
    ("Acervo", "Materiais", "menu_book", "materiais"),
    ("Acervo", "Banco de questões", "database", "banco"),
    ("Acervo", "Nova questão", "post_add", "nova_questao"),
    ("Acervo", "Importar planilha", "upload_file", "importar"),
    ("Acervo", "Sincronizar MediaFire", "sync", "sincronizar"),
]
LABEL_POR_KEY = {key: label for _, label, _, key in PAGINAS_NAV}


@st.cache_data(ttl=30)
def _contadores_rail():
    return db.contar_questoes(), db.contar_materiais()


# Widgets com `key` não podem ter seu session_state sobrescrito depois de já
# instanciados nesta execução — por isso `ui.empty_state` e o botão
# "Sincronizar agora" de Materiais gravam numa chave separada (_forcar_pagina),
# consumida aqui, antes de qualquer botão de navegação existir.
if "_forcar_pagina" in st.session_state:
    st.session_state["pagina_atual"] = st.session_state.pop("_forcar_pagina")
st.session_state.setdefault("pagina_atual", "banco")
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
                f'<span class="rail-brand-text">{"Conduta" if expandida else ""}</span></div>',
                unsafe_allow_html=True,
            )
        with col_toggle:
            with st.container(key="rail_toggle"):
                icone_toggle = "left_panel_close" if expandida else "left_panel_open"
                if st.button("", icon=f":material/{icone_toggle}:", key="btn_rail_toggle",
                             help="Recolher menu" if expandida else "Expandir menu"):
                    st.session_state["rail_expandida"] = not expandida
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
    col_titulo, col_busca, col_prova, col_tema, col_avatar = st.columns([2, 3, 1.7, 0.5, 0.5])
    with col_titulo:
        st.markdown(f'<div class="topbar-title">{LABEL_POR_KEY[pagina_atual]}</div>', unsafe_allow_html=True)
    with col_busca:
        st.text_input(
            "busca", placeholder="Buscar no Banco de Questões...",
            label_visibility="collapsed", key="busca_global",
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
    col_area, col_esp, col_sub = st.columns(3)
    area_nome_f = col_area.selectbox(
        "Área", nomes_area,
        index=nomes_area.index(area_atual_nome) if area_atual_nome in nomes_area else 0,
        key=f"{key_prefix}_area",
    )
    area_id_f = areas_form[area_nome_f]

    esp_opcoes_f = {"(nenhuma)": None}
    esp_opcoes_f.update({e["nome"]: e["id"] for e in db.listar_especialidades(area_id_f)})
    nomes_esp = list(esp_opcoes_f.keys())
    esp_atual_nome = next(
        (n for n, i in esp_opcoes_f.items() if i == q["especialidade_id"]), "(nenhuma)"
    ) if q else "(nenhuma)"
    esp_nome_f = col_esp.selectbox(
        "Especialidade", nomes_esp,
        index=nomes_esp.index(esp_atual_nome) if esp_atual_nome in nomes_esp else 0,
        key=f"{key_prefix}_esp",
    )
    especialidade_id_f = esp_opcoes_f[esp_nome_f]

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
                    especialidade_id=especialidade_id_f,
                )
                st.success("Questão atualizada.", icon=":material/check_circle:")
            else:
                novo_id = db.criar_questao(
                    area_id_f, subtopico_id_f, enunciado_f, nova_alternativas,
                    resposta_correta_f, explicacao_f, banca_f, int(ano_f),
                    especialidade_id=especialidade_id_f,
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


# ---------------------------------------------------------------------------
# MATERIAIS DE ESTUDO
# ---------------------------------------------------------------------------
if pagina_atual == "materiais":
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
            col_area, col_esp = st.columns(2)
            area_nome = col_area.selectbox("Área", list(areas.keys()), key="mat_area")
            area_id = areas[area_nome]
            esp_opcoes = {"(nenhuma)": None}
            esp_opcoes.update({e["nome"]: e["id"] for e in db.listar_especialidades(area_id)})
            esp_nome = col_esp.selectbox("Especialidade", list(esp_opcoes.keys()), key="mat_esp")
            especialidade_id = esp_opcoes[esp_nome]
            col_sub, col_tipo = st.columns(2)
            subtopicos = db.listar_subtopicos(area_id, especialidade_id)
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
                    db.criar_material(area_id, subtopico_id, tipo, titulo, link, especialidade_id=especialidade_id)
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
                df_mat["Especialidade"] = df_mat["especialidade"].fillna("—")
                df_mat["Assunto"] = df_mat["subtopico"].fillna("—")
                df_view = df_mat.rename(columns={
                    "id": "ID", "tipo": "Tipo", "titulo": "Título", "link_mediafire": "Abrir",
                })

                evento = st.dataframe(
                    df_view, hide_index=True, row_height=44, on_select="rerun", selection_mode="multi-row",
                    column_order=["Tipo", "Título", "Especialidade", "Assunto", "Abrir"],
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
        "subpastas (especialidades → assuntos → arquivos) e cadastra tudo como material de estudo.",
    )

    with st.expander("Estrutura esperada da pasta", icon=":material/info:"):
        st.markdown(
            "Pasta raiz → pastas de especialidade ou grande área (ex: Cardiologia, Cirurgia, "
            "Obstetrícia) → pastas de assunto → apostilas/vídeos (ou subpastas extras tipo "
            "'Apostilas'/'Videoaulas' dentro do assunto, que também são lidas).\n\n"
            "O nome da pasta de primeiro nível é encaixado na classificação fixa grande área > "
            "especialidade: *Aprenda Nefro - Gasometria* vai para Clínica Médica > Nefrologia. Uma "
            "pasta cujo nome não corresponde a nenhuma especialidade é pulada e aparece nos avisos — "
            "renomeie e sincronize de novo.\n\n"
            "Funciona apenas com pastas compartilhadas publicamente (aquelas com link "
            "`mediafire.com/folder/...`) e requer conexão com a internet."
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
                {"label": "Pastas de área", "valor": str(relatorio["areas_criadas"])},
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
        df_q["Especialidade"] = df_q["especialidade"].fillna("—")
        df_view = df_q.rename(columns={"id": "ID", "banca": "Banca", "ano": "Ano", "area": "Área"})

        evento = st.dataframe(
            df_view, hide_index=True, row_height=44, on_select="rerun", selection_mode="multi-row",
            column_order=["ID", "Banca", "Ano", "Área", "Especialidade", "Enunciado"],
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

    with st.expander("Adicionar assunto", icon=":material/add_circle:"):
        # Grandes áreas e especialidades vêm de db.TAXONOMIA e não se criam
        # pela tela: uma área digitada à mão era como nomes soltos acabavam
        # misturados às grandes áreas no filtro.
        st.caption(
            "Grandes áreas e especialidades são fixas. Assunto é o nível abaixo delas "
            "(ex: Clínica Médica > Cardiologia > Arritmias)."
        )
        areas = mapa_areas()
        if areas:
            col1, col2 = st.columns(2)
            area_sub = col1.selectbox("Área", list(areas.keys()), key="area_sub_add")
            esp_opcoes_add = {"(nenhuma)": None}
            esp_opcoes_add.update({e["nome"]: e["id"] for e in db.listar_especialidades(areas[area_sub])})
            esp_sub = col2.selectbox("Especialidade", list(esp_opcoes_add.keys()), key="esp_sub_add")
            novo_sub = st.text_input("Novo assunto (ex: Arritmias)")
            if st.button("Adicionar assunto", icon=":material/add:") and novo_sub:
                db.criar_subtopico(areas[area_sub], novo_sub, especialidade_id=esp_opcoes_add[esp_sub])
                st.success(f"Assunto '{novo_sub}' adicionado.", icon=":material/check_circle:")
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
        - **area** *(obrigatório — grande área, ex: Clínica Médica, ou já a especialidade, ex: Cardiologia)*
        - **especialidade** *(opcional — ex: Cardiologia)*
        - **subtopico** *(opcional)*
        - **enunciado** *(obrigatório)*
        - **alternativa_a, alternativa_b, alternativa_c, alternativa_d** *(obrigatórias)*
        - **alternativa_e** *(opcional)*
        - **resposta_correta** *(obrigatório — letra da alternativa certa)*
        - **explicacao** *(opcional)*
        - **banca** *(opcional — ex: ENAMED, USP-SP, UNIFESP)*
        - **ano** *(opcional)*

        Variações como "Área", "Assunto", "Gabarito" também são reconhecidas
        automaticamente. A área precisa corresponder a uma grande área ou
        especialidade existente — um nome desconhecido vira erro da linha, não
        uma área nova. Questões com enunciado idêntico já cadastrado na mesma
        área são ignoradas (não duplicam).
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
