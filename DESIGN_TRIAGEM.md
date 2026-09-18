# Conduta — sistema visual "Triagem"

> Especificação do app do aluno (`frontend/`). Substitui o `REDESIGN.md` ("laudo
> clínico") para o React; o `REDESIGN.md` segue valendo só para as 4 telas
> administrativas no Streamlit. Decidido em 2026-09-13 depois de duas rodadas de
> protótipo (canvas "Conduta Redesign", página "Rodada 2"). Comportamento e fluxos
> do MIGRACAO.md §0 continuam valendo sem exceção: feedback instantâneo, atalhos
> A–E / Enter / → / M, nada se desloca quando um dado chega, sem spinner de tela
> cheia.

## 1. Ideia central

A plataforma faz com o conhecimento do aluno o que o pronto-socorro faz com o
paciente: **classifica o risco e diz por onde começar**. A identidade inteira sai
daí:

- Cada área recebe um **nível de triagem** calculado pelo aproveitamento. O Painel é
  um quadro de triagem, não uma coleção de gráficos.
- A escala de cinco cores é a marca. Ela **só aparece quando significa um nível** —
  nunca como decoração, nunca como "cor da seção".
- Tudo o que não é nível é tinta sobre papel: preto, cinzas e branco. Botão
  primário é preto, não colorido.
- No Praticar e na Revisão, cada questão é um **caso** ("Caso 07", "Discussão do
  caso", "Conduta correta"). No Simulado continua "Questão", porque ali o aluno
  está reproduzindo a prova.

O que diferencia de concorrentes: nenhuma plataforma de questões usa a lógica da
classificação de risco para organizar o estudo, e nenhuma trata o botão primário
como tinta em vez de cor de marca.

## 2. Escala de triagem

| Nível | Nome          | Aproveitamento | Cor (claro) | Cor (escuro) | Texto sobre a cor |
|-------|---------------|----------------|-------------|--------------|-------------------|
| 1     | Emergência    | abaixo de 40%  | `#CF3328`   | `#F0574C`    | branco / tinta    |
| 2     | Muito urgente | 40 a 54%       | `#F17C1B`   | `#F58A34`    | tinta / tinta     |
| 3     | Urgente       | 55 a 69%       | `#EDBB1C`   | `#F2C94C`    | tinta / tinta     |
| 4     | Pouco urgente | 70 a 84%       | `#23804A`   | `#3DB372`    | branco / tinta    |
| 5     | Não urgente   | 85% ou mais    | `#2D6CD2`   | `#5B8FEA`    | branco / tinta    |

- "Tinta" = `--ink` do tema (quase preto no claro, quase branco no escuro). Os pares
  acima passam AA para texto de 13px em negrito; não trocar o texto de cor sem
  medir de novo.
- **Aproveitamento** é o acerto na primeira vez que o aluno responde cada questão
  (`db._PRIMEIRAS_TENTATIVAS`). Responder a mesma questão de novo mede se ele
  lembra dela, e isso é da Revisão ("Evolução da memória"), não do quadro.
- Áreas com **menos de 5 questões respondidas** não são classificadas: vão para a
  linha "Amostra insuficiente" (mesmo limite que já existia).
- A função de classificação é de apresentação e mora em `frontend/src/lib/triagem.ts`
  (mesmo precedente do limite de amostra, que já vivia no front). Se um dia a
  classificação alimentar regra de negócio (ex.: escolher questões), ela migra
  para `db.py`.
- **Semântica derivada da escala**: acerto = nível 4 (verde), erro = nível 1
  (vermelho), atenção = nível 2 (laranja, ex.: cronômetro do simulado com menos de
  10 min, ofensiva ainda não cumprida hoje). Amarelo e azul nunca significam
  acerto/erro.

## 3. Tokens

Todos como variáveis CSS em `src/styles/theme.css` (`:root` claro, `.dark` escuro)
e mapeados no `tailwind.config.js`. Nenhum hex solto em componente.

### Cor

```
                claro      escuro
--ground        #F2F3EF    #0E1012   fundo da aplicação
--surface       #FFFFFF    #16191C   cartões, barra superior, campos
--ink           #111315    #ECEDEA   texto principal, botão primário
--ink-2         #3E4247    #C3C6C2   texto secundário
--muted         #6C7178    #8E949A   rótulos, metadados
--faint         #8A8F96    #6B7077   placeholder, desabilitado
--line          #DFE1DC    #2A2E32   bordas
--line-soft     #ECEDE9    #22262A   trilhos de barra, divisores internos
--on-ink        #FFFFFF    #0E1012   texto sobre botão primário

--t1..--t5      ver §2
--t1-soft       #FCE4E1    #3A1714   fundo de alternativa errada
--t2-soft       #FDEBDB    #3A2410
--t3-soft       #FBF2D3    #3A3110
--t4-soft       #E1F2E7    #10301E   fundo de alternativa correta, ofensiva cumprida
--t5-soft       #E1EAF9    #142540
--focus         #2D6CD2    #5B8FEA   anel de foco (2px, offset 2px)
```

### Tipografia

Uma família: **Archivo** (Google Fonts, variável em largura 62–125 e peso). A
personalidade vem de alternar a **largura**: condensada para rótulos, expandida
para números grandes.

```
display-xl  88px / 0.88 / 800 / largura 118% / tracking -0.045em  aproveitamento geral
display     60px / 0.85 / 800 / largura 118% / tracking -0.04em   número do caso, fila
h1          44px / 1.04 / 800 / tracking -0.03em                  título do Painel
h2          24px / 1.2  / 800 / tracking -0.02em                  "Resposta correta: B"
h3          17px / 1.3  / 700                                     títulos de bloco
corpo       15.5px / 1.55 / 400
enunciado   17.5px / 1.75 / 400 / largura 108% / tracking 0.005em   .leitura-enunciado
discussão   16.5px / 1.75 / 400 / largura 108% / tracking 0.005em   .leitura-discussao, cor --ink-2, em parágrafos
apoio       13.5px / 1.45 / 400, cor --muted
rótulo      13px / largura 70% / 700 / CAIXA ALTA / tracking 0.06em, cor --muted
```

- Números sempre com `tabular-nums` e no formato brasileiro (`63,9%`, `1.646`).
- Caixa alta só no **rótulo** (e nos nomes de nível dentro de etiquetas). Título,
  botão e texto corrido em caixa normal.
- A marca "Conduta": 21px, 800, largura 115%, tracking -0.03em, precedida do
  **símbolo**: cinco barras de 4px de largura, alturas 20/16/12/8/4px, nas cores t1→t5.

### Forma, espaço, movimento

- Raios: 3px etiqueta · 4px cabeçalho de coluna · 5px botão e campo · 6px cartão e
  linha · 8px cartão do caso. Nada acima de 8px (a identidade é de ficha, não de app).
- Sem sombra. Separação por borda de 1px `--line` e contraste de superfície.
- Espaçamento em múltiplos de 4px; entre blocos do Painel, 28px.
- Ícones Lucide com traço 2px (combina com o peso da Archivo), 16px em linha, 18px
  em botão de ícone.
- **Movimento** (tokens em `tailwind.config.js`, ganchos em `src/lib/movimento.ts`).
  A plataforma não pode "cortar" de uma tela para outra; cada troca tem um
  movimento curto, sem quique e sem nada que atrase o aluno.
  - Curvas: `brand` `cubic-bezier(0.2, 0, 0.2, 1)` para troca de estado; `suave`
    `cubic-bezier(0.16, 1, 0.3, 1)` para o que entra, desliza ou cresce.
  - Durações: 120ms hover · 180ms revelação/troca de cor · 320ms deslizamentos
    (sublinhado da aba, gaveta, fundo de aba segmentada) · 700–1100ms só para
    barras enchendo, números contando e a linha do gráfico.
  - Tela nova sobe 8px enquanto aparece (`animate-entrar`, no AppShell por
    caminho e nas trocas de fase de Praticar/Simulado). Caso ou questão nova
    desliza no sentido da navegação (`animate-entrar-frente`/`-tras`) e a página
    volta ao topo.
  - Menus, busca e diálogos crescem de 97% e saem encolhendo (`usePresenca`
    mantém montado durante a saída). Botões cedem ao clique (`active:scale`).
  - Painel é o único momento com coreografia: quadro em cascata (coluna mais
    grave primeiro), barras enchendo, aproveitamento e fila contando do valor
    anterior ao atual (só reanima se mudou) e a linha de 14 dias se desenhando.
  - Revelação da resposta: letra escolhida "carimba", etiquetas de conduta e
    discussão entram em sequência.
  - Nada se desloca durante uma animação: números contam sobre a largura final
    reservada, percentuais entram em coluna já reservada.
  - `prefers-reduced-motion` zera durações e atrasos; contagens pulam direto ao valor.

## 4. Componentes

- **Botão primário**: fundo `--ink`, texto `--on-ink`, 600, altura 42–46px, raio 5.
  Pode carregar um `kbd` à direita ("Enter"). Hover: 88% de opacidade. Desabilitado:
  fundo `--line`, texto `--faint`.
- **Botão secundário**: fundo `--surface`, borda `--line`, texto `--ink-2`; hover
  troca a borda para `--muted`.
- **Etiqueta de nível**: fundo da cor do nível, texto conforme §2, rótulo condensado
  em caixa alta, raio 3.
- **Cabeçalho de coluna**: igual à etiqueta, altura 40px, largura total, nome à
  esquerda e contagem à direita.
- **Cartão de área**: superfície, borda, raio 6, padding 14. Nome (15px/600),
  percentual (30px/800, largura 110%), fração (13px `--muted`), barra de 4px na cor
  do nível. Clique leva ao Praticar filtrado, e o atalho "Praticar 10" fica
  **sempre visível** — botão de tinta no cartão de destaque, link de texto nos
  outros. Era revelado no hover até 2026-09-18, o que o tornava inalcançável em
  tela de toque: nenhuma ação pode depender de hover.
- **Dica de gráfico**: aparece em hover **e** em foco — ponto e barra levam
  `tabindex`, porque toque não gera hover. No gráfico de linha é texto de 12px/600
  com contorno na cor da superfície (`paint-order: stroke`), ancorado para dentro
  nas pontas; nas barras, caixa de superfície com borda `--line` e raio 3 acima da
  barra. Nunca usar o `title` nativo de HTML ou SVG: espera ~1s, não aceita estilo
  e não existe no celular.
- **Alternativa**: grade `[letra 32px] [texto] [extra]`, borda 1px, raio 6, padding
  12/14. Letra num quadrado de 32px, raio 4, fundo `--ground`.
  - Selecionada (antes de confirmar): borda 2px `--ink`, letra com fundo `--ink`.
  - Correta: borda 2px t4, fundo t4-soft, letra t4, etiqueta "Conduta correta".
  - Errada escolhida: borda 2px t1, fundo t1-soft, letra t1, etiqueta "Sua conduta".
  - Demais após confirmar: texto `--muted`, percentual de escolha à direita.
- **Campo / select**: altura 40px, borda `--line`, raio 5; foco com borda `--ink` e
  anel `--focus`.
- **kbd**: 11.5px, 600, padding 4/7, raio 4, fundo translúcido sobre o botão ou
  `--line-soft` fora dele.
- **Estado vazio**: caixa com borda tracejada `--line`, uma frase que orienta e no
  máximo um botão.
- **Skeleton**: blocos `--line-soft` com as dimensões finais.

## 5. Estrutura

**Barra superior (64px, `--surface`, borda inferior)** substitui o rail lateral.
Esquerda: marca. Centro-esquerda: abas Painel, Praticar, Simulado, Revisão (rótulo
curto; o menu em gaveta mostra "Revisão espaçada"), com contagem numa etiqueta t1
quando houver revisões vencidas — aba ativa com sublinhado de 2px
`--ink`. Entre 1024 e 1279px a etiqueta de ofensiva mostra só o número. Direita: busca global (atalho
`/`), etiqueta de ofensiva (t4-soft se já respondeu hoje, t2-soft se não), botão de
tema e avatar. O menu do avatar tem e-mail, prova alvo, **Acervo** (links do
Streamlit, só para `is_admin`) e Sair.

Abaixo de 1024px as abas viram um menu em gaveta aberto pelo botão à esquerda da
marca; abaixo de 640px a busca some da barra.

**Modo foco** (sessão de Praticar, Simulado em andamento, Revisão com fila): a barra
superior troca as abas por "Sessão de prática · {área}", progresso, cronômetro,
Marcar e Encerrar. O conteúdo fica numa coluna de 680px centralizada; é essa
largura, e não um limite no parágrafo, que mantém a linha curta com o texto indo
até a borda das alternativas. Medido com o texto real: ~63 caracteres por linha no
enunciado e ~68 na discussão (com 840px eram 85 e 98, cansativo de ler; um limite
em ch no parágrafo deixava um vão à direita das alternativas). Configurador e
resumo usam a mesma coluna, para nada mudar de largura entre as fases. Toda sessão
tem uma saída na própria barra (Encerrar, Finalizar ou Sair), e a marca à esquerda
é sempre um link para o Painel, inclusive no modo foco.

Conteúdo das demais telas: largura máxima 1360px, padding 36/40px.

## 6. Telas

### Painel
1. **Cabeçalho**: rótulo "Triagem de hoje · {dia da semana, data}"; h1 "{Área} é a
   sua maior lacuna." (com menos de 50 respostas: "Volume ainda baixo para
   conclusões." e apoio "Responda mais {n} questões para a triagem ficar
   confiável."); linha de apoio "{acertos} acertos em {total} questões · {hoje} de 20
   questões hoje · prova em {n} dias"; à direita, rótulo "Aproveitamento geral" e o
   percentual em display-xl.
2. **Quadro de triagem**: 5 colunas, uma por nível, com cabeçalho e cartões de área
   ordenados do pior para o melhor. Coluna vazia mostra estado vazio curto ("Nenhuma
   área acima de 85% ainda."). O primeiro cartão da coluna mais grave já mostra o
   botão "Praticar 10". Abaixo, legenda das faixas, a nota "Acerto no chute vale
   meio" e a linha "Amostra insuficiente". Em telas estreitas, as colunas viram
   grupos empilhados. Todo o Painel conta só a primeira resposta a cada questão, e
   nela o acerto marcado como chute vale 0,5 (`db._PRIMEIRAS_TENTATIVAS`): os
   acertos podem ter vírgula ("14,5 acertos").
3. **Nota projetada na prova** (`db.nota_projetada`), largura total, só com 50
   questões respondidas ou mais: a nota que o domínio de hoje dá numa prova do
   INEP (o domínio estimado de cada tema, o mesmo de "Onde você ganha mais pontos",
   pesado pelas questões de caderno do tema), com etiqueta de nível e
   "Provavelmente entre {x}% e {y}% numa prova de 100 questões". A faixa (95%) soma
   a incerteza das respostas à variação de uma prova só, então não fica menor que
   uns 10 pontos para cada lado, e a tela diz isso. Ao lado, "Provas oficiais
   feitas" (`db.simulados_oficiais_feitos`): as 5 últimas, com data, etiqueta de
   percentual e "já tinha visto {n} das {total}" quando o aluno respondeu questões
   do caderno antes de começar (o banco é feito dos cadernos, e nessas a nota mede
   memória). Sem nenhuma, "Fazer uma prova oficial" abre o Simulado.
4. **Onde você ganha mais pontos** (`db.prioridades_estudo`), largura total: os 3
   temas com mais pontos a ganhar, pela fração dos cadernos do INEP (Revalida e
   ENAMED) que o tema ocupa × o que falta de domínio. Com poucas respostas, o
   domínio do tema é estimado a partir da especialidade, e o dela a partir da
   área, para uma resposta certa não virar 100%. Cada cartão: tema, especialidade ·
   área, o acerto ("Você ainda não praticou este tema", "Acertou 1 de 2 · pouca
   evidência" ou percentual com barra de nível a partir de 5 respostas), "Caiu em
   {n} das {total} provas do INEP" e "Praticar {n}" (10, ou o tema inteiro se tiver
   menos), que abre a sessão já filtrada. Só o primeiro botão é primário.
5. **O que mudou nesta semana** (`db.progresso_semana`), largura total, só quando
   houve questão nova desde segunda-feira: "{n} questões novas, {x} certas ({%})" e
   até 4 temas praticados, do mais praticado para o menos. Cada tema traz a
   especialidade, quantas novas e quantas certas, o que a Revisão cobrou dele na
   semana ("lembrou de {a} de {b}", a mesma definição de teste da Evolução da
   memória) e o domínio estimado na segunda → agora, o de agora em etiqueta de
   nível. Quem começou nesta semana não tem "antes": só aparece o agora.
6. **Por tipo de pergunta** (`db.desempenho_por_tipo`), largura total: o mesmo
   aproveitamento do quadro separado pelo que a questão pede — Diagnóstico,
   Exames, Conduta e Conceitos (`db.TIPOS_PERGUNTA`). Cada tipo com percentual,
   fração e barra de nível a partir de 5 respostas ("Pouca evidência" antes), e o
   tipo inteiro é um botão para "Praticar 10" dele. Quando o melhor e o pior tipo
   com amostra diferem 15 pontos ou mais, uma frase aponta o ponto fraco.
7. **Rodapé** em duas colunas: "Fila de revisão" (casos de hoje dentro da meta diária em
   display, com a duração estimada pelo tempo real do aluno e quantos podem esperar;
   seletor "Meta diária" 10/20/30/50; "Próximos 7 dias" em barras — parte dentro da
   meta em `--ink`, o que passa dela em t2 (atenção), linha tracejada na meta, legenda
   só quando algum dia passa; botão "Revisar agora") e "Acerto nos últimos 14
   dias" (linha em `--ink` sobre as faixas de nível em transparência, último ponto
   marcado e rotulado; menos de 3 dias: "Histórico começa a aparecer no terceiro dia
   de estudo.").
8. **Evolução da memória** (`repeticao_espacada.evolucao_memoria`), largura total. Só
   conta como teste de memória o caso que voltou depois de pelo menos 1 dia sem ser
   visto (refazer 10 min depois do erro não conta). Frase da semana: "Nos últimos 7
   dias, {n} casos voltaram e você lembrou de {x} ({%})" com etiqueta de nível e,
   em apoio, a semana anterior, recuperados (errou e lembrou dias depois),
   consolidados e dias com revisão. Abaixo, três blocos: **Estágios dos casos**
   (barra empilhada aprendendo / consolidando / consolidado em `--faint` / `--muted`
   / `--ink` — não são níveis, então nada de t1–t5 — com legenda e contagem);
   **Retenção por semana** (8 blocos de 7 dias terminando hoje, escala 0–100%,
   o atual em `--ink` e os anteriores em `--muted`; semana com menos de 5 testes só
   marca o chão; nenhuma com amostra: caixa tracejada na altura do gráfico); **Onde
   você mais esquece** (até 4 especialidades com 5+ testes, da menor retenção, barra
   na cor do nível). O mesmo limite de amostra do quadro vale para todo percentual.

### Praticar
- **Configurador**: título "Praticar"; campos área, especialidade e tema (só os que
  têm casos, com a contagem; cada um depende do anterior, e o tema ocupa a linha
  inteira porque há nomes longos), banca, ano; tipo de pergunta (Todos e os quatro
  tipos) e quantidade como botões segmentados (10/20/30/50); dois interruptores; filtros escolhidos
  viram etiquetas removíveis; no rodapé, "{n} casos nesse recorte" à esquerda e
  o botão "Iniciar sessão de {n} casos" à direita. A contagem vem do servidor a
  cada mudança de filtro (`GET /praticar/contagem`) e manda no botão: ele
  anuncia o menor entre a quantidade escolhida e o que existe, e desliga em
  "Nenhum caso nesse recorte" — antes o recorte vazio só aparecia depois de
  começar a sessão.
- **Sessão (modo foco)**: acima do cartão, "Caso" + número em display à esquerda,
  área · especialidade e selo de prova oficial à direita, com todas as provas em que
  o caso caiu ("Revalida 2025/2 · ENAMED 2025") e não só o caderno principal
  (`db.provas_das_questoes`). O tema não entra aí: numa
  questão que pede o diagnóstico ele entregaria o gabarito, então só aparece
  depois de confirmar, na discussão (decisão do usuário). Cartão com enunciado, imagem,
  pergunta, alternativas e, antes de confirmar, dicas de atalho + "Confirmar
  resposta". Progresso na barra superior: um quadrado por caso (t4 acerto, t1 erro,
  `--line` pendente).
- **Após confirmar**: estados de alternativa (§4) com percentual de escolha;
  bloco "Discussão do caso" com "Resposta correta: {letra}", "Você marcou {letra},
  como {x}% dos outros alunos" (só quando a distribuição chegar; o espaço fica
  reservado; sem respostas de outros alunos: "Ninguém mais respondeu este caso
  ainda." e nenhum percentual nas alternativas), "Tema: {tema}" e a explicação em parágrafos (`src/lib/paragrafos.ts`: as explicações do banco
  são um bloco único, então a quebra é na exibição — um parágrafo para a resposta
  certa, um por alternativa discutida, alternativas curtas juntas, blocos longos
  divididos por frase; quebras escritas no texto têm prioridade). Acertou: "Acertei com segurança" (primário) e "Acertei
  no chute" (secundário; vale meio acerto no Painel). Errou: "Volta na sua revisão em 10 min" (é verdade: o SM-2
  agenda qualidade abaixo de 3 para 10 minutos, `repeticao_espacada.py`) e "Próximo
  caso" com `Enter`.
