# Histórico de decisões — Conduta

Resumo do **porquê** das decisões que continuam valendo, pendências e
armadilhas das telas admin. Regras, comandos e arquitetura atuais ficam no
`CLAUDE.md`; o histórico superado (paletas antigas, telas de aluno em
Streamlit, transcrições) só existe no git, no antigo `contextoconversaclaude.txt`.

## Pendências

- **Deploy no servidor (bloqueado por SSH).** A chave autorizada na instância
  Oracle ficou em outro computador, e a Oracle não deixa baixar nem trocar a
  chave de uma instância existente. No notebook atual existe
  `~/.ssh/conduta-oracle` (alias `residencia-med` no `~/.ssh/config`), ainda
  não autorizada: a partir do outro PC, anexar a `.pub` em
  `~/.ssh/authorized_keys`. Host key ED25519 esperada:
  `SHA256:c5q+FAcRSupd1hNDvfaGk6Su6oepMnb1cf+8DTQJN6A` (conferir antes de
  aceitar). Esperando esse deploy: HTTPS via DuckDNS, redesign Triagem,
  simulado por prova oficial e `questoes_provas`, taxonomia de especialidades,
  correção da conexão morta do Neon, revisão espaçada em 3 fases, a limpeza de
  código morto e a remoção dos materiais. Passos: `git pull`,
  rebuild do front, no `.env.production` `COOKIE_SECURE=true` e
  `CORS_ORIGENS=https://conduta.duckdns.org`, copiar o Caddyfile, reload do
  caddy, restart de api e streamlit, testar, só então fechar a 8080 (iptables
  **e** Security List) e atualizar o `DEPLOY.md`, apagando junto o
  `deploy/Caddyfile.com-dominio.example` (é do domínio pago descartado, e o
  `DEPLOY.md` ainda o cita).
- Enquanto o deploy não sai, o servidor roda código antigo sobre o banco já
  migrado: Materiais lá mostra só as 5 grandes áreas, sem especialidades, e a
  Prova oficial lista a Revalida 2025/2 só com as 50 questões próprias (as 43
  comuns com o ENAMED 2025 só entram pela `questoes_provas`).
- Questões oficiais ainda fora do banco: Revalida 2020, 2021 e 2022-1;
  edições anteriores da USP (a FUVEST só mantém a atual); UNICAMP de 2024 em
  diante (respostas curtas); UNIFESP e Santa Casa (caderno não público); ENARE
  e hospitais.
- Se o shape ARM `VM.Standard.A1.Flex` (1 OCPU/6 GB, Always Free) aparecer em
  São Paulo e 1 GB apertar, recriar a instância nele.
