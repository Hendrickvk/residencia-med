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
  simulado por prova oficial e taxonomia de especialidades. Passos: `git pull`,
  rebuild do front, no `.env.production` `COOKIE_SECURE=true` e
  `CORS_ORIGENS=https://conduta.duckdns.org`, copiar o Caddyfile, reload do
  caddy, restart de api e streamlit, testar, só então fechar a 8080 (iptables
  **e** Security List) e atualizar o `DEPLOY.md`.
- Enquanto o deploy não sai, o servidor roda código antigo sobre o banco já
  migrado: Materiais lá mostra só as 5 grandes áreas, sem especialidades.
- Questões oficiais ainda fora do banco: Revalida 2020, 2021 e 2022-1 (PDFs
  fora do padrão de nome do INEP, não localizados) e provas de USP, UNIFESP,
  ENARE e hospitais.
- Se o shape ARM `VM.Standard.A1.Flex` (1 OCPU/6 GB, Always Free) aparecer em
  São Paulo e 1 GB apertar, recriar a instância nele.
- Tema escuro do Triagem só existe por tokens, sem protótipo próprio.

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
Especificado em `REDESIGN.md`, detalhado em `HANDOFF_REDESIGN.md`. Hoje só
governa as 4 telas admin.

### 2026-09-12 — migração para FastAPI + React e publicação
- Motivo: acabamento visual em Streamlit exigia CSS frágil a cada atualização,
  e o objetivo número 1 era feedback instantâneo na resposta (daí o lote
  inteiro com gabarito em `GET /praticar/sessao`). Antes de codar, o contrato
  função→endpoint do `MIGRACAO.md` foi conferido contra o código real.
- As 4 telas admin ficam no Streamlit para sempre: um único admin usa, a
  reescrita é cara e não melhora nada para o aluno (`MIGRACAO.md` §4/§5).
  As telas de aluno antigas continuam no `app.py`, sem uso; limpar não
  compensou o risco.
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