- **Resumo**: acertos em display, etiqueta de nível do aproveitamento da sessão,
  tempo médio por caso e desempenho por especialidade em linhas com barra de nível.

### Simulado
- Configurador com duas abas. **Prova oficial**: lista das edições com caderno
  identificado (nome, total de questões, duração no ritmo oficial de 3 min por
  questão e, se houver, o aproveitamento da última tentativa como etiqueta de
  nível); começar pede confirmação, porque o tempo não para. **Montar simulado**:
  área, banca, quantidade e tempo.
- Prova em andamento e ainda dentro do tempo aparece acima das abas, com borda
  `--ink` e "Continuar prova"; ao retomar, abre na primeira questão em branco.
- Mesmo cartão e alternativas do Praticar, sem feedback e sem o tema (o resultado
  mostra, junto da discussão). Na prova oficial, a linha
  de procedência mostra a edição e o número da questão no caderno.
- Cronômetro em h:mm:ss a partir de 1 hora (a prova oficial passa de 4 horas).
- Barra superior em modo foco com o cronômetro regressivo em display condensado:
  `--ink` normal, t2 com menos de 10 min, t1 com menos de 1 min. Sem piscar.
- Grade de navegação com três estados: respondida (fundo `--ink`), marcada (canto
  t3), em branco (só borda). Questão atual com anel `--focus`.