- Tema escuro do Triagem só existe por tokens, sem protótipo próprio.
- **Temas por especialidade, em fases.** Decisão do usuário (2026-09-14): um
  nível abaixo da especialidade, para o aluno saber exatamente o que a questão
  cobra (ex.: Psiquiatria > Transtornos de ansiedade). Usa a tabela
  `subtopicos`, que já existe e não tem nenhuma questão ligada. Fonte: Portaria
  Inep nº 540/2020, art. 7º (conteúdos por área do Revalida); a Matriz Comum de
  2025 (Portaria 478) só define áreas, competências e cenários, sem lista de
  doenças. Fases:
  1. Lista `db.TEMAS`, 197 temas (feita e aprovada). Na classificação entraram
     temas que faltavam, com aprovação do usuário: "Prolapso genital e
     incontinência urinária" (Ginecologia); em Pediatria clínica, diabetes e
     endócrino, vasculites e reumatologia, desenvolvimento e comportamento,
     síndromes genéticas e doenças digestivas; e "Malformações e síndromes
     genéticas no recém-nascido" (Neonatologia); em Infectologia pediátrica,
     infecções respiratórias agudas e infecções gastrointestinais e urinárias;
     e "Cirurgia bariátrica" (Cirurgia geral, não citada pelo nome na portaria,
     mas cobrada nas provas) — os demais citados na Portaria
     540/2020, que a primeira lista tinha comprimido demais. Vale conferir as
     próximas especialidades contra o texto da portaria antes de classificar.
  2. Temas no banco (feita): `init_db` grava os temas em `subtopicos`;
     `db.listar_temas` esconde os 44 assuntos antigos do MediaFire pelo campo
     `origem` (nenhum nome colide); a planilha e o formulário do Streamlit só
     aceitam temas existentes, e "Adicionar assunto" saiu. **Próxima: fase 3.**
  3. Classificar as 986 questões lendo o conteúdo, uma especialidade por vez,
     com simulação, backup e amostra revisada pelo usuário. Ferramenta:
     `scripts/classificar_temas.py <json>` (simula; `--aplicar` grava e salva
     backup); os JSONs de classificação ficam em `backups/temas_*.json`.
     Feito (2026-09-14): Ginecologia e Obstetrícia inteira — Obstetrícia (96),
     Ginecologia (92) e Mastologia (12); em Pediatria, Pediatria clínica (73) e
     Neonatologia (33), Infectologia pediátrica (30) e Puericultura (25) —
     Pediatria inteira; em Cirurgia, Cirurgia geral (57). 418 de 986 questões
     com tema. **Próximo: Trauma**, depois as outras especialidades de
     Cirurgia, Medicina Preventiva e Clínica Médica.
  4. Filtro de tema no Praticar e tema no cabeçalho do caso (o cabeçalho já
     mostra `subtopico`).
  5. Estatística por tema só quando houver respostas suficientes (hoje ~30 por
     aluno; o Painel exige 5 por grupo).

### Próximos passos sugeridos (enquanto o deploy espera)
Levantados em 2026-09-14, em ordem de valor. O deploy continua sendo o item
mais importante assim que houver acesso SSH.

1. **Revalida 2020, 2021 e 2022-1.** Procurar pelas abas por ano da página do
   INEP (`…/revalida/provas-e-gabaritos/2020`, `/2021`, `/2022`), que trazem os
   links dos PDFs no próprio HTML; foi assim que a 2025/2 e a 2026/1 foram
   achadas depois de o padrão de nome falhar. Seguir o roteiro de importação do
   `CLAUDE.md`.
2. **Revisão clínica de uma amostra das explicações de 2026-09-14**, começando
   pelas de gabarito discutível: Revalida 2025/2 Q91 (vírus sincicial
   respiratório em adolescente); USP 2026 Q31 (estadiamento antes de ampliar
   margens no melanoma T4b), Q108 (ressonância na puberdade precoce aos 6 anos)
   e Q116 (SIU de levonorgestrel em vez de DIU de cobre na paciente com SAAF
   anticoagulada); UNICAMP 2023 Q6 (profilaxia meningocócica até 14 dias). Uma
   página de revisão em que o usuário marca o que ajustar resolve; correções
   entram por UPDATE, nunca apagando a questão.
3. **QA no navegador das questões com figura**, sobretudo as de
   alternativa-imagem (USP 11, 14, 33, 40, 49, 66, 69, 70 e 72) e os recortes
   altos (USP 1 e 70), também em largura de celular. O usuário faz o login na
   conta de QA.
4. **Tempo do simulado oficial por banca.** Hoje todas usam
   `MINUTOS_POR_QUESTAO_PROVA_OFICIAL` = 3. Bate com o INEP e com a UNICAMP 2023
   (80 questões em 4 h); conferir no edital da FUVEST a duração da prova da USP
   (113 questões dão 5h39) e, se diferir, guardar o ritmo por banca.
5. **Questões comuns a mais de uma prova.** No simulado da Revalida 2025/2, as
   43 questões compartilhadas aparecem com o selo "ENAMED 2025". Expor na API as
   provas de `questoes_provas` e mostrar todas na questão.
