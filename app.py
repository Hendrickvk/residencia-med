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
ui.inject_custom_css()

# Materiais são um recurso compartilhado entre todos os usuários — ações
# destrutivas em massa (excluir todos de uma vez) ficam restritas a quem
# está nessa lista, pra não deixar qualquer conta apagar o acervo de todo
# mundo.
ADMIN_EMAILS = {"hendrickvk@gmail.com"}

# db.init_db() cria tabelas/índices/seed — precisa rodar uma vez, não a
# cada interação. Sem cache, essa chamada sozinha custava ~1.6s (~27
# round-trips ao Postgres: 8 CREATE TABLE, 13 INSERT de seed, checagem de
# colunas, índices) e rodava em TODO clique, porque Streamlit reroda o
# script inteiro a cada interação. st.cache_resource garante execução
# única por processo do servidor (compartilhada entre todos os usuários).
@st.cache_resource
def _init_db_uma_vez():
    db.init_db()
    return True


_init_db_uma_vez()

if "usuario_id" not in st.session_state:
    auth.render_login_signup()
    st.stop()

eh_admin = st.session_state.get("usuario_email") in ADMIN_EMAILS

# ---------------------------------------------------------------------------
# Sidebar / navegação
# ---------------------------------------------------------------------------
# Cada página é um st.button (não mais st.radio) pra dar pra ter um modo
# "recolhido" (só ícone, como em plataformas tipo Notion/Linear) sem manter
# duas implementações de menu separadas — só muda o rótulo exibido.
PAGINAS_NAV = [
    ("Dashboard", "dashboard"),
    ("Praticar", "edit_note"),
    ("Simulado", "timer"),
    ("Nova Questão", "post_add"),
    ("Importar Planilha", "upload_file"),
    ("Revisão Espaçada", "psychology"),
    ("Materiais de Estudo", "menu_book"),
    ("Sincronizar MediaFire", "sync"),
    ("Banco de Questões", "database"),
]


@st.cache_data(ttl=30)
def _contadores_sidebar():
    """Contadores só informativos, iguais pra todo mundo — cachear evita
    2 round-trips ao Postgres a cada clique em qualquer página."""
    return db.contar_questoes(), db.contar_materiais()


# Widgets com `key` não podem ter seu session_state sobrescrito depois de
# já terem sido instanciados nesta mesma execução (StreamlitWidgetAlready
# InstantiatedError) — por isso os botões de "ir para" em ui.empty_state
# gravam numa chave separada (_forcar_pagina) que só é consumida AQUI,
# antes de qualquer botão de navegação ser criado.
if "_forcar_pagina" in st.session_state:
    st.session_state["nav_pagina"] = st.session_state.pop("_forcar_pagina")
st.session_state.setdefault("nav_pagina", PAGINAS_NAV[0][0])
st.session_state.setdefault("sidebar_expandida", False)

expandida = st.session_state["sidebar_expandida"]