- Diálogo de finalização informa quantas ficaram em branco.
- Tempo de tela por questão (`simulado_itens.tempo_ms`): cada passagem pela questão
  vai para o servidor ao sair dela, ao finalizar e quando a aba some; aba escondida
  não conta.
- Resultado: aproveitamento com etiqueta de nível; "Tempo médio de {mm:ss} por
  questão respondida, dentro (ou acima) do ritmo de {mm:ss} da prova", em que o
  ritmo é o tempo do simulado dividido pelas questões (3 min na prova oficial), e em
  quantas questões passou dele; quadro de triagem por área do simulado; "Temas para
  revisar" (`db.temas_errados_simulado`): temas com erro ou em branco, mais erros
  primeiro e, no empate, os que mais caem no INEP, 8 visíveis e "Mostrar os {n}
  temas", cada um com especialidade, "acertou {x} de {y}" e "Praticar {n}" já
  filtrado pelo tema; na revisão
  completa, o tempo de cada questão, em `--ink` e negrito quando passou do ritmo, e
  um traço na que o aluno nem abriu.
  Simulado de antes da medição não mostra tempo.

### Revisão espaçada
- A fila é o que o SM-2 já venceu mais as questões marcadas pelo aluno
  (`repeticao_espacada.fila_revisao`). Casos nunca respondidos não entram: não há
  o que revisar, e eles são do Praticar. A contagem da aba, do Painel e o
  "restantes" da barra saem dessa mesma fila e precisam sempre bater.