6. **Importador reutilizável em `scripts/`.** Os scripts das importações de
   2026-09-14 ficaram no scratchpad da sessão e se perderam. Fazer um script
   genérico que recebe o JSON montado (enunciado, alternativas, gabarito, área,
   especialidade, explicação, imagem, banca, edição e número) e grava as
   questões e os vínculos em `questoes_provas` numa transação, com simulação por
   padrão, checagem de duplicatas e backup.

## Decisões, por data

### 2026-09-10 — performance e conteúdo (ainda em Streamlit)
- Lentidão vinha de `init_db()` rodando a cada clique, falta de cache, 4
  queries sequenciais no dashboard e FKs sem índice. Viraram cache, uma query
  com subqueries `jsonb_agg` (`desempenho_dashboard_combinado`) e índices
  explícitos. De ~2 s por clique para ~0,1–0,35 s.
- Imagem da questão fica no Postgres (BYTEA), não em disco: o host da época
  apagava o filesystem a cada deploy. O motivo sumiu, o padrão continua certo.
- As explicações das 458 questões originais foram escritas por raciocínio
  clínico próprio porque o INEP só publica gabarito. Sem marca de "gerado por
  IA" por decisão do usuário. Reaproveitar explicação de plataforma paga foi
  descartado.
- Edição e exclusão de questão/material só para admin, com confirmação.

### 2026-09-11 — redesign "laudo clínico" (Streamlit)
Especificado em `REDESIGN.md` (o handoff detalhado só existe no git). Hoje só
governa as telas admin do Streamlit.

### 2026-09-12 — migração para FastAPI + React e publicação
- Motivo: acabamento visual em Streamlit exigia CSS frágil a cada atualização,
  e o objetivo número 1 era feedback instantâneo na resposta (daí o lote
  inteiro com gabarito em `GET /praticar/sessao`). Antes de codar, o contrato
  função→endpoint do `MIGRACAO.md` foi conferido contra o código real.
- As 4 telas admin ficam no Streamlit para sempre: um único admin usa, a
  reescrita é cara e não melhora nada para o aluno (`MIGRACAO.md` §4/§5).
  As telas de aluno antigas ficaram no `app.py`, sem uso; limpar não
  compensou o risco na época (saíram em 2026-09-14).
- Bugs que a migração revelou: o simulado vazava gabarito antes de finalizar
  (hoje os campos saem enquanto `finalizado_em` é nulo); o status da
  sincronização exigia admin e voltou a ser de qualquer usuário logado.
- `scripts/seed_demo_user.py` popula `demo@residenciamed.com` com ~400
  respostas sintéticas em 8 semanas (desempenho desigual por área de
  propósito), para o Painel de demonstração não aparecer vazio. Idempotente.
- A migração foi um commit único (`bf5798d`) em vez de reconstituir um
  histórico fase a fase que nunca existiu.
- **Publicação na Oracle Cloud Free Tier (São Paulo):** `VM.Standard.E2.1.Micro`
  (x86, 1 OCPU/1 GB), porque o A1.Flex estava sem capacidade. IP
  `64.181.167.174`, usuário `ubuntu`. A VCN foi criada pelo assistente
  "Create a VCN with internet connectivity": criar a subnet dentro do fluxo da
  instância trava o IP público desabilitado. Toda porta precisa de regra nas
  duas camadas, iptables (`netfilter-persistent`) e Security List. Os serviços
  rodam como o usuário de sistema `residenciamed`. O `.env.production` foi
  gerado no próprio servidor a partir do `secrets.toml`, sem o segredo passar
  pelo terminal local.
- Sem domínio na época: sem HTTPS, `COOKIE_SECURE=false`, e o Streamlit numa
  porta própria (8080) liberada só para o IP do admin (/32). Abrir a 8080 para
  `0.0.0.0/0` foi bloqueado pelo classificador de segurança, e o bloqueio
  estava certo: a senha do admin trafegaria em texto claro. Se o IP do admin
  mudar, atualizar a regra ou usar túnel SSH (`DEPLOY.md` §2).

