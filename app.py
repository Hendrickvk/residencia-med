import streamlit as st
import pandas as pd
import json
import random
import datetime

import db
import repeticao_espacada as sr
import importador_questoes as imp_q
import mediafire_import as mf
import mediafire_cache as mfc
import auth
import ui

st.set_page_config(
    page_title="Residência Med - Plataforma de Estudos",
    page_icon="🩺",
    layout="wide",
)
ui.inject_custom_css()

db.init_db()

if "usuario_id" not in st.session_state:
    auth.render_login_signup()
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar / navegação
# ---------------------------------------------------------------------------
st.sidebar.markdown(
    f"""
    <div style="display:flex; align-items:center; gap:0.6rem; padding: 0.2rem 0 1rem 0; color:#2DD4BF;">
        {ui.icon_svg("stethoscope", size=22)}
        <span style="font-size:1.25rem; font-weight:700; color:#E2E8F0;">Residência Med</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.caption(f"Logado como: {st.session_state.get('usuario_email', '')}")
if st.sidebar.button("Sair", use_container_width=True, icon=":material/logout:"):
    for chave in ("usuario_id", "usuario_email"):
        st.session_state.pop(chave, None)
    st.rerun()
st.sidebar.markdown("---")
pagina = st.sidebar.radio(
    "Navegação",
    ["Dashboard", "Responder Questões", "Simulado", "Cadastrar Questão",
     "Importar Questões (planilha)", "Revisão (Repetição Espaçada)",
     "Materiais de Estudo", "Sincronizar MediaFire", "Banco de Questões"],
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.caption(f"Total de questões cadastradas: **{db.contar_questoes()}**")
st.sidebar.caption(f"Total de materiais cadastrados: **{db.contar_materiais()}**")


def mapa_areas():
    return {a["nome"]: a["id"] for a in db.listar_areas()}


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


def consolidar_simulado_no_historico(simulado_id, usuario_id):
    """Joga as respostas do simulado nos mesmos caminhos usados por
    'Responder Questões' (db.registrar_resposta + sr.registrar_revisao),
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

    desemp_area = db.desempenho_por_area(usuario_id=st.session_state.usuario_id)
    if not desemp_area:
        st.info("Ainda não há respostas registradas. Vá em **Responder Questões** para começar.")
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
        st.bar_chart(df_area.set_index("area")["pct_acerto"])

        st.subheader("Áreas com mais erros (prioridade de revisão)")
        piores = df_area.sort_values("pct_acerto").head(5)
        for _, row in piores.iterrows():
            st.write(
                f":material/priority_high: **{row['area']}** — {row['pct_acerto']}% de acerto "
                f"({int(row['acertos'])}/{int(row['total'])})"
            )

        st.subheader("Evolução diária")
        evol = db.evolucao_diaria(usuario_id=st.session_state.usuario_id)
        if evol:
            df_evol = pd.DataFrame([dict(r) for r in evol]).set_index("dia")
            st.line_chart(df_evol[["pct_acerto"]])
            st.bar_chart(df_evol[["total"]])

        st.subheader("Desempenho por banca / instituição")
        desemp_banca = db.desempenho_por_banca(usuario_id=st.session_state.usuario_id)
        if not desemp_banca:
            st.caption(
                "Nenhuma resposta registrada em questões com banca definida "
                "ainda. Preencha o campo 'Banca' ao cadastrar ou importar "
                "questões para acompanhar esse comparativo."
            )
        else:
            df_banca = pd.DataFrame([dict(r) for r in desemp_banca])
            st.bar_chart(df_banca.set_index("banca")["pct_acerto"])

            sem_banca = db.contar_respostas_sem_banca(usuario_id=st.session_state.usuario_id)
            if sem_banca:
                st.caption(
                    f":material/info: {sem_banca} resposta(s) de questões sem banca definida "
                    "não entram nessa comparação."
                )

            with st.expander("Comparar bancas por área", icon=":material/table_chart:"):
                desemp_banca_area = db.desempenho_por_banca_e_area(usuario_id=st.session_state.usuario_id)
                df_ba = pd.DataFrame([dict(r) for r in desemp_banca_area])
                pivot = df_ba.pivot_table(index="area", columns="banca", values="pct_acerto")
                pivot_fmt = pivot.map(lambda v: f"{v:.1f}%" if pd.notna(v) else "—")
                st.caption("% de acerto por área, banca a banca ('—' = sem respostas dessa combinação).")
                st.dataframe(pivot_fmt, use_container_width=True)

        with st.expander("Desempenho por subtópico", icon=":material/insights:"):
            desemp_sub = db.desempenho_por_subtopico(usuario_id=st.session_state.usuario_id)
            if desemp_sub:
                df_sub = pd.DataFrame([dict(r) for r in desemp_sub])
                st.dataframe(df_sub, use_container_width=True, hide_index=True)

        with st.expander("Questões mais erradas", icon=":material/error:"):
            piores_q = db.questoes_mais_erradas(usuario_id=st.session_state.usuario_id)
            if piores_q:
                df_q = pd.DataFrame([dict(r) for r in piores_q])
                st.dataframe(
                    df_q[["area", "enunciado", "total_respostas", "erros", "pct_erro"]],
                    use_container_width=True, hide_index=True,
                )

# ---------------------------------------------------------------------------
# RESPONDER QUESTÕES
# ---------------------------------------------------------------------------
elif pagina == "Responder Questões":
    ui.page_header("pencil-line", "Responder Questões")

    areas = mapa_areas()
    if not areas:
        st.warning("Cadastre uma área primeiro.")
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

        fila = st.session_state.get("fila_questoes", [])
        idx = st.session_state.get("idx_atual", 0)

        if not fila:
            st.info("Nenhuma questão encontrada para esse filtro. Cadastre questões primeiro.")
        elif idx >= len(fila):
            st.success("Você respondeu todas as questões desse lote! Gere um novo lote acima.")
        else:
            q = db.obter_questao(fila[idx])
            st.progress((idx) / len(fila))
            st.caption(f"Questão {idx + 1} de {len(fila)}")
            st.markdown(f"### {q['enunciado']}")

            alternativas = json.loads(q["alternativas"])
            resposta = st.radio(
                "Alternativas",
                options=list(alternativas.keys()),
                format_func=lambda k: f"{k}) {alternativas[k]}",
                key=f"resp_{q['id']}",
            )

            if st.button("Confirmar resposta", key=f"conf_{q['id']}", icon=":material/check:"):
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
            bancas = db.listar_bancas()
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
                st.bar_chart(df_desemp.set_index("area")["pct_acerto"])

            st.subheader("Revisão completa")
            itens = db.listar_itens_simulado(simulado_id, usuario_id=st.session_state.usuario_id)
            for item in itens:
                alternativas = json.loads(item["alternativas"])
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
                    st.markdown(item["enunciado"])
                    for letra, texto in alternativas.items():
                        prefixo = ":material/check_circle:" if letra == item["resposta_correta"] else ":material/radio_button_unchecked:"
                        sufixo = " (sua resposta)" if letra == item["resposta_dada"] else ""
                        st.write(f"{prefixo} **{letra})** {texto}{sufixo}")
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
                cor = "🔴" if restante_seg < 60 else ("🟡" if restante_seg < limite_seg * 0.1 else "🟢")
                col1, col2 = st.columns([1, 3])
                col1.metric("Tempo restante", f"{cor} {minutos:02d}:{segundos:02d}")
                col2.progress((idx + 1) / len(ids))
                col2.caption(f"Questão {idx + 1} de {len(ids)}")

                q = db.obter_questao(ids[idx])
                st.markdown(f"### {q['enunciado']}")

                alternativas = json.loads(q["alternativas"])
                opcoes = list(alternativas.keys())
                resposta_atual = respostas_dadas.get(q["id"])
                resposta = st.radio(
                    "Alternativas",
                    options=opcoes,
                    index=opcoes.index(resposta_atual) if resposta_atual in opcoes else None,
                    format_func=lambda k: f"{k}) {alternativas[k]}",
                    key=f"sim_resp_{simulado_id}_{q['id']}",
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
                    respondidas_marcador = ["✅" if respostas_dadas.get(qid) else "◻️" for qid in ids]
                    ir_para = st.selectbox(
                        "Ir para questão",
                        options=list(range(len(ids))),
                        index=idx,
                        format_func=lambda i: f"{i + 1} {respondidas_marcador[i]}",
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
elif pagina == "Cadastrar Questão":
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

    areas = mapa_areas()
    if not areas:
        st.warning("Cadastre uma área acima antes de criar questões.")
    else:
        area_nome = st.selectbox("Área", list(areas.keys()))
        area_id = areas[area_nome]

        subtopicos = db.listar_subtopicos(area_id)
        sub_opcoes = {"(nenhum)": None}
        sub_opcoes.update({s["nome"]: s["id"] for s in subtopicos})
        sub_nome = st.selectbox("Subtópico", list(sub_opcoes.keys()))
        subtopico_id = sub_opcoes[sub_nome]

        enunciado = st.text_area("Enunciado da questão")

        st.write("Alternativas")
        alt_a = st.text_input("A)")
        alt_b = st.text_input("B)")
        alt_c = st.text_input("C)")
        alt_d = st.text_input("D)")
        alt_e = st.text_input("E) (opcional)")

        resposta_correta = st.selectbox("Alternativa correta", ["A", "B", "C", "D", "E"])
        explicacao = st.text_area("Explicação / comentário (opcional)")
        col1, col2 = st.columns(2)
        banca = col1.text_input("Banca / Instituição (ex: ENAMED, USP-SP, UNIFESP)")
        ano = col2.number_input("Ano", min_value=1990, max_value=2100, value=2025, step=1)

        if st.button("Salvar questão", icon=":material/save:"):
            alternativas = {"A": alt_a, "B": alt_b, "C": alt_c, "D": alt_d}
            if alt_e.strip():
                alternativas["E"] = alt_e

            if not enunciado.strip() or not all([alt_a, alt_b, alt_c, alt_d]):
                st.error("Preencha ao menos o enunciado e as alternativas A a D.", icon=":material/cancel:")
            else:
                db.criar_questao(
                    area_id, subtopico_id, enunciado, alternativas,
                    resposta_correta, explicacao, banca, int(ano),
                )
                st.success("Questão cadastrada com sucesso!", icon=":material/check_circle:")
                st.rerun()

# ---------------------------------------------------------------------------
# IMPORTAR QUESTÕES EM MASSA (PLANILHA)
# ---------------------------------------------------------------------------
elif pagina == "Importar Questões (planilha)":
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

                    st.success(
                        f"Concluído! {relatorio['importadas']} questão(ões) importada(s), "
                        f"{relatorio['duplicadas']} duplicada(s) ignorada(s), "
                        f"de {relatorio['total']} linha(s) na planilha.",
                        icon=":material/check_circle:",
                    )
                    if relatorio["erros"]:
                        st.warning(f"{len(relatorio['erros'])} linha(s) com problema:", icon=":material/warning:")
                        df_erros = pd.DataFrame(relatorio["erros"], columns=["Linha", "Motivo"])
                        st.dataframe(df_erros, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# REVISÃO (REPETIÇÃO ESPAÇADA)
# ---------------------------------------------------------------------------
elif pagina == "Revisão (Repetição Espaçada)":
    ui.page_header("brain", "Revisão por Repetição Espaçada")
    st.caption(
        "Questões que você errou voltam mais rápido; as que você domina "
        "voltam com intervalos cada vez maiores (algoritmo estilo Anki/SM-2)."
    )

    pendentes = sr.questoes_para_revisar_hoje(usuario_id=st.session_state.usuario_id)
    novas = sr.questoes_nunca_revisadas(usuario_id=st.session_state.usuario_id)

    st.write(
        f":material/event: **{len(pendentes)}** questões para revisar hoje | "
        f":material/fiber_new: **{len(novas)}** ainda sem revisão agendada"
    )

    fila = list(pendentes) + list(novas)

    if "rev_idx" not in st.session_state:
        st.session_state.rev_idx = 0

    if st.button("Recomeçar fila de revisão", icon=":material/restart_alt:"):
        st.session_state.rev_idx = 0

    if not fila:
        st.info("Nenhuma questão pendente de revisão. Responda questões novas para alimentar a fila.")
    elif st.session_state.rev_idx >= len(fila):
        st.success("Fila de revisão concluída por hoje!", icon=":material/celebration:")
    else:
        q = fila[st.session_state.rev_idx]
        st.markdown(f"### {q['enunciado']}")
        alternativas = json.loads(q["alternativas"])
        resposta = st.radio(
            "Alternativas",
            options=list(alternativas.keys()),
            format_func=lambda k: f"{k}) {alternativas[k]}",
            key=f"rev_resp_{q['id']}_{st.session_state.rev_idx}",
        )

        if st.button("Confirmar", key=f"rev_conf_{q['id']}_{st.session_state.rev_idx}", icon=":material/check:"):
            correta = (resposta == q["resposta_correta"])
            db.registrar_resposta(q["id"], resposta, correta, usuario_id=st.session_state.usuario_id)
            if correta:
                st.success("Correto!", icon=":material/check_circle:")
                qualidade = st.slider(
                    "Quão fácil foi lembrar? (afeta o próximo intervalo)",
                    0, 5, 4, key=f"qual_{q['id']}_{st.session_state.rev_idx}",
                )
            else:
                st.error(f"Errado. Resposta correta: {q['resposta_correta']}", icon=":material/cancel:")
                qualidade = 1

            sr.registrar_revisao(q["id"], qualidade, usuario_id=st.session_state.usuario_id)
            st.session_state.rev_idx += 1
            st.rerun()

# ---------------------------------------------------------------------------
# MATERIAIS DE ESTUDO (MediaFire)
# ---------------------------------------------------------------------------
elif pagina == "Materiais de Estudo":
    ui.page_header("book-open", "Materiais de Estudo (MediaFire)")
    st.caption(
        "Organize aqui os links da sua pasta compartilhada do MediaFire, "
        "por área, subtópico e tipo de material. Cada material pode ser "
        "baixado para um cache local (útil para acessar offline) — o "
        "download é sempre por sua conta, um material de cada vez, já que "
        "vídeos podem ser grandes."
    )

    areas = mapa_areas()
    if not areas:
        st.warning("Cadastre uma área primeiro (na página 'Cadastrar Questão').")
    else:
        with st.expander("Adicionar novo material", icon=":material/add_circle:"):
            area_nome = st.selectbox("Área", list(areas.keys()), key="mat_area")
            area_id = areas[area_nome]
            subtopicos = db.listar_subtopicos(area_id)
            sub_opcoes = {"(nenhum)": None}
            sub_opcoes.update({s["nome"]: s["id"] for s in subtopicos})
            sub_nome = st.selectbox("Subtópico", list(sub_opcoes.keys()), key="mat_sub")
            subtopico_id = sub_opcoes[sub_nome]

            tipo = st.selectbox(
                "Tipo de material",
                ["Apostila", "Videoaula", "Vídeo Bônus", "Vídeo Apostila", "Outro"],
            )
            titulo = st.text_input("Título do material")
            link = st.text_input("Link do MediaFire")

            if st.button("Salvar material", icon=":material/save:"):
                if titulo.strip() and link.strip():
                    db.criar_material(area_id, subtopico_id, tipo, titulo, link)
                    st.success("Material adicionado!", icon=":material/check_circle:")
                    st.rerun()
                else:
                    st.error("Preencha título e link.", icon=":material/cancel:")

        st.markdown("---")
        st.subheader("Buscar materiais")

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
            st.info("Nenhum material encontrado para esse filtro.")
        else:
            POR_PAGINA = 50
            _, offset = controle_paginacao("mat_pagina", total, POR_PAGINA)
            materiais = db.listar_materiais_paginado(
                area_id_filtro, subtopico_id_filtro, tipo_filtro, busca,
                limite=POR_PAGINA, offset=offset,
            )

            cache_n, cache_bytes = db.estatisticas_cache()
            if cache_n:
                st.caption(
                    f":material/save: {cache_n} material(is) em cache local, ocupando "
                    f"{mfc.formatar_tamanho(cache_bytes)} em disco."
                )

            df_mat = pd.DataFrame([dict(m) for m in materiais])
            for tipo, grupo in df_mat.groupby("tipo", sort=False):
                st.markdown(f"**{tipo}**")
                for _, m in grupo.iterrows():
                    col1, col2, col3, col4 = st.columns([3, 1, 1.8, 1])
                    col1.write(m["titulo"])
                    col2.link_button("Abrir", m["link_mediafire"], icon=":material/open_in_new:", key=f"mat_link_{m['id']}")

                    if mfc.esta_em_cache(m):
                        col3.caption(f":material/check_circle: Em cache ({mfc.formatar_tamanho(m['tamanho_bytes'])})")
                        if col4.button("", icon=":material/delete:", key=f"mat_rmcache_{m['id']}", help="Remover do cache local"):
                            mfc.remover_cache(int(m["id"]))
                            st.rerun()
                    else:
                        if col3.button("Baixar para cache", icon=":material/download:", key=f"mat_baixar_{m['id']}"):
                            try:
                                with st.spinner(f"Baixando '{m['titulo']}'... isso pode demorar se for um vídeo."):
                                    mfc.baixar_material(int(m["id"]))
                                st.rerun()
                            except mfc.CacheError as e:
                                st.error(f"Não consegui baixar: {e}", icon=":material/cancel:")

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

    st.info(
        "**Estrutura esperada:** Pasta raiz → pastas de área (ex: Cardiologia, "
        "Cirurgia, Dermatologia) → pastas de assunto → apostilas/vídeos "
        "(ou subpastas extras tipo 'Apostilas'/'Videoaulas' dentro do assunto, "
        "que também são lidas). Funciona apenas com pastas compartilhadas "
        "publicamente (aquelas com link `mediafire.com/folder/...`) e requer "
        "conexão com a internet."
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
                    for erro in relatorio["erros"]:
                        st.write(f"- {erro}")

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
    col1, col2 = st.columns(2)
    with col1:
        area_nome = st.selectbox("Filtrar por área", ["Todas"] + list(areas.keys()), key="bq_area")
        area_id = areas[area_nome] if area_nome != "Todas" else None
    with col2:
        busca = st.text_input("Buscar no enunciado (opcional)", key="bq_busca")

    resetar_paginacao_se_filtro_mudou("bq_pagina", (area_id, busca))

    total = db.contar_questoes_filtradas(area_id=area_id, busca=busca)

    if total == 0:
        st.info("Nenhuma questão encontrada para esse filtro.")
    else:
        POR_PAGINA = 50
        _, offset = controle_paginacao("bq_pagina", total, POR_PAGINA)
        questoes = db.listar_questoes_paginado(area_id=area_id, busca=busca, limite=POR_PAGINA, offset=offset)

        for q in questoes:
            with st.expander(f"[{q['id']}] {q['enunciado'][:80]}..."):
                alternativas = json.loads(q["alternativas"])
                for letra, texto in alternativas.items():
                    marcador = ":material/check_circle:" if letra == q["resposta_correta"] else ":material/radio_button_unchecked:"
                    st.write(f"{marcador} **{letra})** {texto}")
                if q["explicacao"]:
                    st.info(q["explicacao"], icon=":material/lightbulb:")
                st.caption(f"Banca: {q['banca'] or '-'} | Ano: {q['ano'] or '-'}")
                if st.button("Excluir questão", icon=":material/delete:", key=f"del_{q['id']}"):
                    db.excluir_questao(q["id"])
                    st.rerun()