- Meta diária (padrão 20, `usuarios.meta_revisao_diaria`, `plano_revisao`): a tela
  oferece só os casos que cabem no que falta da meta, em ordem de prioridade —
  reaprendendo (errou), marcadas, depois as mais atrasadas em relação ao próprio
  intervalo e as de menor facilidade. Só avaliações na Revisão consomem a meta. O
  que passa dela espera sem alerta: meta cumprida mostra "Meta de hoje cumprida" e
  "Revisar mais 10". A barra mostra os restantes com a duração estimada.
- Um caso por vez, contagem restante na barra superior, "Recomeçar fila" e "Sair"
  (volta ao Painel; cada avaliação já foi gravada).
- O aluno responde de novo, como no Praticar (A–E, Enter), e vê a correção, o
  tema e a discussão. Quem decide se foi erro é o gabarito: resposta errada agenda sozinha
  ("Volta na sua revisão em 10 min" + "Próximo caso", Enter). Resposta certa pede
  "Como foi lembrar?": "Com esforço" (t2), "Lembrei" (t4), "Fácil" (t5), teclas
  1–3, cada botão com o prazo que vai de fato agendar ("volta em 6 dias"), vindo de
  `repeticao_espacada.prever_prazos` — nunca um prazo fixo escrito no front (os
  antigos "Bom — 4 dias"/"Fácil — 10 dias" não batiam com o SM-2). Quadrado de 10px
  da cor do nível antes do rótulo; nada de borda lateral colorida.
- Toda avaliação (Praticar, Simulado, Revisão) grava uma linha em
  `revisao_eventos`: nota, acerto, alternativa, estado antes/depois, atraso e
  tempo. É a base da estimativa de duração e da Evolução da memória no Painel.
- Fim da fila com casos avaliados: resumo "Lembrou {x} de {n} casos.", com a
  retenção de primeira (etiqueta de nível), quantos voltam em 10 min e a próxima
  leva; se houve, uma frase com os recuperados e consolidados da sessão (quem
  decide é o servidor, `classificar_eventos`).
- Fila vazia: estado vazio com a próxima leva ("As próximas 8 vencem na quinta.") e
  "Praticar casos novos".

### Login
- Marca grande com o símbolo, frase "Sua plataforma de estudos para residência
  médica", cartão com abas Entrar / Criar conta. Fundo `--ground`.

## 7. Voz

Português do Brasil, direto, sem "Parabéns!". A metáfora da triagem aparece nos
nomes de nível e na organização, não em piadas: nada de "paciente", "óbito" ou
"alta" aplicados ao aluno. Botões no infinitivo ou com o objeto explícito
("Revisar agora", "Próximo caso").