### 2026-09-13
- **Nome "Conduta"** no título, login, menus e API. Identificadores internos
  (usuário systemd `residenciamed`, serviços, cookie, e-mail da demo, paths)
  ficaram iguais porque mudar quebraria deploy e sessões abertas.
- **HTTPS via DuckDNS:** domínio pago descartado por custo.
  `conduta.duckdns.org` e `admin.conduta.duckdns.org` já apontam para o
  servidor; a config está commitada (`59cd72a`, `f8bb4d1`), falta aplicar (ver
  Pendências).
- **Redesign "Triagem"** do app do aluno (`DESIGN_TRIAGEM.md`). Escolhido
  depois de duas rodadas de protótipo: "Marca forte" agradou, mas parecia
  concorrente; na segunda, Triagem venceu "Traçado" (ECG) e "Sinalização". A
  escala de classificação de risco do pronto-socorro (t1–t5) é a marca e só
  aparece quando significa nível. Junto saiu o rail lateral (barra superior
  com abas, modo foco nas sessões) e foi corrigida a classe
  `transition-hover`, que nunca existiu no Tailwind.
- **+187 questões oficiais** (Revalida 2025-1 e 2023-2): de 458 para 645.
  Explicações escritas do zero, 10 questões com imagem. A Q55 da 2023-2
  ficou fora por depender de charge de jornal.
- **Simulado por prova oficial:** refaz um caderno inteiro na ordem original,
  3 min por questão (ritmo do INEP: 100 questões em 5 h), sem as anuladas.
  `edicao`/`numero_prova` foram preenchidos casando o texto do banco com os
  PDFs; as ids 206, 258 e 381 (reextraídas à mão antes) foram conferidas
  lendo. A prova em andamento pode ser retomada, porque dura horas.
- **ENAMED 2025 corrigido:** as 90 questões eram versões resumidas das
  originais, apesar do selo de prova oficial. O texto do caderno 1 do INEP
  entrou no próprio registro (UPDATE, não DELETE) para preservar as 173
  respostas e as revisões dos alunos. O gabarito definitivo bateu nas 90;
  7 explicações ajustadas e 3 imagens anexadas.
- **Taxonomia grande área > especialidade:** a sincronização do MediaFire
  criava uma área por pasta, e o filtro misturava grandes áreas com
  "Aprenda Nefro" e "CardioPapers ECG". Decisão do usuário: dois níveis, com
  Psiquiatria dentro de Clínica Médica. As 645 questões foram reclassificadas
  lendo o conteúdo: 212 mudaram de grande área, a maioria estava em Clínica
  Médica sem ser. Resultado: CM 180, GO 137, Cirurgia 119, Preventiva 105,
  Pediatria 104 (cirurgia pediátrica ficou em Cirurgia). O Painel agrega por
  grande área, então o histórico dos alunos por área mudou junto. Módulos do
  MEDCURSO viraram assuntos com nome legível; os que são a própria
  especialidade (Neuro, Psiquiatria, Ortopedia, Neonatologia, Vigilância,
  Trauma) ficaram sem assunto, e a sincronização repete essa regra. 23 áreas
  antigas vazias foram apagadas. A id 304 tinha a explicação de outra questão;
  foi achada comparando o vocabulário da explicação com o do enunciado, e foi
  o único caso.
- **Movimento na interface:** o usuário achou a plataforma "dura" (clique e a
  tela troca seca). Caiu a regra "nada anima sozinho ao carregar" do
  `DESIGN_TRIAGEM.md`; entrou um vocabulário curto (§3): telas sobem ao
  entrar, casos deslizam, menus e diálogos entram e saem, o Painel monta em
  cascata. Sem biblioteca de animação: keyframes do Tailwind e dois ganchos
  (`usePresenca`, `useContagem`). Materiais passou a manter a tabela anterior
  esmaecida ao filtrar (`keepPreviousData`) em vez de piscar o esqueleto.
