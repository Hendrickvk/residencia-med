import streamlit as st
import pandas as pd
import json
import datetime

import db
import importador_questoes as imp_q
import auth
import ui

st.set_page_config(
    page_title="Conduta - Plataforma de Estudos",
    page_icon="🩺",
    layout="wide",
)

# Questões são um recurso compartilhado entre todos os usuários — ações
# destrutivas ficam restritas a quem está na configuração (`ADMIN_EMAILS` no
# .streamlit/secrets.toml ou no ambiente). Estava escrito aqui, e este
# repositório é público.


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

eh_admin = st.session_state.get("usuario_email") in db.emails_admin()
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
    ("Acervo", "Banco de questões", "database", "banco"),
    ("Acervo", "Nova questão", "post_add", "nova_questao"),
    ("Acervo", "Importar planilha", "upload_file", "importar"),
    ("Acervo", "Revisar explicações", "rate_review", "revisar"),
    ("Acompanhamento", "Uso da plataforma", "insights", "uso"),
]
LABEL_POR_KEY = {key: label for _, label, _, key in PAGINAS_NAV}


@st.cache_data(ttl=30)
def _contadores_rail():
    return db.contar_questoes(), db.contar_relatos_pendentes()


# Widgets com `key` não podem ter seu session_state sobrescrito depois de já
# instanciados nesta execução — por isso `ui.empty_state` grava numa chave
# separada (_forcar_pagina),
# consumida aqui, antes de qualquer botão de navegação existir.
if "_forcar_pagina" in st.session_state:
    st.session_state["pagina_atual"] = st.session_state.pop("_forcar_pagina")
