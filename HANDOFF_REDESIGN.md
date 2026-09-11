# Handoff: redesign visual concluído — próximos passos de investigação

> Para o agente que for continuar este trabalho: leia este arquivo por completo,
> depois leia `REDESIGN.md` (o briefing original que motivou tudo isto) e por
> fim dê uma passada nos arquivos citados abaixo antes de propor qualquer
> mudança. Não assuma nada sobre o estado do código a partir só deste
> resumo — ele descreve o estado em que o redesign foi ENTREGUE, não
> necessariamente o estado atual (pode ter mudado desde então).

## Contexto

Este é um app Streamlit (`app.py`, `ui.py`, `db.py`) de preparação para provas
de residência médica / ENAMED. Um redesign visual e de interação completo
acabou de ser implementado a partir do briefing em `REDESIGN.md` — que
especifica uma direção estética "vocabulário de laudo clínico" (densidade
alta, cor só como sinal, números como protagonistas), tokens de design
exatos (cores, tipografia, espaçamento), estrutura de rail+topbar, e o
comportamento detalhado de cada tela.

**Seu trabalho não é refazer esse redesign.** Ele já está implementado e
testado manualmente no navegador, tela por tela. Seu trabalho é: (1)
verificar se a implementação está de fato fiel ao briefing e ao bom senso de
produto, (2) achar pontos fracos que a implementação atual não resolveu bem,
e (3) propor abordagens — inclusive abordagens que o briefing não previu —
para deixar a plataforma ainda melhor. Trate o que foi entregue como uma
baseline sólida a criticar, não como um resultado intocável.

## O que foi implementado

- **Tokens e CSS global** (`ui.py`, topo do arquivo): paleta clara e escura
  completas (dicionários `_TOKENS_LIGHT`/`_TOKENS_DARK`), tipografia IBM Plex
  Sans/Mono carregada via Google Fonts, toda a folha de estilo injetada uma
  vez por `ui.inject_theme_css(tema)`. `.streamlit/config.toml` ganhou
  `toolbarMode = "minimal"` e cores base alinhadas ao tema claro (o tema
  escuro só existe via CSS custom, não dá pra fazer o Streamlit nativo
  alternar tema em runtime).
- **Shell**: rail lateral (`st.sidebar`, 232px expandida / 64px recolhida,
  sempre com fundo escuro `--ink-900` independente do tema — decisão do
  briefing) com grupos "Estudo"/"Acervo", CTA fixo "Praticar agora", e uma
  barra superior (`st.container(key="topbar")`) com busca (só visual, não
  funcional — ver limitações), selo de ofensiva, contagem regressiva pra
  prova alvo, alternador de tema e avatar com popover (prova alvo + logout).