- **Leitura do caso:** o usuário achou enunciado e discussão cansativos. Três
  ajustes, cada um medido com o texto real: (1) um limite em ch no parágrafo
  deixava um vão à direita das alternativas; saiu, e a coluna das sessões foi de
  840 para 680px (linha de 85/98 caracteres para ~63/68). (2) Ainda cansava:
  numa página de comparação com o mesmo caso, o usuário escolheu entre Archivo
  atual, Archivo aberta, Literata e Atkinson Hyperlegible a **Archivo aberta**
  (largura 108% do eixo variável, mais entrelinha), que mantém a identidade.
  (3) Discussão em parágrafos: nenhuma das 645 explicações tem quebra de linha
  (média de 746 caracteres), então a quebra é feita na exibição
  (`lib/paragrafos.ts`), sem mexer no banco. A regra foi testada nas 645 antes
  de entrar: 10 continuam em um parágrafo (uma frase enorme só), as demais em 2
  a 5, parágrafo mediano de 206 caracteres.
- **Fila da Revisão sem questões nunca respondidas:** a aba mostrava 34 e a
  tela "624 restantes". A contagem era só das vencidas, mas a fila (regra da
  primeira versão, de quando o banco era pequeno) somava todas as questões do
  banco sem registro de revisão — como responder no Praticar/Simulado já agenda
  a revisão, eram as 591 que o aluno nunca respondeu. Agora a fila é vencidas +
  marcadas, e aba, Painel e tela contam a mesma coisa
  (`repeticao_espacada.contar_fila_revisao`). Questões novas ficam no Praticar.
- **Revisão que mede (fase 1 de 3):** o usuário quis dar foco à repetição
  espaçada e ligá-la à evolução do aluno. Diagnóstico: `revisao` só guardava o
  estado atual (sem histórico), a Revisão era autoavaliação sem responder, e os
  botões prometiam prazos fixos que o SM-2 não seguia. Decisões do usuário:
  começar só pela fase 1, e o aluno volta a responder as alternativas. Entrou:
  `revisao_eventos` (uma linha por avaliação, de qualquer origem), SM-2 como
  função pura (`calcular_proximo_estado`) usada tanto para gravar quanto para
  prever o prazo de cada botão, gabarito decidindo a nota de erro, atalhos 1–3
  e resumo da sessão. Fases seguintes, feitas depois: (2) carga sob controle —
  meta diária priorizando atrasadas/difíceis, estimativa de tempo pelo tempo
  real do aluno, previsão de 7 dias no Painel, espalhar agendamentos; (3)
  evolução — retenção por semana e especialidade, estágios dos casos
  (aprendendo/consolidando/consolidado ≥ 21 dias), "recuperados", resumo semanal.
- **Carga sob controle (fase 2 de 3):** meta diária de revisão por aluno (padrão
  20, 10/20/30/50 no Painel) — a tela oferece só o que cabe no que falta dela, em
  ordem de prioridade (reaprendendo, marcadas, mais atrasadas em relação ao
  intervalo, menor facilidade); o resto espera, e "Revisar mais 10" é opt-in. A
  aba e o Painel contam os casos de hoje dentro da meta. Duração estimada pela
  mediana do tempo real do aluno, só com tempos plausíveis (15 s a 15 min) e ao
  menos 10 medidas; senão, 90 s. Sem esse filtro a primeira versão estimou 20
  casos em 2 min: das 35 respostas com tempo no banco, 29 tinham menos de 15 s.
  Os testes dessa estimativa acharam um bug antigo do SM-2: sem teto, o
  intervalo multiplica sem fim e ~26 acertos seguidos estouram `datetime`
  (OverflowError). Teto de 36.500 dias, o padrão do Anki — não muda nenhum prazo
  real. Um teto ligado à data da prova seria decisão de produto, não tomada. Previsão de 7 dias no
  Painel simulando o que sobra de um dia para o outro. Ficou de fora, de
  propósito, a variação aleatória dos intervalos: quebraria a garantia da fase 1
  (prazo do botão = prazo agendado), e a meta já absorve os picos.