# Chave de uma tela que já não existe (ex.: "materiais", removida) volta ao Banco.
if st.session_state.get("pagina_atual") not in LABEL_POR_KEY:
    st.session_state["pagina_atual"] = "banco"
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
        n_questoes, n_relatos = _contadores_rail()
        # O relato do aluno é o sinal mais barato de erro de conteúdo: fica no
        # rodapé para o admin ver sem abrir a tela de revisão.
        aviso = f' · <strong>{n_relatos} relato(s)</strong>' if n_relatos else ""
        st.markdown(
            f'<div class="rail-footer">{n_questoes} questões{aviso}</div>',
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
            dias_restantes = (datetime.date.fromisoformat(data_alvo) - db.hoje_br()).days
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

    # Temas são fixos (db.TEMAS) e dependem da especialidade escolhida.
    subtopicos_f = db.listar_temas(area_id_f, especialidade_id_f)
    sub_opcoes_f = {"(nenhum)": None}
    sub_opcoes_f.update({s["nome"]: s["id"] for s in subtopicos_f})
    nomes_sub = list(sub_opcoes_f.keys())
    sub_atual_nome = next((n for n, i in sub_opcoes_f.items() if i == q["subtopico_id"]), "(nenhum)") if q else "(nenhum)"
    sub_nome_f = col_sub.selectbox(
        "Tema", nomes_sub,
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

    col_correta, col_tipo, col_banca, col_ano = st.columns([1, 1, 2, 1])
    correta_atual = q["resposta_correta"] if q and q["resposta_correta"] in letras else "A"
    resposta_correta_f = col_correta.selectbox(
        "Alternativa correta", letras, index=letras.index(correta_atual), key=f"{key_prefix}_correta",
    )
    banca_f = col_banca.text_input(
        "Banca / Instituição (ex: ENAMED, USP-SP, UNIFESP)",
        value=(q["banca"] if q else "") or "", key=f"{key_prefix}_banca",
    )
    # Sem tipo a questão fica fora do filtro do Praticar e da seção
    # "Por tipo de pergunta" do Painel, por isso é exigido ao salvar.
    tipos_opcoes = ["(nenhum)"] + list(db.TIPOS_PERGUNTA)
    tipo_atual = (q["tipo_pergunta"] if q else None) or "(nenhum)"
    tipo_f = col_tipo.selectbox(
        "Tipo de pergunta", tipos_opcoes,
        index=tipos_opcoes.index(tipo_atual) if tipo_atual in tipos_opcoes else 0,
        key=f"{key_prefix}_tipo",
        help="O que as alternativas pedem. Pedindo mais de uma coisa, vale a etapa mais "
             "adiante (Conduta > Exames > Diagnóstico).",
    )
    tipo_pergunta_f = None if tipo_f == "(nenhum)" else tipo_f

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
        elif tipo_pergunta_f is None:
            st.error("Escolha o tipo de pergunta.", icon=":material/cancel:")
        else:
            if q is not None:
                db.atualizar_questao(
                    q["id"], area_id_f, subtopico_id_f, enunciado_f, nova_alternativas,
                    resposta_correta_f, explicacao_f, banca_f, int(ano_f),
                    especialidade_id=especialidade_id_f, tipo_pergunta=tipo_pergunta_f,
                )
                st.success("Questão atualizada.", icon=":material/check_circle:")
            else:
                novo_id = db.criar_questao(
                    area_id_f, subtopico_id_f, enunciado_f, nova_alternativas,
                    resposta_correta_f, explicacao_f, banca_f, int(ano_f),
                    especialidade_id=especialidade_id_f, tipo_pergunta=tipo_pergunta_f,
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
# BANCO DE QUESTÕES
# ---------------------------------------------------------------------------
if pagina_atual == "banco":
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
    # Grande área, especialidade e tema são fixos (db.TAXONOMIA e db.TEMAS) e
    # não se criam pela tela: nomes digitados à mão eram como "áreas" soltas
    # acabavam misturadas às grandes áreas no filtro.

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
        - **tema** *(opcional — um dos temas fixos da especialidade, ex: Arritmias)*
        - **enunciado** *(obrigatório)*
        - **alternativa_a, alternativa_b, alternativa_c, alternativa_d** *(obrigatórias)*
        - **alternativa_e** *(opcional)*
        - **resposta_correta** *(obrigatório — letra da alternativa certa)*
        - **tipo** *(obrigatório — Diagnóstico, Exames, Conduta ou Conceitos, pelo que as alternativas pedem)*
        - **explicacao** *(opcional)*
        - **banca** *(opcional — ex: ENAMED, USP-SP, UNIFESP)*
        - **ano** *(opcional)*

        Variações como "Área", "Assunto", "Gabarito" também são reconhecidas
        automaticamente. A área precisa corresponder a uma grande área ou
        especialidade existente — um nome desconhecido vira erro da linha, não
        uma área nova. O tema segue a mesma regra. Questões com enunciado idêntico já cadastrado na mesma
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


# ---------------------------------------------------------------------------
# REVISAR EXPLICAÇÕES
# ---------------------------------------------------------------------------
# As explicações foram escritas do zero e só passaram por checagem automática
# de que cada uma defende a letra oficial — isso não pega raciocínio clínico
# ruim defendendo a letra certa. Esta tela é para o admin ler uma a uma e
# marcar o que corrigir depois, em lote, por UPDATE.
# ponytail: as marcas ficam num JSON do repositório, não numa tabela. É uma
# varredura de um admin só, numa máquina só; vira tabela se precisar ser
# compartilhada com o servidor.
ARQUIVO_REVISAO = "backups/revisao_explicacoes.json"


def _marcas_revisao():
    try:
        with open(ARQUIVO_REVISAO, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _gravar_marca(questao_id, status, nota):
    marcas = _marcas_revisao()
    marcas[str(questao_id)] = {
        "status": status,
        "nota": nota.strip(),
        "em": db.agora_br().isoformat(timespec="seconds"),
    }
    with open(ARQUIVO_REVISAO, "w", encoding="utf-8") as f:
        json.dump(marcas, f, ensure_ascii=False, indent=1, sort_keys=True)


if pagina_atual == "revisar":
    ui.page_title(
        "Revisar explicações",
        "Leia a explicação contra o gabarito e marque o que precisa de ajuste. "
        "As marcas ficam em backups/revisao_explicacoes.json.",
    )

    # Relatos dos alunos vêm primeiro: apontam onde olhar, ao contrário da
    # varredura questão a questão abaixo, que é cara e cega.
    relatos = db.listar_relatos(pendentes=True)
    if relatos:
        with st.expander(f"⚑ {len(relatos)} relato(s) de erro pendente(s)", expanded=True):
            for r in relatos:
                prova = f"{r['banca']} {r['edicao']}" if r["edicao"] else (r["banca"] or "—")
                numero = f" · questão {r['numero_prova']}" if r["numero_prova"] else ""
                st.markdown(
                    f"**id {r['questao_id']}** · {prova}{numero} · **{r['parte']}** — "
                    f"{r['comentario'] or '_sem comentário_'}"
                )
                st.caption(
                    f"{r['usuario']} em {r['criado_em']:%d/%m/%Y %H:%M} · {r['trecho']}…"
                )
                if st.button("Marcar como resolvido", key=f"rev_relato_{r['id']}"):
                    db.resolver_relato(r["id"])
                    st.rerun()
                st.divider()

    edicoes = db.listar_edicoes_oficiais()
    rotulos = [f"{e['banca']} {e['edicao']}" for e in edicoes]
    padrao = next((i for i, r in enumerate(rotulos) if r.startswith("USP")), 0)
    escolha = st.selectbox("Edição", rotulos, index=padrao, key="rev_edicao")
    edicao = edicoes[rotulos.index(escolha)]

    ids = db.ids_questoes_da_edicao(edicao["banca"], edicao["edicao"])
    marcas = _marcas_revisao()
    pendentes = [i for i, qid in enumerate(ids) if str(qid) not in marcas]
    ajustar = [qid for qid in ids if marcas.get(str(qid), {}).get("status") == "ajustar"]

    faixa = [
        {"label": "Questões", "valor": str(len(ids))},
        {"label": "Revisadas", "valor": str(len(ids) - len(pendentes)), "cor": "var(--correct)"},
    ]
    item_ajustar = {"label": "Para ajustar", "valor": str(len(ajustar))}
    if ajustar:
        item_ajustar["cor"] = "var(--warn)"
    ui.faixa_row(faixa + [item_ajustar])

    chave_idx = f"rev_idx_{edicao['banca']}_{edicao['edicao']}"
    if chave_idx not in st.session_state:
        st.session_state[chave_idx] = pendentes[0] if pendentes else 0
    idx = max(0, min(st.session_state[chave_idx], len(ids) - 1))

    nav_a, nav_b, nav_c = st.columns([1, 2, 1])
    if nav_a.button("← Anterior", key="rev_ant", disabled=idx == 0, use_container_width=True):
        st.session_state[chave_idx] = idx - 1
        st.rerun()
    nav_b.markdown(
        f"<div style='text-align:center;padding-top:.4rem'>{idx + 1} de {len(ids)}</div>",
        unsafe_allow_html=True,
    )
    if nav_c.button("Próxima →", key="rev_prox", disabled=idx >= len(ids) - 1, use_container_width=True):
        st.session_state[chave_idx] = idx + 1
        st.rerun()

    q = db.obter_questao(ids[idx])
    marca = marcas.get(str(q["id"]), {})

    with st.container(border=True):
        ui.render_cabecalho_questao(q)
        ui.render_alternativas_resultado(q)
        st.caption(f"Gabarito oficial: **{q['resposta_correta']}** · questão {q['numero_prova']} do caderno")
        if q["explicacao"]:
            st.info(q["explicacao"], icon=":material/lightbulb:")
        else:
            st.warning("Sem explicação cadastrada.", icon=":material/warning:")

    if marca:
        rotulo = "precisa de ajuste" if marca["status"] == "ajustar" else "está certa"
        st.caption(f"Já revisada em {marca['em'][:16].replace('T', ' ')} — {rotulo}."
                   + (f" Nota: {marca['nota']}" if marca["nota"] else ""))

    nota = st.text_area(
        "O que ajustar (opcional)", value=marca.get("nota", ""),
        key=f"rev_nota_{q['id']}", placeholder="Ex.: defende a letra certa, mas pelo motivo errado…",
    )

    col_ok, col_aj = st.columns(2)
    if col_ok.button("Está certa", key=f"rev_ok_{q['id']}", use_container_width=True,
                     icon=":material/check_circle:"):
        _gravar_marca(q["id"], "ok", nota)
        st.session_state[chave_idx] = min(idx + 1, len(ids) - 1)
        st.rerun()
    if col_aj.button("Precisa de ajuste", key=f"rev_aj_{q['id']}", type="primary",
                     use_container_width=True, icon=":material/flag:"):
        _gravar_marca(q["id"], "ajustar", nota)
        st.session_state[chave_idx] = min(idx + 1, len(ids) - 1)
        st.rerun()

    if ajustar:
        with st.expander(f"{len(ajustar)} marcada(s) para ajuste nesta edição"):
            for qid in ajustar:
                m = marcas[str(qid)]
                st.markdown(f"**id {qid}** — {m['nota'] or '(sem nota)'}")


if pagina_atual == "uso":
    ui.page_title(
        "Uso da plataforma",
        "Quem estuda, quanto e com o quê, e os erros que o app das alunas mandou. Estudo é resposta, "
        "caso revisado ou cartão avaliado: a mesma régua da ofensiva. As contas dos testes ficam de fora.",
    )
    # A tabela por conta mostra os e-mails de todo mundo: é tela do dono da
    # plataforma, e não de qualquer conta que passe pela senha do Caddy.
    if not eh_admin:
        st.error("Esta tela é só para quem administra a plataforma.")
        st.stop()

    m = db.metricas_uso()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Contas", m["contas"]["total"],
              f"+{m['contas']['novas_7d']} na semana" if m["contas"]["novas_7d"] else None)
    c2.metric("Estudaram hoje", m["ativas"]["hoje"])
    c3.metric("Nos últimos 7 dias", m["ativas"]["7d"])
    c4.metric("Nos últimos 30 dias", m["ativas"]["30d"])

    # Dia sem ninguém também é informação: o gráfico mostra os 14 dias.
    calendario = pd.date_range(end=pd.Timestamp(db.hoje_br()), periods=14)
    por_dia = {d["dia"]: d["ativas"] for d in m["ativas_por_dia"]}
    st.markdown("**Contas que estudaram, por dia**")
    st.bar_chart(pd.DataFrame({"Contas": [por_dia.get(d.date(), 0) for d in calendario]}, index=calendario))

    s = m["semana"]
    st.markdown(
        f"**Nos últimos 7 dias:** {s['simulados']} simulado(s) terminado(s) · "
        f"{s['cartoes_criados']} cartão(ões) criado(s) · {s['relatos']} relato(s) de erro"
    )

    st.markdown("**Por conta**, da atividade mais recente para a mais antiga (contagens dos últimos 30 dias)")
    st.dataframe(pd.DataFrame([{
        "Conta": c["nome"] or c["email"],
        "E-mail": c["email"],
        "Última atividade": c["ultima_atividade"].strftime("%d/%m %H:%M") if c["ultima_atividade"] else "nunca estudou",
        "Dias ativos": c["dias_ativos"],
        "Respostas": c["respostas"],
        "Revisões": c["revisoes"],
        "Cartões": c["cartoes"],
        "E-mail confirmado": "sim" if c["confirmada"] else "não",
    } for c in m["por_conta"]]), hide_index=True, use_container_width=True)

    erros = db.erros_front_recentes()
    st.markdown(f"**Erros do app nos últimos 7 dias:** {len(erros) if erros else 'nenhum'}")
    for e in erros:
        with st.expander(f"{e['vezes']}× · {e['contas']} conta(s) · {e['ultima']:%d/%m %H:%M} · {e['mensagem'][:90]}"):
            st.caption(f"Tela: {e['url'] or '—'} · Navegador: {e['agente'] or '—'}")
            if e["pilha"]:
                st.code(e["pilha"], language=None)
