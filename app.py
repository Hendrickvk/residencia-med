import streamlit as st
import pandas as pd
import json
import random

import db
import repeticao_espacada as sr
import importador_questoes as imp_q
import mediafire_import as mf

st.set_page_config(
    page_title="Residência Med - Plataforma de Estudos",
    page_icon="🩺",
    layout="wide",
)

db.init_db()

# ---------------------------------------------------------------------------
# Sidebar / navegação
# ---------------------------------------------------------------------------
st.sidebar.title("🩺 Residência Med")
pagina = st.sidebar.radio(
    "Navegação",
    ["Dashboard", "Responder Questões", "Cadastrar Questão",
     "Importar Questões (planilha)", "Revisão (Repetição Espaçada)",
     "Materiais de Estudo", "Sincronizar MediaFire", "Banco de Questões"],
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
        if st.button("⬅️ Anterior", key=f"{chave}_prev", disabled=st.session_state[chave] <= 0):
            st.session_state[chave] -= 1
            st.rerun()
    with col2:
        st.markdown(
            f"<div style='text-align:center'>Página {st.session_state[chave] + 1} "
            f"de {total_paginas} — {total} resultado(s)</div>",
            unsafe_allow_html=True,
        )
    with col3:
        if st.button("Próxima ➡️", key=f"{chave}_next", disabled=st.session_state[chave] >= total_paginas - 1):
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


# ---------------------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------------------
if pagina == "Dashboard":
    st.title("📊 Dashboard de Desempenho")

    desemp_area = db.desempenho_por_area()
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
                f"🔴 **{row['area']}** — {row['pct_acerto']}% de acerto "
                f"({int(row['acertos'])}/{int(row['total'])})"
            )

        st.subheader("Evolução diária")
        evol = db.evolucao_diaria()
        if evol:
            df_evol = pd.DataFrame([dict(r) for r in evol]).set_index("dia")
            st.line_chart(df_evol[["pct_acerto"]])
            st.bar_chart(df_evol[["total"]])

        with st.expander("🎯 Desempenho por subtópico"):
            desemp_sub = db.desempenho_por_subtopico()
            if desemp_sub:
                df_sub = pd.DataFrame([dict(r) for r in desemp_sub])
                st.dataframe(df_sub, use_container_width=True, hide_index=True)

        with st.expander("❌ Questões mais erradas"):
            piores_q = db.questoes_mais_erradas()
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
    st.title("✏️ Responder Questões")

    areas = mapa_areas()
    if not areas:
        st.warning("Cadastre uma área primeiro.")
    else:
        col_a, col_b = st.columns(2)
        area_nome = col_a.selectbox("Filtrar por área (opcional)", ["Todas"] + list(areas.keys()))
        area_id = areas[area_nome] if area_nome != "Todas" else None

        if "fila_questoes" not in st.session_state or st.button("🔄 Gerar novo lote"):
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

            if st.button("Confirmar resposta", key=f"conf_{q['id']}"):
                correta = (resposta == q["resposta_correta"])
                db.registrar_resposta(q["id"], resposta, correta)

                if correta:
                    st.success(f"✅ Correto! Resposta: {q['resposta_correta']}")
                else:
                    st.error(f"❌ Errado. A resposta correta é: {q['resposta_correta']}")

                if q["explicacao"]:
                    st.info(f"💡 {q['explicacao']}")

                # qualidade simples para a repetição espaçada
                qualidade = 5 if correta else 1
                sr.registrar_revisao(q["id"], qualidade)

                st.session_state.idx_atual += 1
                if st.button("Próxima questão ➡️"):
                    st.rerun()

# ---------------------------------------------------------------------------
# CADASTRAR QUESTÃO
# ---------------------------------------------------------------------------
elif pagina == "Cadastrar Questão":
    st.title("➕ Cadastrar Nova Questão")

    with st.expander("Cadastrar nova área ou subtópico"):
        col1, col2 = st.columns(2)
        with col1:
            nova_area = st.text_input("Nova área (ex: Cardiologia)")
            if st.button("Adicionar área") and nova_area:
                db.criar_area(nova_area)
                st.success(f"Área '{nova_area}' adicionada.")
                st.rerun()
        with col2:
            areas = mapa_areas()
            if areas:
                area_sub = st.selectbox("Área do novo subtópico", list(areas.keys()), key="area_sub_add")
                novo_sub = st.text_input("Novo subtópico (ex: Arritmias)")
                if st.button("Adicionar subtópico") and novo_sub:
                    db.criar_subtopico(areas[area_sub], novo_sub)
                    st.success(f"Subtópico '{novo_sub}' adicionado.")
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

        if st.button("💾 Salvar questão"):
            alternativas = {"A": alt_a, "B": alt_b, "C": alt_c, "D": alt_d}
            if alt_e.strip():
                alternativas["E"] = alt_e

            if not enunciado.strip() or not all([alt_a, alt_b, alt_c, alt_d]):
                st.error("Preencha ao menos o enunciado e as alternativas A a D.")
            else:
                db.criar_questao(
                    area_id, subtopico_id, enunciado, alternativas,
                    resposta_correta, explicacao, banca, int(ano),
                )
                st.success("Questão cadastrada com sucesso!")
                st.rerun()