- **9 páginas reescritas**: Painel (painel de diagnóstico 3-faixas + lista
  "onde você está errando" + revisões do dia), Praticar (configurador com
  filtros avançados + sessão interativa com calibração de confiança +
  resumo), Simulado (cronômetro em destaque + grade de navegação + diálogo
  de confirmação), Revisão Espaçada (fluxo de autoavaliação estilo
  Anki — mudou de "múltipla escolha corrigida" pra "mostrar resposta + avaliar
  lembrança"), Materiais (árvore de áreas + tabela densa), Banco de
  Questões/Nova Questão/Importar Planilha/Sincronizar MediaFire (formulário
  em coluna única, tabela densa com seleção em lote).
- **Backend novo em `db.py`** (migração automática via `init_db()`, roda na
  inicialização): colunas `usuarios.tema`, `usuarios.data_prova_alvo`,
  `respostas.confianca`; tabela nova `questoes_marcadas`; funções
  `calcular_ofensiva`, `contar_respondidas_hoje`, `distribuicao_respostas_questao`,
  `ids_questoes_filtro_pratica`, `listar_anos`, `ultima_sincronizacao`,
  `marcar_questao`/`desmarcar_questao`/`questao_esta_marcada`/`listar_questoes_marcadas`,
  `definir_prova_alvo`, `atualizar_tema_usuario`. Em `repeticao_espacada.py`:
  `proxima_leva_revisao`.

## Arquitetura que vale entender antes de mexer

- `app.py` roteia páginas por uma chave estável (`pagina_atual`, ex.:
  `"praticar"`, `"banco"`), desacoplada do rótulo exibido no menu
  (`LABEL_POR_KEY`). Isso foi proposital — numa rodada de redesign anterior,
  renomear o rótulo do menu quebrava sessões abertas porque o rótulo era
  usado como chave de roteamento. Não volte a acoplar os dois.
- `ui.py` concentra TODO o sistema de design: ícones SVG Lucide
  (`icon_svg`), componentes de layout (`page_title`, `empty_state`, `chips`,
  `faixa_row`, `lista_erro_barra`, `sparkline_svg`, `anel_progresso`,
  `grafico_barras_horizontais`), e o renderizador de questão
  (`render_cabecalho_questao` + `render_alternativas_interativas` +
  `render_alternativas_resultado`). Qualquer tela nova de questão deveria
  reusar essas três funções, não reimplementar.
- Ícones em **botões nativos do Streamlit** (`st.button(icon=...)`) têm que
  ser Material Symbols (`:material/nome:`) — é a única coisa que o parâmetro
  aceita além de emoji. Os ícones Lucide SVG (`ui.icon_svg`) só podem ser
  usados em HTML próprio (`st.markdown(unsafe_allow_html=True)`), nunca como
  ícone de widget nativo. Isso é uma limitação real do Streamlit, não uma
  inconsistência a "corrigir" — só ficar ciente ao adicionar botões novos.

## Gotchas do Streamlit descobertos nesta rodada (não redescobrir)

1. **`st.markdown('<div>')` seguido de outro elemento e depois
   `st.markdown('</div>')` NÃO envolve o elemento do meio.** Cada chamada de
   `st.markdown`/`st.radio`/etc. vira um elemento IRMÃO no DOM, nunca
   pai/filho de outra chamada. Pra estilizar um widget nativo via CSS, alvo
   tem que ser a classe `st-key-<key>` que o Streamlit aplica automaticamente
   no `.stElementContainer` que envolve QUALQUER widget com `key=` — inclusive
   quando o key varia dinamicamente, dá pra usar `[class*="st-key-prefixo"]`
   (seletor de substring) se todos os keys daquele grupo compartilharem um
   prefixo fixo.
2. **A estrutura real do `st.radio`** (Streamlit 1.63): `[role="radiogroup"]`
   > `label` (um por opção) > `span` (contém o `<input type="radio">` nativo,
   sem classe própria) + `div` com `[data-testid="stMarkdownContainer"]`
   (texto). Não tem um "container da bolinha" separado pra estilizar — pra
   customizar o indicador visual, esconda o `span` (`display:none`) e desenhe
   via `label::before` (dá pra usar `label:has(input:checked)` pra estado
   selecionado, e `:nth-of-type` pra conteúdo posicional tipo letras A-E).
3. **Editar um módulo local (`ui.py`, `db.py`, não o `app.py` principal) e
   só dar refresh na página NÃO garante que o Streamlit recarregue o código
   novo** — na prática, precisou matar e subir o processo `streamlit run` de
   novo pra pegar mudanças em `ui.py` de forma confiável. Se uma mudança de
   CSS/função "não aparece" depois de editar um módulo importado, restart do
   processo antes de assumir que o seletor está errado.
4. **`st.dialog` (modal) não herda automaticamente o CSS customizado da
   página.** O card do dialog cai no tema NATIVO do Streamlit (definido em
   `.streamlit/config.toml`, estático, não responde à alternância de
   tema por sessão) a menos que você mire explicitamente
   `[data-testid="stDialog"] > div` e force `background: var(--surface)
   !important`. Sem isso, o modal fica sempre claro mesmo com o app inteiro
   no tema escuro — bug real que apareceu e foi corrigido nesta rodada (ver
   `ui.py`, seção "Modal (st.dialog)" do CSS).
5. **Screenshots tirados imediatamente após um clique, via automação de
   navegador, às vezes capturam um frame intermediário** (conteúdo da
   página anterior com o título/topbar já atualizado, ou vice-versa) — não é
   bug de roteamento, é timing da automação. Um segundo screenshot sem
   nenhuma ação no meio resolve a dúvida.

## O que ficou deliberadamente fora do escopo (investigar se vale resolver)

- **Atalhos de teclado** (A-E seleciona alternativa, Enter confirma, →
  avança) — o briefing pede isso explicitamente. Não foi implementado
  porque exigiria injetar JS via `st.components.v1.html` com algum canal de
  comunicação de volta pro Streamlit (postMessage + um componente custom, ou
  um hack via query param/session_state polling) — não trivial, mas também
  não impossível. Vale investigar se há uma lib de componente Streamlit
  pronta pra isso antes de construir do zero.
- **Hover-reveal de ações** (ex.: botão "Abrir" de um material só aparecendo
  no hover da linha da tabela) — os botões ficam sempre visíveis hoje.
  `st.dataframe` com `column_config.LinkColumn` já resolve parte disso pra
  materiais (o link abre direto, sem precisar de um botão), mas não há
  hover-reveal de verdade em nenhum lugar.
- **Estado "marcada" na grade de navegação do Simulado** — a grade hoje só
  distingue respondida/em branco (dois estados via `type="primary"`/
  `"secondary"` do `st.button`); o briefing pede três estados
  (respondida/marcada/em branco). "Marcar para revisão" existe em Praticar
  (tabela `questoes_marcadas`) mas não foi estendido ao Simulado.
- **Calibração "Errei — 10 min" na Revisão Espaçada** é só aproximada: o
  algoritmo SM-2 por trás (`repeticao_espacada.py`) agenda em dias inteiros,
  não em minutos. O fix atual reinsere a questão ~4 posições à frente na
  fila da SESSÃO atual (session_state), então ela "volta logo" na prática,
  mas o registro persistido no banco (`revisao.proxima_revisao`) sempre pula
  pro dia seguinte. Se quisesse ser fiel de verdade ao "10 min", precisaria
  de um campo de timestamp (não só data) na tabela `revisao` — mudança de
  schema que não foi feita porque não estava no escopo aprovado desta rodada.
- **Menu do avatar**: só tem "Prova alvo" (editável) e "Sair da conta". O
  briefing menciona "Perfil, Assinatura, Sair" — as duas primeiras eram só
  citadas de passagem, sem conteúdo especificado, então não foram criadas
  como páginas vazias. Se a plataforma for evoluir pra ter assinatura paga
  de verdade, é um ponto natural de expansão.
- **Busca global no topbar** é só um campo visual — não faz busca de
  verdade em nenhuma entidade (questões, materiais). Fica como uma dívida
  explícita: hoje é decoração que parece funcional e não é.
- **Sem testes automatizados de UI** — toda a verificação foi manual, via
  browser automation, tela por tela, uma vez. Não há regressão automatizada
  se algo quebrar depois.
- **O briefing original sugere considerar migrar pra React/Next.js**
  (seção final do `REDESIGN.md`) alegando que o nível de acabamento em
  Streamlit "exige gambiarras de CSS frágeis a cada atualização do
  framework" — o que os gotchas acima confirmam na prática (specialmente o
  #2 e #4). Vale uma avaliação honesta de custo/benefício dessa migração
  agora que o design system already existe e está documentado — talvez não
  precise ser tudo de uma vez, dá pra pensar em migrar por página.

## O pedido pro próximo agente

Não repita o trabalho de implementação — investigue e critique. Coisas que
valem uma segunda opinião:

1. **Teste você mesmo** (suba o app, `streamlit run app.py`, peça login numa
   conta de teste) e veja se a experiência realmente aparenta "nível
   comercial" como o briefing pedia, ou se ainda cheira a protótipo em
   algum ponto que a lista de limitações acima não capturou.
2. **Ataque os pontos fracos listados acima** — escolha os que valem mais a
   pena pelo esforço e proponha (ou já implemente, se o usuário autorizar)
   uma solução.
3. **Traga abordagens que o briefing original não considerou.** Ele foi
   escrito antes de qualquer implementação existir — pode haver ideias
   melhores agora que dá pra ver o resultado real rodando.
4. **Questione decisões que você achar erradas**, inclusive as que este
   handoff apresenta como definitivas. Nada aqui é sagrado — é só o
   registro do que foi feito e por quê, pra você não perder tempo
   redescobrindo o óbvio.