if not expandida:
    # Só dá pra mudar a largura da sidebar via CSS (o Streamlit não expõe
    # isso como parâmetro) — injeta só quando recolhida pra não interferir
    # no redimensionamento manual normal quando expandida. Também redesenha
    # os botões de navegação/sair como ícones quadrado-arredondados
    # pequenos e centralizados — sem isso, use_container_width=True (usado
    # no modo expandido) estica cada botão até a largura toda da rail,
    # virando uma "caixa" grande e vazia em volta de um ícone pequeno.
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            min-width: 7.5rem !important;
            width: 7.5rem !important;
        }
        [data-testid="stSidebarUserContent"] {
            padding-left: 0.4rem !important;
            padding-right: 0.4rem !important;
        }
        /* Ícones alinhados à esquerda (não centralizados na rail toda) —
           reserva a faixa direita, perto da borda, só pro handle de
           expandir/recolher (CSS em ui.py). Com a rail mais estreita e
           os ícones centralizados, ícone (2.75rem) e handle (32px)
           não cabem lado a lado sem se sobrepor. */
        [data-testid="stSidebar"] .st-key-nav_area {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            padding-left: 0.5rem;
            gap: 0.35rem;
        }
        [data-testid="stSidebar"] .st-key-nav_area .stButton button {
            width: 2.75rem !important;
            height: 2.75rem !important;
            min-height: 2.75rem !important;
            min-width: 2.75rem !important;
            padding: 0 !important;
            border-radius: 12px;
            justify-content: center;
        }
        [data-testid="stSidebar"] .st-key-nav_area .stButton button[kind="secondary"] {
            border-color: transparent;
            background: transparent;
        }
        /* Avatar alinhado com os ícones do menu (mesmo padding-left),
           em vez de centralizado na rail toda (regra padrão em ui.py,
           usada só no modo expandido). */
        [data-testid="stSidebar"] .st-key-perfil_popover {
            justify-content: flex-start !important;
            padding-left: 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

with st.sidebar:
    # Marca + toggle + usuário ficam num container próprio
    # (key="sidebar_header") porque o handle de expandir/recolher é
    # ancorado NELE (altura constante), não na sidebar inteira — assim
    # ele sempre fica logo abaixo do cabeçalho, acima do primeiro item
    # do menu, em vez de "flutuar" no meio da tela dependendo de quanto
    # conteúdo a página atual tem.
    with st.container(key="sidebar_header"):
        if expandida:
            st.markdown(
                f"""
                <div style="display:flex; align-items:center; gap:0.55rem;">
                    <span style="color:#0F766E; display:flex;">{ui.icon_svg("stethoscope", size=21)}</span>
                    <span style="font-size:1.15rem; font-weight:700; color:#142523;">Residência Med</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="display:flex; justify-content:flex-start; padding-left:0.5rem; '
                f'color:#0F766E; margin-top:0.2rem;">'
                f'{ui.icon_svg("stethoscope", size=22)}</div>',
                unsafe_allow_html=True,
            )

        # Botão único de expandir/recolher — um "handle" redondo ancorado
        # na borda da sidebar (CSS em ui.py), em vez dos dois botões
        # separados de antes (um no cabeçalho expandido, outro full-width
        # recolhido).
        with st.container(key="toggle_handle"):
            if expandida:
                if st.button("", icon=":material/left_panel_close:", key="toggle_fechar", help="Recolher menu"):
                    st.session_state["sidebar_expandida"] = False
                    st.rerun()
            else:
                if st.button("", icon=":material/left_panel_open:", key="toggle_abrir", help="Expandir menu"):
                    st.session_state["sidebar_expandida"] = True
                    st.rerun()

        email_usuario = st.session_state.get("usuario_email", "")
        iniciais = "".join(p[0] for p in email_usuario.replace("@", " ").split()[:1])[:2].upper() or "?"

        # Perfil como popover: só o avatar (iniciais) fica visível por
        # padrão nos dois modos — clicar nele abre um card com e-mail
        # completo e o botão de sair, em vez de deixar o e-mail/logout
        # sempre expostos na sidebar.
        with st.popover(iniciais, key="perfil_popover", help=email_usuario):
            st.markdown(
                f'<div class="p-avatar" style="width:2.4rem; height:2.4rem; '
                f'margin:0 auto 0.6rem; font-size:0.85rem;">{iniciais}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="text-align:center; font-size:0.85rem; color:#142523; '
                f'margin-bottom:0.75rem; word-break:break-all;">{email_usuario}</div>',
                unsafe_allow_html=True,
            )
            if st.button("Sair da conta", icon=":material/logout:", use_container_width=True, key="sair_popover"):
                for chave in ("usuario_id", "usuario_email"):
                    st.session_state.pop(chave, None)
                st.rerun()

    st.markdown("---")

    with st.container(key="nav_area"):
        for nome, icone in PAGINAS_NAV:
            ativo = st.session_state["nav_pagina"] == nome
            if st.button(
                nome if expandida else "",
                icon=f":material/{icone}:",
                key=f"nav_{nome}",
                type="primary" if ativo else "secondary",
                use_container_width=expandida,
                help=None if expandida else nome,
            ):
                st.session_state["nav_pagina"] = nome
                st.rerun()

    pagina = st.session_state["nav_pagina"]

    st.markdown("---")

    if expandida:
        _n_questoes, _n_materiais = _contadores_sidebar()
        st.caption(f"Total de questões cadastradas: **{_n_questoes}**")
        st.caption(f"Total de materiais cadastrados: **{_n_materiais}**")


@st.cache_data(ttl=60)
def mapa_areas():
    return {a["nome"]: a["id"] for a in db.listar_areas()}


@st.cache_data(ttl=60)
def _listar_bancas_cache():
    return db.listar_bancas()


# TTL curto: o dashboard muda toda vez que o usuário responde uma questão,
# mas não precisa refletir isso em tempo real — cachear por alguns segundos
# elimina as 7 idas sequenciais ao Postgres que rodavam a cada clique em
# QUALQUER lugar do app (Streamlit reroda o script inteiro a cada
# interação), sem deixar os números velhos por muito tempo.
@st.cache_data(ttl=15)
def _dash_combinado(usuario_id):
    return db.desempenho_dashboard_combinado(usuario_id=usuario_id)


@st.cache_data(ttl=15)
def _dash_evolucao_diaria(usuario_id):
    return db.evolucao_diaria(usuario_id=usuario_id)


@st.cache_data(ttl=15)
def _dash_desempenho_por_subtopico(usuario_id):
    return db.desempenho_por_subtopico(usuario_id=usuario_id)


@st.cache_data(ttl=15)
def _dash_questoes_mais_erradas(usuario_id):
    return db.questoes_mais_erradas(usuario_id=usuario_id)


def controle_paginacao(chave, total, por_pagina=50):
    """Widget de paginação reutilizável. Guarda a página atual em
    st.session_state[chave] e devolve (pagina_atual, offset).
    Sempre renderiza no máximo `por_pagina` itens por vez — evita travar
    o navegador quando há milhares de registros (questões/materiais)."""
    total_paginas = max(1, -(-total // por_pagina))  # arredonda pra cima
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
            f"<div style='text-align:center'>Página {st.session_state[chave] + 1} "
            f"de {total_paginas} — {total} resultado(s)</div>",
            unsafe_allow_html=True,
        )
    with col3:
        if st.button("Próxima", key=f"{chave}_next", icon=":material/arrow_forward:", disabled=st.session_state[chave] >= total_paginas - 1):
            st.session_state[chave] += 1
            st.rerun()

    pagina_atual = st.session_state[chave]
    return pagina_atual, pagina_atual * por_pagina


def resetar_paginacao_se_filtro_mudou(chave, assinatura_filtro):
    """Zera a página quando um filtro (área/tipo/busca) muda, senão o
    usuário pode ficar 'preso' numa página que não existe mais."""
    chave_assinatura = f"{chave}_assinatura"
    if st.session_state.get(chave_assinatura) != assinatura_filtro:
        st.session_state[chave_assinatura] = assinatura_filtro
        st.session_state[chave] = 0


def _form_questao(q, *, key_prefix):
    """Formulário de criar/editar questão, compartilhado entre 'Nova
    Questão' e o dialog de edição do Banco de Questões — antes eram duas
    cópias quase idênticas (uma com variáveis soltas, outra com dict),
    já levemente divergentes. `q=None` cria; `q` preenchido edita.
    Devolve "salvo", "cancelado" ou None (nada aconteceu ainda)."""
    areas_form = mapa_areas()
    if not areas_form:
        ui.empty_state(
            "Nenhuma área cadastrada ainda",
            "Use 'Cadastrar nova área ou subtópico' antes de criar questões.",
            icon="square-plus",
        )
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
        # Em edição a imagem salva na hora, como já era — em criação (q
        # é None) a questão ainda não tem id, então o arquivo só é
        # aplicado depois do INSERT, no bloco de salvar abaixo.
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
    if col_salvar.button(label_botao, icon=":material/save:", key=f"{key_prefix}_salvar"):
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


def consolidar_simulado_no_historico(simulado_id, usuario_id):
    """Joga as respostas do simulado nos mesmos caminhos usados por
    'Praticar' (db.registrar_resposta + sr.registrar_revisao),
    para que o Dashboard e a fila de repetição espaçada considerem o
    simulado automaticamente. Chamar uma única vez, ao finalizar."""
    for item in db.listar_itens_simulado(simulado_id, usuario_id=usuario_id):
        if item["resposta_dada"] is None:
            continue
        correta = bool(item["correta"])
        db.registrar_resposta(item["id"], item["resposta_dada"], correta, usuario_id=usuario_id)
        sr.registrar_revisao(item["id"], 5 if correta else 1, usuario_id=usuario_id)


# ---------------------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------------------
if pagina == "Dashboard":
    ui.page_header("layout-dashboard", "Dashboard de Desempenho")

    dash = _dash_combinado(st.session_state.usuario_id)
    desemp_area = dash["por_area"]
    if not desemp_area:
        ui.empty_state(
            "Ainda não há respostas registradas",
            "Responda algumas questões para começar a acompanhar seu desempenho aqui.",
            cta_label="Ir para Praticar", cta_icon=":material/arrow_forward:",
            cta_pagina="Praticar",
        )
    else:
        df_area = pd.DataFrame([dict(r) for r in desemp_area])

        col1, col2, col3 = st.columns(3)
        total_resp = int(df_area["total"].sum())
        total_acertos = int(df_area["acertos"].sum())
        pct_geral = round(100 * total_acertos / total_resp, 1) if total_resp else 0
        col1.metric("Questões respondidas", total_resp)
        col2.metric("Acertos", total_acertos)
        col3.metric("% de acerto geral", f"{pct_geral}%")

        st.subheader("Desempenho por área (% de acerto)")
        st.bar_chart(df_area.set_index("area")["pct_acerto"], color="#0F766E")

        st.subheader("Áreas com mais erros (prioridade de revisão)")
        piores = df_area.sort_values("pct_acerto").head(5)
        ui.metric_badge_row([
            {
                "label": row["area"],
                "valor": f"{row['pct_acerto']}% ({int(row['acertos'])}/{int(row['total'])})",
                "cor": ui.cor_semantica_pct(row["pct_acerto"]),
            }
            for _, row in piores.iterrows()
        ])

        st.subheader("Evolução diária")
        evol = _dash_evolucao_diaria(st.session_state.usuario_id)
        if evol:
            df_evol = pd.DataFrame([dict(r) for r in evol]).set_index("dia")
            st.line_chart(df_evol[["pct_acerto"]], color="#0F766E")
            st.bar_chart(df_evol[["total"]], color="#155E75")

        st.subheader("Desempenho por banca / instituição")
        desemp_banca = dash["por_banca"]
        if not desemp_banca:
            st.caption(
                "Nenhuma resposta registrada em questões com banca definida "
                "ainda. Preencha o campo 'Banca' ao cadastrar ou importar "
                "questões para acompanhar esse comparativo."
            )
        else:
            df_banca = pd.DataFrame([dict(r) for r in desemp_banca])
            st.bar_chart(df_banca.set_index("banca")["pct_acerto"], color="#0F766E")

            sem_banca = dash["sem_banca"]
            if sem_banca:
                st.caption(
                    f":material/info: {sem_banca} resposta(s) de questões sem banca definida "
                    "não entram nessa comparação."
                )

            with st.expander("Comparar bancas por área", icon=":material/table_chart:"):
                desemp_banca_area = dash["por_banca_area"]
                df_ba = pd.DataFrame([dict(r) for r in desemp_banca_area])
                pivot = df_ba.pivot_table(index="area", columns="banca", values="pct_acerto")
                pivot_fmt = pivot.map(lambda v: f"{v:.1f}%" if pd.notna(v) else "—")
                st.caption("% de acerto por área, banca a banca ('—' = sem respostas dessa combinação).")
                st.dataframe(pivot_fmt, use_container_width=True)

        with st.expander("Desempenho por subtópico", icon=":material/insights:"):
            desemp_sub = _dash_desempenho_por_subtopico(st.session_state.usuario_id)
            if desemp_sub:
                df_sub = pd.DataFrame([dict(r) for r in desemp_sub])
                st.dataframe(df_sub, use_container_width=True, hide_index=True)

        with st.expander("Questões mais erradas", icon=":material/error:"):
            piores_q = _dash_questoes_mais_erradas(st.session_state.usuario_id)
            if piores_q:
                df_q = pd.DataFrame([dict(r) for r in piores_q])
                st.dataframe(
                    df_q[["area", "enunciado", "total_respostas", "erros", "pct_erro"]],
                    use_container_width=True, hide_index=True,
                )

# ---------------------------------------------------------------------------
# RESPONDER QUESTÕES
# ---------------------------------------------------------------------------
elif pagina == "Praticar":
    ui.page_header("pencil-line", "Responder Questões")

    areas = mapa_areas()
    if not areas:
        ui.empty_state(
            "Nenhuma área cadastrada ainda",
            "Cadastre uma área (ex: Cardiologia) antes de responder questões.",
            icon="square-plus", cta_label="Ir para Nova Questão",
            cta_icon=":material/arrow_forward:", cta_pagina="Nova Questão",
        )
    else:
        col_a, col_b = st.columns(2)
        area_nome = col_a.selectbox("Filtrar por área (opcional)", ["Todas"] + list(areas.keys()))
        area_id = areas[area_nome] if area_nome != "Todas" else None

        if "fila_questoes" not in st.session_state or st.button("Gerar novo lote", icon=":material/refresh:"):
            questoes = db.listar_questoes(area_id=area_id)
            ids = [q["id"] for q in questoes]
            random.shuffle(ids)
            st.session_state.fila_questoes = ids
            st.session_state.idx_atual = 0
            st.session_state.fila_area_id = area_id

        # O filtro de área não regenera a fila sozinho (só o botão acima
        # faz isso) — sem esse aviso, o usuário podia trocar o filtro e
        # continuar respondendo silenciosamente questões da área antiga.
        if area_id != st.session_state.get("fila_area_id"):
            st.caption(
                ":material/info: Filtro mudou — clique em **Gerar novo lote** "
                "para aplicá-lo (a fila atual continua sendo do filtro anterior)."
            )

        fila = st.session_state.get("fila_questoes", [])
        idx = st.session_state.get("idx_atual", 0)

        if not fila:
            ui.empty_state(
                "Nenhuma questão encontrada para esse filtro",
                "Cadastre questões para essa área, ou selecione 'Todas' acima.",
                icon="square-plus", cta_label="Ir para Nova Questão",
                cta_icon=":material/arrow_forward:", cta_pagina="Nova Questão",
            )
        elif idx >= len(fila):
            st.success("Você respondeu todas as questões desse lote! Gere um novo lote acima.")
        else:
            q = db.obter_questao(fila[idx])
            st.progress((idx) / len(fila))
            st.caption(f"Questão {idx + 1} de {len(fila)}")

            resposta = ui.render_questao(q, modo="interativa", key=f"resp_{q['id']}")

            if st.button(
                "Confirmar resposta", key=f"conf_{q['id']}", icon=":material/check:",
                disabled=resposta is None,
            ):
                correta = (resposta == q["resposta_correta"])
                db.registrar_resposta(q["id"], resposta, correta, usuario_id=st.session_state.usuario_id)

                if correta:
                    st.success(f"Correto! Resposta: {q['resposta_correta']}", icon=":material/check_circle:")
                else:
                    st.error(f"Errado. A resposta correta é: {q['resposta_correta']}", icon=":material/cancel:")

                if q["explicacao"]:
                    st.info(q["explicacao"], icon=":material/lightbulb:")

                # qualidade simples para a repetição espaçada
                qualidade = 5 if correta else 1
                sr.registrar_revisao(q["id"], qualidade, usuario_id=st.session_state.usuario_id)

                st.session_state.idx_atual += 1
                if st.button("Próxima questão", icon=":material/arrow_forward:"):
                    st.rerun()

# ---------------------------------------------------------------------------
# SIMULADO (prova cronometrada)
# ---------------------------------------------------------------------------
elif pagina == "Simulado":
    ui.page_header("timer", "Simulado Cronometrado")

    simulado_id = st.session_state.get("simulado_id")

    if simulado_id is None:
        # --- Tela de configuração ---------------------------------------
        st.caption(
            "Monte uma prova no formato das provas de residência: número "
            "de questões, tempo limite e sem correção até o final."
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
                    "Quantas questões?", min_value=1, max_value=200, value=15, step=1,
                    key="sim_num_custom",
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
                f"(pediu {num_questoes}). Ajuste os filtros ou a quantidade."
            )

        if st.button("Iniciar simulado", icon=":material/play_arrow:", disabled=disponiveis == 0 or disponiveis < num_questoes):
            questoes = db.questoes_aleatorias(area_id, banca, limite=num_questoes)
            ids = [q["id"] for q in questoes]
            novo_id = db.criar_simulado(
                area_id, banca, len(ids), int(tempo_limite_min), ids,
                usuario_id=st.session_state.usuario_id,
            )
            st.session_state.simulado_id = novo_id
            st.session_state.simulado_questoes = ids
            st.session_state.simulado_idx = 0
            st.rerun()

        with st.expander("Histórico de simulados", icon=":material/history:"):
            historico = db.listar_simulados(10, usuario_id=st.session_state.usuario_id)
            if not historico:
                st.caption("Nenhum simulado concluído ainda.")
            else:
                df_hist = pd.DataFrame([dict(h) for h in historico])
                df_hist["area"] = df_hist["area"].fillna("Todas")
                st.dataframe(
                    df_hist[["finalizado_em", "area", "banca", "num_questoes", "acertos", "pct_acerto"]],
                    use_container_width=True, hide_index=True,
                )

    else:
        simulado = db.obter_simulado(simulado_id, usuario_id=st.session_state.usuario_id)
        if simulado is None:
            for chave in ("simulado_id", "simulado_questoes", "simulado_idx"):
                st.session_state.pop(chave, None)
            st.warning("Simulado não encontrado.")
            st.rerun()

        if simulado["finalizado_em"] is not None:
            # --- Tela de resultado ---------------------------------------
            acertos = simulado["acertos"] or 0
            total = simulado["num_questoes"]
            pct = round(100 * acertos / total, 1) if total else 0

            col1, col2, col3 = st.columns(3)
            col1.metric("Acertos", f"{acertos}/{total}")
            col2.metric("% de acerto", f"{pct}%")
            col3.metric("Respondidas", simulado["total_respondidas"] or 0)

            desemp = db.desempenho_simulado(simulado_id, usuario_id=st.session_state.usuario_id)
            if desemp:
                st.subheader("Desempenho por área (neste simulado)")
                df_desemp = pd.DataFrame([dict(r) for r in desemp])
                st.bar_chart(df_desemp.set_index("area")["pct_acerto"], color="#0F766E")

            st.subheader("Revisão completa")
            itens = db.listar_itens_simulado(simulado_id, usuario_id=st.session_state.usuario_id)
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
                    ui.render_questao(item, modo="leitura", resposta_selecionada=item["resposta_dada"])
                    if item["explicacao"]:
                        st.info(item["explicacao"], icon=":material/lightbulb:")

            if st.button("Novo Simulado", icon=":material/add:"):
                for chave in ["simulado_id", "simulado_questoes", "simulado_idx"]:
                    st.session_state.pop(chave, None)
                st.rerun()

        else:
            # --- Simulado em andamento ------------------------------------
            iniciado_em = datetime.datetime.fromisoformat(simulado["iniciado_em"])
            limite_seg = simulado["tempo_limite_min"] * 60
            decorrido_seg = (datetime.datetime.now() - iniciado_em).total_seconds()
            restante_seg = limite_seg - decorrido_seg

            if restante_seg <= 0:
                db.finalizar_simulado(simulado_id, usuario_id=st.session_state.usuario_id)
                consolidar_simulado_no_historico(simulado_id, st.session_state.usuario_id)
                st.warning("Tempo esgotado! Confira seu resultado abaixo.", icon=":material/schedule:")
                st.rerun()
            else:
                ids = st.session_state.get("simulado_questoes") or [
                    i["id"] for i in db.listar_itens_simulado(simulado_id, usuario_id=st.session_state.usuario_id)
                ]
                idx = st.session_state.get("simulado_idx", 0)
                idx = max(0, min(idx, len(ids) - 1))

                itens = db.listar_itens_simulado(simulado_id, usuario_id=st.session_state.usuario_id)
                respostas_dadas = {i["id"]: i["resposta_dada"] for i in itens}

                minutos, segundos = divmod(int(restante_seg), 60)
                if restante_seg < 60:
                    cor_tempo = "#DC2626"
                elif restante_seg < limite_seg * 0.1:
                    cor_tempo = "#D97706"
                else:
                    cor_tempo = "#16A34A"
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.markdown(
                        f'<div class="metric-badge" style="--mb-cor:{cor_tempo};">'
                        f'<span class="metric-badge-label" style="display:flex;align-items:center;gap:0.4rem;">'
                        f'{ui.icon_svg("timer", size=15)} Tempo restante</span>'
                        f'<span class="metric-badge-value">{minutos:02d}:{segundos:02d}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                col2.progress((idx + 1) / len(ids))
                col2.caption(f"Questão {idx + 1} de {len(ids)}")

                q = db.obter_questao(ids[idx])
                alternativas_atuais = json.loads(q["alternativas"])
                opcoes = list(alternativas_atuais.keys())
                resposta_atual = respostas_dadas.get(q["id"])
                resposta = ui.render_questao(
                    q, modo="interativa",
                    key=f"sim_resp_{simulado_id}_{q['id']}",
                    index_pre_selecionado=opcoes.index(resposta_atual) if resposta_atual in opcoes else None,
                )
                if resposta is not None:
                    db.registrar_resposta_simulado(
                        simulado_id, q["id"], resposta, usuario_id=st.session_state.usuario_id,
                    )

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button("Anterior", icon=":material/arrow_back:", disabled=idx <= 0):
                        st.session_state.simulado_idx = idx - 1
                        st.rerun()
                with col_b:
                    ir_para = st.selectbox(
                        "Ir para questão",
                        options=list(range(len(ids))),
                        index=idx,
                        format_func=lambda i: f"{i + 1} — respondida" if respostas_dadas.get(ids[i]) else f"{i + 1} — em branco",
                        key=f"sim_nav_{simulado_id}_{idx}",
                    )
                    if ir_para != idx:
                        st.session_state.simulado_idx = ir_para
                        st.rerun()
                with col_c:
                    if st.button("Próxima", icon=":material/arrow_forward:", disabled=idx >= len(ids) - 1):
                        st.session_state.simulado_idx = idx + 1
                        st.rerun()

                st.markdown("---")
                if st.button("Finalizar Simulado", icon=":material/flag:"):
                    db.finalizar_simulado(simulado_id, usuario_id=st.session_state.usuario_id)
                    consolidar_simulado_no_historico(simulado_id, st.session_state.usuario_id)
                    st.rerun()

# ---------------------------------------------------------------------------
# CADASTRAR QUESTÃO
# ---------------------------------------------------------------------------
elif pagina == "Nova Questão":
    ui.page_header("square-plus", "Cadastrar Nova Questão")

    with st.expander("Cadastrar nova área ou subtópico", icon=":material/add_circle:"):
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

    st.markdown("---")

    with st.container(border=True):
        if _form_questao(None, key_prefix="novaq") == "salvo":
            st.rerun()

# ---------------------------------------------------------------------------
# IMPORTAR QUESTÕES EM MASSA (PLANILHA)
# ---------------------------------------------------------------------------
elif pagina == "Importar Planilha":
    ui.page_header("file-up", "Importar Questões em Massa")
    st.caption(
        "Importe centenas de questões de uma vez a partir de uma planilha "
        "Excel (.xlsx) ou CSV, em vez de cadastrar uma por uma."
    )

    st.download_button(
        "Baixar planilha modelo (.xlsx)",
        icon=":material/download:",
        data=imp_q.gerar_template_bytes(),
        file_name="modelo_importacao_questoes.xlsx",
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

        Variações como "Área", "Assunto", "Gabarito" também são
        reconhecidas automaticamente. Questões com enunciado idêntico
        já cadastrado na mesma área são ignoradas (não duplicam).
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
                st.dataframe(df.head(10), use_container_width=True, hide_index=True)

                if st.button("Importar todas as questões", icon=":material/upload_file:"):
                    with st.spinner("Importando..."):
                        relatorio = imp_q.importar(df)

                    st.success("Importação concluída!", icon=":material/check_circle:")
                    col_imp, col_dup, col_tot = st.columns(3)
                    col_imp.metric("Importadas", relatorio["importadas"])
                    col_dup.metric("Duplicadas (ignoradas)", relatorio["duplicadas"])
                    col_tot.metric("Total na planilha", relatorio["total"])
                    if relatorio["erros"]:
                        st.warning(f"{len(relatorio['erros'])} linha(s) com problema:", icon=":material/warning:")
                        df_erros = pd.DataFrame(relatorio["erros"], columns=["Linha", "Motivo"])
                        st.dataframe(df_erros, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# REVISÃO (REPETIÇÃO ESPAÇADA)
# ---------------------------------------------------------------------------
elif pagina == "Revisão Espaçada":
    ui.page_header("brain", "Revisão por Repetição Espaçada")
    st.caption(
        "Questões que você errou voltam mais rápido; as que você domina "
        "voltam com intervalos cada vez maiores (algoritmo estilo Anki/SM-2)."
    )

    pendentes = sr.questoes_para_revisar_hoje(usuario_id=st.session_state.usuario_id)
    novas = sr.questoes_nunca_revisadas(usuario_id=st.session_state.usuario_id)

    col_pend, col_novas = st.columns(2)
    col_pend.metric("Para revisar hoje", len(pendentes))
    col_novas.metric("Ainda sem revisão agendada", len(novas))

    fila = list(pendentes) + list(novas)

    if "rev_idx" not in st.session_state:
        st.session_state.rev_idx = 0

    if st.button("Recomeçar fila de revisão", icon=":material/restart_alt:"):
        st.session_state.rev_idx = 0

    if not fila:
        ui.empty_state(
            "Tudo em dia por aqui!",
            "Nenhuma questão pendente de revisão. Responda questões novas em "
            "'Praticar' para alimentar a fila.",
            icon="circle-check",
            cta_label="Ir para Praticar", cta_icon=":material/arrow_forward:",
            cta_pagina="Praticar",
        )
    elif st.session_state.rev_idx >= len(fila):
        st.success("Fila de revisão concluída por hoje!", icon=":material/celebration:")
    else:
        q = fila[st.session_state.rev_idx]
        resposta = ui.render_questao(
            q, modo="interativa",
            key=f"rev_resp_{q['id']}_{st.session_state.rev_idx}",
        )

        # Fluxo em 2 passos: (1) confirmar resposta certa/errada; só DEPOIS
        # (2) mostrar o slider de qualidade e registrar a revisão. Antes,
        # o slider era criado E lido no mesmo clique de "Confirmar" — o
        # usuário nunca tinha chance de mexer nele antes do valor (sempre
        # o default 4) ser gravado; o SM-2 nunca recebia a nota real.
        aguardando = st.session_state.get("rev_aguardando")

        if aguardando is None:
            if st.button(
                "Confirmar", key=f"rev_conf_{q['id']}_{st.session_state.rev_idx}",
                icon=":material/check:", disabled=resposta is None,
            ):
                correta = (resposta == q["resposta_correta"])
                db.registrar_resposta(q["id"], resposta, correta, usuario_id=st.session_state.usuario_id)
                st.session_state.rev_aguardando = {"correta": correta}
                st.rerun()
        else:
            correta = aguardando["correta"]
            if correta:
                st.success("Correto!", icon=":material/check_circle:")
                qualidade = st.slider(
                    "Quão fácil foi lembrar? (afeta o próximo intervalo)",
                    0, 5, 4, key=f"qual_{q['id']}_{st.session_state.rev_idx}",
                )
            else:
                st.error(f"Errado. Resposta correta: {q['resposta_correta']}", icon=":material/cancel:")
                qualidade = 1

            if st.button(
                "Registrar e continuar", key=f"rev_prox_{q['id']}_{st.session_state.rev_idx}",
                icon=":material/arrow_forward:",
            ):
                sr.registrar_revisao(q["id"], qualidade, usuario_id=st.session_state.usuario_id)
                st.session_state.pop("rev_aguardando", None)
                st.session_state.rev_idx += 1
                st.rerun()

# ---------------------------------------------------------------------------
# MATERIAIS DE ESTUDO (MediaFire)
# ---------------------------------------------------------------------------
elif pagina == "Materiais de Estudo":
    ui.page_header("book-open", "Materiais de Estudo (MediaFire)")
    st.caption(
        "Organize aqui os links da sua pasta compartilhada do MediaFire, "
        "por área, subtópico e tipo de material."
    )

    total_mat_atual = db.contar_materiais()
    if total_mat_atual and eh_admin:
        with st.expander("Zona de risco (admin)", icon=":material/warning:"):
            st.write(
                f"Isso apaga permanentemente **{total_mat_atual}** material(is) "
                "cadastrados, para **todos os usuários** da plataforma. Não tem como desfazer."
            )
            confirmar_excluir_todos = st.checkbox(
                f"Sim, quero excluir todos os {total_mat_atual} materiais cadastrados",
                key="confirmar_excluir_todos_materiais",
            )
            if st.button(
                "Excluir todos os materiais",
                icon=":material/delete_forever:",
                disabled=not confirmar_excluir_todos,
            ):
                db.excluir_todos_materiais()
                st.session_state.pop("confirmar_excluir_todos_materiais", None)
                st.success("Todos os materiais foram excluídos.", icon=":material/check_circle:")
                st.rerun()

    areas = mapa_areas()
    if not areas:
        ui.empty_state(
            "Nenhuma área cadastrada ainda",
            "Cadastre uma área (ex: Cardiologia) antes de adicionar materiais.",
            icon="square-plus", cta_label="Ir para Nova Questão",
            cta_icon=":material/arrow_forward:", cta_pagina="Nova Questão",
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
                "Tipo de material",
                ["Apostila", "Videoaula", "Vídeo Bônus", "Vídeo Apostila", "Outro"],
            )
            col_titulo, col_link = st.columns(2)
            titulo = col_titulo.text_input("Título do material")
            link = col_link.text_input("Link do MediaFire")

            if st.button("Salvar material", icon=":material/save:"):
                if titulo.strip() and link.strip():
                    db.criar_material(area_id, subtopico_id, tipo, titulo, link)
                    st.success("Material adicionado!", icon=":material/check_circle:")
                    st.rerun()
                else:
                    st.error("Preencha título e link.", icon=":material/cancel:")

        st.markdown("---")
        st.subheader("Buscar materiais")

        with st.container(border=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                area_filtro = st.selectbox("Área", ["Todas"] + list(areas.keys()), key="mat_filtro_area")
                area_id_filtro = areas[area_filtro] if area_filtro != "Todas" else None
            with col2:
                sub_opcoes_filtro = {"Todos": None}
                if area_id_filtro:
                    sub_opcoes_filtro.update({s["nome"]: s["id"] for s in db.listar_subtopicos(area_id_filtro)})
                sub_filtro_nome = st.selectbox("Subtópico", list(sub_opcoes_filtro.keys()), key="mat_filtro_sub")
                subtopico_id_filtro = sub_opcoes_filtro[sub_filtro_nome]
            with col3:
                tipos_disponiveis = db.listar_tipos_materiais()
                tipo_filtro = st.selectbox("Tipo", ["Todos"] + tipos_disponiveis, key="mat_filtro_tipo")
                tipo_filtro = None if tipo_filtro == "Todos" else tipo_filtro

            busca = st.text_input("Buscar por título (opcional)", key="mat_busca")

        # zera a paginação sempre que algum filtro muda
        assinatura = (area_id_filtro, subtopico_id_filtro, tipo_filtro, busca)
        resetar_paginacao_se_filtro_mudou("mat_pagina", assinatura)

        total = db.contar_materiais_filtrados(area_id_filtro, subtopico_id_filtro, tipo_filtro, busca)

        if total == 0:
            ui.empty_state(
                "Nenhum material encontrado",
                "Tente ajustar os filtros acima, ou adicione um novo material.",
            )
        else:
            POR_PAGINA = 50
            _, offset = controle_paginacao("mat_pagina", total, POR_PAGINA)
            materiais = db.listar_materiais_paginado(
                area_id_filtro, subtopico_id_filtro, tipo_filtro, busca,
                limite=POR_PAGINA, offset=offset,
            )

            ICONE_TIPO = {
                "Apostila": ":material/description:",
                "Videoaula": ":material/play_circle:",
                "Vídeo Bônus": ":material/play_circle:",
                "Vídeo Apostila": ":material/play_circle:",
            }

            df_mat = pd.DataFrame([dict(m) for m in materiais])
            for tipo, grupo in df_mat.groupby("tipo", sort=False):
                icone = ICONE_TIPO.get(tipo, ":material/insert_drive_file:")
                with st.container(border=True):
                    st.markdown(f"{icone} **{tipo}** &nbsp;·&nbsp; {len(grupo)} material(is)")
                    linhas = list(grupo.iterrows())
                    for i, (_, m) in enumerate(linhas):
                        col1, col2, col3 = st.columns([5, 1, 1])
                        col1.write(m["titulo"])
                        col2.link_button(
                            "Abrir", m["link_mediafire"], icon=":material/open_in_new:",
                            key=f"mat_link_{m['id']}", use_container_width=True,
                        )
                        if eh_admin and col3.button(
                            "", icon=":material/delete_forever:", key=f"mat_del_{m['id']}",
                            help="Excluir material", use_container_width=True,
                        ):
                            ui.confirmar_exclusao(
                                f"Excluir o material **{m['titulo']}**? Ele some do "
                                "acervo compartilhado pra todos os usuários. Essa ação "
                                "não pode ser desfeita.",
                                lambda mid=int(m["id"]): db.excluir_material(mid),
                            )
                        if i < len(linhas) - 1:
                            st.markdown(
                                "<hr style='margin:0.2rem 0; border-color:#D7E3E2;'>",
                                unsafe_allow_html=True,
                            )

# ---------------------------------------------------------------------------
# SINCRONIZAR MEDIAFIRE (importação em massa dos materiais)
# ---------------------------------------------------------------------------
elif pagina == "Sincronizar MediaFire":
    ui.page_header("folder-sync", "Sincronizar Pasta do MediaFire")
    st.caption(
        "Cole o link da sua pasta raiz compartilhada do MediaFire. O app vai "
        "varrer automaticamente todas as subpastas (áreas → assuntos → "
        "arquivos) e cadastrar tudo como material de estudo — sem precisar "
        "adicionar link por link."
    )

    with st.expander("Estrutura esperada da pasta", icon=":material/info:"):
        st.markdown(
            "Pasta raiz → pastas de área (ex: Cardiologia, Cirurgia, "
            "Dermatologia) → pastas de assunto → apostilas/vídeos (ou "
            "subpastas extras tipo 'Apostilas'/'Videoaulas' dentro do "
            "assunto, que também são lidas). Funciona apenas com pastas "
            "compartilhadas publicamente (aquelas com link "
            "`mediafire.com/folder/...`) e requer conexão com a internet."
        )

    link_raiz = st.text_input(
        "Link (ou chave) da pasta raiz do MediaFire",
        placeholder="https://www.mediafire.com/folder/xxxxxxxxxxxxx/NomeDaPasta",
    )

    if st.button("Sincronizar agora", icon=":material/sync:", disabled=not link_raiz.strip()):
        status_area = st.empty()
        log_linhas = []

        def _progresso(msg):
            log_linhas.append(msg)
            # mostra só as últimas linhas para não poluir a tela
            status_area.text("\n".join(log_linhas[-8:]))

        try:
            with st.spinner("Varrendo a pasta do MediaFire... isso pode levar alguns minutos."):
                relatorio = mf.sincronizar_pasta_raiz(link_raiz, on_progress=_progresso)
        except mf.MediaFireError as e:
            st.error(f"Erro ao sincronizar: {e}", icon=":material/cancel:")
        else:
            status_area.empty()
            st.success("Sincronização concluída!", icon=":material/check_circle:")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Áreas", relatorio["areas_criadas"])
            col2.metric("Assuntos", relatorio["subtopicos_criados"])
            col3.metric("Materiais novos", relatorio["materiais_novos"])
            col4.metric("Já existiam", relatorio["materiais_duplicados"])

            if relatorio["erros"]:
                with st.expander(f"{len(relatorio['erros'])} aviso(s)/erro(s)", icon=":material/warning:"):
                    df_erros_mf = pd.DataFrame({"Aviso": relatorio["erros"]})
                    st.dataframe(df_erros_mf, use_container_width=True, hide_index=True)

            st.caption(
                "Pode rodar a sincronização de novo sempre que adicionar arquivos "
                "novos na pasta — os que já foram importados não duplicam."
            )

# ---------------------------------------------------------------------------
# BANCO DE QUESTÕES (listagem / gestão)
# ---------------------------------------------------------------------------
elif pagina == "Banco de Questões":
    ui.page_header("database", "Banco de Questões")

    areas = mapa_areas()
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            area_nome = st.selectbox("Filtrar por área", ["Todas"] + list(areas.keys()), key="bq_area")
            area_id = areas[area_nome] if area_nome != "Todas" else None
        with col2:
            busca = st.text_input("Buscar no enunciado (opcional)", key="bq_busca")

    resetar_paginacao_se_filtro_mudou("bq_pagina", (area_id, busca))

    total = db.contar_questoes_filtradas(area_id=area_id, busca=busca)

    if total == 0:
        ui.empty_state(
            "Nenhuma questão encontrada",
            "Tente ajustar os filtros acima, ou cadastre uma nova questão.",
            cta_label="Ir para Nova Questão", cta_icon=":material/arrow_forward:",
            cta_pagina="Nova Questão",
        )
    else:
        POR_PAGINA = 50
        _, offset = controle_paginacao("bq_pagina", total, POR_PAGINA)
        questoes = db.listar_questoes_paginado(area_id=area_id, busca=busca, limite=POR_PAGINA, offset=offset)

        for q in questoes:
            rotulo = f"{q['enunciado'][:80]}...  ·  {q['banca'] or 'Banca não informada'} · {q['ano'] or '-'}"
            with st.expander(rotulo, icon=":material/quiz:"):
                ui.render_questao(q, modo="leitura")
                if q["explicacao"]:
                    st.info(q["explicacao"], icon=":material/lightbulb:")
                else:
                    st.caption(":material/info: Sem explicação cadastrada ainda.")

                col_edit, col_del = st.columns(2)
                if eh_admin and col_edit.button("Editar questão", icon=":material/edit:", key=f"editar_{q['id']}"):
                    _dialog_editar_questao(q)
                if eh_admin and col_del.button("Excluir questão", icon=":material/delete:", key=f"del_{q['id']}"):
                    ui.confirmar_exclusao(
                        f"Excluir a questão **#{q['id']}**? O histórico de respostas e "
                        "revisões associado a ela deixa de fazer sentido. Essa ação não "
                        "pode ser desfeita.",
                        lambda qid=q["id"]: db.excluir_questao(qid),
                    )