# ---------------------------------------------------------------------------
# IMPORTAR QUESTÕES EM MASSA (PLANILHA)
# ---------------------------------------------------------------------------
elif pagina == "Importar Questões (planilha)":
    st.title("📥 Importar Questões em Massa")
    st.caption(
        "Importe centenas de questões de uma vez a partir de uma planilha "
        "Excel (.xlsx) ou CSV, em vez de cadastrar uma por uma."
    )

    st.download_button(
        "⬇️ Baixar planilha modelo (.xlsx)",
        data=imp_q.gerar_template_bytes(),
        file_name="modelo_importacao_questoes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    with st.expander("📋 Colunas aceitas"):
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
                st.success(f"Planilha lida com sucesso: {len(df)} linha(s) encontrada(s).")
                st.dataframe(df.head(10), use_container_width=True, hide_index=True)

                if st.button("🚀 Importar todas as questões"):
                    with st.spinner("Importando..."):
                        relatorio = imp_q.importar(df)

                    st.success(
                        f"Concluído! {relatorio['importadas']} questão(ões) importada(s), "
                        f"{relatorio['duplicadas']} duplicada(s) ignorada(s), "
                        f"de {relatorio['total']} linha(s) na planilha."
                    )
                    if relatorio["erros"]:
                        st.warning(f"{len(relatorio['erros'])} linha(s) com problema:")
                        df_erros = pd.DataFrame(relatorio["erros"], columns=["Linha", "Motivo"])
                        st.dataframe(df_erros, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# REVISÃO (REPETIÇÃO ESPAÇADA)
# ---------------------------------------------------------------------------
elif pagina == "Revisão (Repetição Espaçada)":
    st.title("🔁 Revisão por Repetição Espaçada")
    st.caption(
        "Questões que você errou voltam mais rápido; as que você domina "
        "voltam com intervalos cada vez maiores (algoritmo estilo Anki/SM-2)."
    )

    pendentes = sr.questoes_para_revisar_hoje()
    novas = sr.questoes_nunca_revisadas()

    st.write(f"📅 **{len(pendentes)}** questões para revisar hoje | 🆕 **{len(novas)}** ainda sem revisão agendada")

    fila = list(pendentes) + list(novas)

    if "rev_idx" not in st.session_state:
        st.session_state.rev_idx = 0

    if st.button("🔄 Recomeçar fila de revisão"):
        st.session_state.rev_idx = 0

    if not fila:
        st.info("Nenhuma questão pendente de revisão. Responda questões novas para alimentar a fila.")
    elif st.session_state.rev_idx >= len(fila):
        st.success("Fila de revisão concluída por hoje! 🎉")
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

        if st.button("Confirmar", key=f"rev_conf_{q['id']}_{st.session_state.rev_idx}"):
            correta = (resposta == q["resposta_correta"])
            db.registrar_resposta(q["id"], resposta, correta)
            if correta:
                st.success("✅ Correto!")
                qualidade = st.slider(
                    "Quão fácil foi lembrar? (afeta o próximo intervalo)",
                    0, 5, 4, key=f"qual_{q['id']}_{st.session_state.rev_idx}",
                )
            else:
                st.error(f"❌ Errado. Resposta correta: {q['resposta_correta']}")
                qualidade = 1

            sr.registrar_revisao(q["id"], qualidade)
            st.session_state.rev_idx += 1
            st.rerun()

# ---------------------------------------------------------------------------
# MATERIAIS DE ESTUDO (MediaFire)
# ---------------------------------------------------------------------------
elif pagina == "Materiais de Estudo":
    st.title("📚 Materiais de Estudo (MediaFire)")
    st.caption(
        "Organize aqui os links da sua pasta compartilhada do MediaFire, "
        "por área, subtópico e tipo de material."
    )

    areas = mapa_areas()
    if not areas:
        st.warning("Cadastre uma área primeiro (na página 'Cadastrar Questão').")
    else:
        with st.expander("➕ Adicionar novo material"):
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

            if st.button("Salvar material"):
                if titulo.strip() and link.strip():
                    db.criar_material(area_id, subtopico_id, tipo, titulo, link)
                    st.success("Material adicionado!")
                    st.rerun()
                else:
                    st.error("Preencha título e link.")

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

            df_mat = pd.DataFrame([dict(m) for m in materiais])
            for tipo, grupo in df_mat.groupby("tipo", sort=False):
                st.markdown(f"**{tipo}**")
                for _, m in grupo.iterrows():
                    col1, col2 = st.columns([4, 1])
                    col1.write(m["titulo"])
                    col2.link_button("Abrir 🔗", m["link_mediafire"], key=f"mat_link_{m['id']}")

# ---------------------------------------------------------------------------
# SINCRONIZAR MEDIAFIRE (importação em massa dos materiais)
# ---------------------------------------------------------------------------
elif pagina == "Sincronizar MediaFire":
    st.title("🔄 Sincronizar Pasta do MediaFire")
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

    if st.button("🚀 Sincronizar agora", disabled=not link_raiz.strip()):
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
            st.error(f"Erro ao sincronizar: {e}")
        else:
            status_area.empty()
            st.success("Sincronização concluída!")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Áreas", relatorio["areas_criadas"])
            col2.metric("Assuntos", relatorio["subtopicos_criados"])
            col3.metric("Materiais novos", relatorio["materiais_novos"])
            col4.metric("Já existiam", relatorio["materiais_duplicados"])

            if relatorio["erros"]:
                with st.expander(f"⚠️ {len(relatorio['erros'])} aviso(s)/erro(s)"):
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
    st.title("🗂️ Banco de Questões")

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
                    marcador = "✅" if letra == q["resposta_correta"] else "▫️"
                    st.write(f"{marcador} **{letra})** {texto}")
                if q["explicacao"]:
                    st.info(q["explicacao"])
                st.caption(f"Banca: {q['banca'] or '-'} | Ano: {q['ano'] or '-'}")
                if st.button("🗑️ Excluir questão", key=f"del_{q['id']}"):
                    db.excluir_questao(q["id"])
                    st.rerun()