- **Evolução da memória (fase 3 de 3):** seção no Painel e frase no resumo da
  Revisão, com todas as definições numa função só
  (`repeticao_espacada.classificar_eventos`). Teste de memória = caso que voltou
  depois de pelo menos 1 dia sem ser visto, de qualquer origem; o tempo sem ver
  sai do estado antes do evento (acerto agendou `intervalo_antes` dias, erro 10
  min, mais `atraso_dias`), porque o evento não guarda quando foi a avaliação
  anterior. Recuperado = primeiro teste lembrado depois de um erro (repetições 0
  antes também conta, o que pega erros de antes do histórico). Consolidado =
  intervalo ≥ 21 dias, o corte "mature" do Anki (4º acerto seguido). Estágios
  saem do estado atual de `revisao`; retenção, recuperados e consolidados, do
  histórico. Semanas são blocos de 7 dias terminando hoje, não semanas do
  calendário, para o bloco atual ser o mesmo período da frase "últimos 7 dias".
  Retenção só vem de `revisao_eventos`, sem misturar `respostas`: em 2026-09-14 o
  histórico estava vazio (começou na fase 1) e `respostas` tinha 1 resposta
  repetida com 1 dia de distância na conta real, então não valia duas fontes.
  Até o aluno revisar, a seção mostra os estágios e estados vazios que explicam
  quando cada número aparece. A conta demo ganhou histórico de revisão com
  `scripts/seed_demo_revisao.py` (idempotente, uma transação, simula sem
  `--aplicar`; `--refazer` salva em `backups/` e gera de novo): as 400 respostas
  passam pelo SM-2 real e há 55 sessões de Revisão sintéticas, sem mexer em
  `respostas`. A primeira versão (meta 20, 3 dias pulados em 10) acumulou fila e
  a previsão da demo ficou toda acima da meta; refeita com meta 30 gravada na
  demo, 9 de 10 dias e "Revisar mais 10" quando sobra um lote.

### 2026-09-14
- **Revalida 2025/2 e 2026/1:** +149 questões (de 645 para 794). O padrão de
  nome anotado para os PDFs do INEP estava errado (é `2025_1_…`, com
  sublinhado), e a partir da 2025/2 os arquivos viraram `{ed}_caderno_1…`; as
  abas por ano da página do INEP trazem os links no próprio HTML. A nota de
  gabarito do INEP confirmou que o Revalida 2025/2 e o ENAMED 2025 aplicaram as
  mesmas questões 1–50, e 43 delas já estavam no banco como ENAMED. Decisão do
  usuário: não duplicar. A tabela `questoes_provas` liga uma questão a mais de
  um caderno, e simulado oficial, lista de edições e filtro de banca leem dela;
  as colunas `questoes.edicao`/`numero_prova` ficaram com o caderno principal
  porque o servidor ainda roda código que lê só elas. A 2025/2 ficou com 93
  questões (50 novas; 7 anuladas) e a 2026/1 com 99 (nenhuma anulada; a Q5
  ficou fora por depender de foto de livro de terceiros). 6 imagens novas,
  tabelas reescritas em prosa, explicações escritas do zero e conferidas contra
  a letra oficial. Backup em `backups/importacao_revalida_2025-2_2026-1_*.json`.
- **Provas das faculdades de SP:** das pedidas, só duas cabem no banco. A
  FUVEST publica apenas a edição atual da USP (2026); os cadernos AD1 a AD3 são
  as mesmas 120 questões em ordens diferentes, e entrou o AD1 com 113 questões
  (fora as 2 anuladas, as 3 com duas respostas aceitas e as 2 cuja imagem o
  próprio caderno removeu pelo ECA). Da UNICAMP entrou 2023 (versão W, 79
  questões): de 2024 em diante o acesso direto é de respostas curtas, sem
  alternativas. A UNIFESP não publica o caderno e a Santa Casa só mostra com
  login de candidato, então ficaram de fora. Decisão do usuário: questões com
  alternativas em imagem entram com a figura rotulada (A) a (D) e o texto
  "Imagem A" a "Imagem D". Bancas "USP" e "UNICAMP". Tabelas perdidas na
  extração foram reescritas a partir da página renderizada (a Q51 da USP tinha
  as alternativas deslocadas). Banco de 794 para 986 questões. Backup em
  `backups/importacao_usp2026_unicamp2023_*.json`.
- **Limpeza de código morto** (auditoria de excesso, `b0d9a2e`, −1.914 linhas):
  saíram as telas de aluno antigas do `app.py` com os helpers e o CSS só delas;
  o `mediafire_cache.py` e a coluna Tamanho (nenhum dos 1646 materiais tinha
  arquivo em cache, a coluna mostrava sempre "—"); os endpoints admin da API
  que nenhum cliente chamava (escrita de questões, materiais, áreas e
  sincronização; prova-alvo), com `exigir_admin` e o `python-multipart`;
  funções sem chamador em `db.py`; e o `HANDOFF_REDESIGN.md`. A tela Materiais
  do Streamlit ficou, no grupo Acervo, porque é nela que o admin cadastra e
  exclui materiais, e a página inicial do Streamlit virou Banco de questões.
  Ficaram de propósito o `GET /questoes/{id}/distribuicao` (o Praticar usa) e
  as colunas de cache em `materiais`, que existem em produção. Não aplicado,
  por ser decisão do usuário: trocar o rail e a barra superior feitos à mão do
  Streamlit por `st.navigation`, o que contraria o escopo do `REDESIGN.md`.
- **Materiais fora da plataforma, por enquanto.** Decisão do usuário: o foco
  passou a ser o desempenho e a evolução do aluno (questões, simulados,
  revisão, pontos fracos). Saíram a aba Materiais do app, as telas Materiais e
  Sincronizar MediaFire do Streamlit, o `mediafire_import.py`, os routers
  `materiais` e `sincronizacao`, os materiais da busca global e do `/me`, as
  funções de materiais do `db.py` e a dependência `requests`. O banco não foi
  mexido: a tabela `materiais` (1646 linhas) e a coluna `subtopicos.origem`
  continuam lá, sem código, porque o servidor ainda roda a versão antiga e o
  recurso pode voltar — o caminho é reverter o commit que os removeu.

## Armadilhas das telas admin (Streamlit)

- `st.markdown('<div>')` … `st.markdown('</div>')` não envolve nada: cada
  chamada vira elemento irmão. Para estilizar um widget, mirar a classe
  `st-key-<key>` do `.stElementContainer`.
- `st.radio` é `[role=radiogroup] > label > span(input) + div(texto)`: para um
  indicador próprio, esconder o `span` e desenhar em `label::before`.
- `st.dialog` não herda o CSS da página: mirar `[data-testid="stDialog"] > div`
  com `background: var(--surface) !important`.
- `st.button(..., help=...)` insere um span entre `.stButton` e o `<button>`:
  usar seletor descendente, nunca `>`.
- `st.popover` sempre põe um ícone de seta no gatilho; esconder com
  `[data-testid="stIconMaterial"] { display: none }` escopado.
- A borda direita da sidebar tem uma faixa de resize invisível (~8 px, z-index
  do framework) que rouba cliques; nenhum z-index vence, posicionar por dentro.
- Largura/altura custom de botão na sidebar que "não pega": tentar
  `!important` antes de investigar mais.
- `st.bar_chart`/`st.line_chart` não herdam a cor do tema: passar `color=`.
- Clique por coordenada na automação do navegador pode errar elemento pequeno
  mesmo com DOM certo: testar com `.click()` via JS antes de concluir que é bug.
