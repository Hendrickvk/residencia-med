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
  não autorizada: a partir do outro PC, anexar o conteúdo de
  `~/.ssh/conduta-oracle.pub` deste notebook ao `~/.ssh/authorized_keys` do
  servidor; a alternativa é trazer para cá a chave original da instância
  (`ssh-key-2026-09-12.key`). Estado conferido em 2026-09-15: a host key
  ED25519 que o servidor apresenta é a esperada
  (`SHA256:c5q+FAcRSupd1hNDvfaGk6Su6oepMnb1cf+8DTQJN6A`) e já está no
  `known_hosts` deste PC, então a primeira conexão não vai perguntar nada;
  `ssh residencia-med` chega até a autenticação e volta
  `Permission denied (publickey)`, ou seja, falta só a autorização no servidor.
  A permissão da chave privada foi restringida ao usuário pela ACL do Windows
  (`icacls … /inheritance:r /grant:r`); o `ls` do Git Bash continua mostrando
  `-rw-r--r--`, que ali não reflete a ACL. Esperando esse deploy: HTTPS via
  DuckDNS, redesign Triagem, simulado por prova oficial e `questoes_provas`,
  taxonomia de especialidades, correção da conexão morta do Neon, revisão
  espaçada em 3 fases, a limpeza de código morto, a remoção dos materiais, os
  temas e o tipo de pergunta das questões e os 7 itens do acompanhamento do
  desempenho. Passos: `git pull`,
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
- Questões oficiais ainda fora do banco (a Revalida 2021 entrou em 2026-09-15):
  **Revalida 2020**, porque o INEP só publica o gabarito preliminar dos dois
  cadernos, e preliminar muda em anulação e em letra depois dos recursos;
  **Revalida 2022-1**, cujo caderno não tem mapa de caracteres — as fontes são
  subconjuntos com glifos "g87", sem ToUnicode, e pdfplumber e PyMuPDF devolvem
  lixo, de modo que só sairia por OCR, que exigiria instalar o Tesseract e
  revisar 100 enunciados clínicos número a número. **Revalida 2026/2** é só
  esperar: em 2026-09-15 o caderno 1 já estava publicado, mas o gabarito ainda
  era o preliminar; quando sair o definitivo, é importação direta com
  `scripts/importar_prova.py`. Também fora: edições
  anteriores da USP (a FUVEST só mantém a atual); UNICAMP de 2024 em diante
  (respostas curtas); UNIFESP e Santa Casa (caderno não público). O **ENARE**
  foi conferido em 2026-09-15 e não serve: a FGV publica 139 cadernos, todos de
  ano adicional, área de atuação, pré-requisito e multiprofissional, porque o
  acesso direto em medicina migrou para o ENAMED, que já está no banco. Sobram
  as provas estaduais e de instituições (SES-DF, SES-PE, SUS-SP, AMRIGS,
  IAMSPE), que dão volume de prática mas ficam fora do peso do INEP.
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
  1. Lista `db.TEMAS`, 209 temas (feita e aprovada). Na classificação entraram
     temas que faltavam, com aprovação do usuário: "Prolapso genital e
     incontinência urinária" (Ginecologia); em Pediatria clínica, diabetes e
     endócrino, vasculites e reumatologia, desenvolvimento e comportamento,
     síndromes genéticas e doenças digestivas; e "Malformações e síndromes
     genéticas no recém-nascido" (Neonatologia); em Infectologia pediátrica,
     infecções respiratórias agudas e infecções gastrointestinais e urinárias;
     e "Cirurgia bariátrica" (Cirurgia geral, não citada pelo nome na portaria,
     mas cobrada nas provas) e "Trauma de pelve, extremidades e partes moles"
     (Trauma), "Doenças da coluna vertebral" (Ortopedia) e "Trauma ocular e
     queimaduras químicas" (Oftalmologia), "História natural e determinantes
     do processo saúde-doença" (Epidemiologia) e "Imunização e profilaxia
     pós-exposição" (Vigilância) — os demais citados na Portaria
     540/2020, que a primeira lista tinha comprimido demais. Em Clínica Médica
     (2026-09-15, sem aprovação caso a caso) entraram "Cardiopatias congênitas
     no adulto" (Cardiologia), "Via aérea e acesso venoso central" (Emergências
     clínicas), "Sífilis e outras IST" e "Mononucleose, febre maculosa e outras
     infecções" (Infectologia), "Complicações e emergências oncológicas"
     (Oncologia), "Tromboembolismo pulmonar" (Pneumologia) e "Transtornos
     mentais na infância e adolescência" (Psiquiatria). Texto da portaria:
     `download.inep.gov.br/educacao_superior/revalida/portaria/2020/Portaria_540_17092020.pdf`.
  2. Temas no banco (feita): `init_db` grava os temas em `subtopicos`;
     `db.listar_temas` esconde os 44 assuntos antigos do MediaFire pelo campo
     `origem` (nenhum nome colide); a planilha e o formulário do Streamlit só
     aceitam temas existentes, e "Adicionar assunto" saiu.
  3. Classificar as 986 questões lendo o conteúdo, uma especialidade por vez,
     com simulação, backup e amostra revisada pelo usuário. Ferramenta:
     `scripts/classificar_temas.py <json>` (simula; `--aplicar` grava e salva
     backup); os JSONs de classificação ficam em `backups/temas_*.json`.
     Feito (2026-09-14): Ginecologia e Obstetrícia inteira — Obstetrícia (96),
     Ginecologia (92) e Mastologia (12); em Pediatria, Pediatria clínica (73) e
     Neonatologia (33), Infectologia pediátrica (30) e Puericultura (25) —
     Pediatria inteira; Cirurgia inteira (180: Cirurgia geral 57, Trauma 40,
     Urologia 18, Coloproctologia 16, Cirurgia pediátrica 15, Ortopedia 12,
     Oftalmologia 10, Otorrinolaringologia 6, Cirurgia vascular 6); Medicina
     Preventiva e Social inteira (159: Atenção primária 37, Vigilância 34,
     Epidemiologia 30, Ética 24, Políticas 21, Trabalhador 13). Em 2026-09-15,
     Clínica Médica inteira (286) numa sessão só, a pedido do usuário, sem
     amostra revisada: Psiquiatria 36, Infectologia 35, Cardiologia 32,
     Dermatologia 22, Gastroenterologia 22, Emergências clínicas 21,
     Endocrinologia 21, Neurologia 21, Pneumologia 17, Reumatologia 16,
     Nefrologia 13, Hematologia 10, Geriatria 9, Oncologia 6, Hepatologia 5.
     **Fase feita: 986 de 986 questões com tema.** Quando o tema certo era de
     outra especialidade da mesma grande área, a questão mudou de
     especialidade (o script passou a aceitar isso): 16 questões — emergência
     hipertensiva (922) e dislipidemia (399) para Cardiologia; hipocalcemia e
     hiponatremia (931, 189, 2297) para Emergências clínicas; cistite (194,
     332, 2398) para Nefrologia; lombalgia com sinais de alarme (971, 2411)
     para Reumatologia; demência vascular (1882) para Geriatria; encefalite
     herpética (2415) para Infectologia; Wernicke (1792) e arterite temporal
     cobrada como tipo de cefaleia (87) para Neurologia; tabagismo (1889, 2418)
     para Psiquiatria. Ficaram no tema mais próximo, sem tema próprio:
     hidradenite supurativa (300, Infecções de pele), dermatite seborreica
     infantil (359, Dermatoses alérgicas) e colangite esclerosante na
     retocolite (51, Doenças inflamatórias intestinais). Vale o usuário
     conferir os temas novos e essas mudanças.
  4. Filtro de tema no Praticar e tema no caso (feita, 2026-09-15). O
     Configurador ganhou o campo Tema, que depende da especialidade e só lista
     temas com casos (`GET /areas/{id}/temas`, contagem em `db.listar_temas`).
     Decisão do usuário: o tema não fica no cabeçalho antes da resposta, porque
     numa questão que pede o diagnóstico ele entregaria o gabarito (ex.:
     "Leptospirose, tétano e raiva"). Aparece como "Tema: …" na discussão do
     Praticar e da Revisão e no comentário do resultado do Simulado, e some
     durante a prova (`components/TemaDoCaso.tsx`).
  5. Estatística por tema: coberta pela estimativa ajustada do "Acompanhamento do
     desempenho", abaixo, que funciona com poucas respostas.
- **Acompanhamento do desempenho, em fases — os 7 itens estão feitos.** Decisão do usuário (2026-09-15):
  com os temas prontos, o foco passa a ser medir e melhorar o desempenho do
  aluno. Propostas, em ordem: (1) separar domínio (primeira resposta a cada
  questão) de memória (Revisão); (2) estimativa por tema que aguente pouca
  amostra; (3) prioridade = peso do tema na prova × lacuna; (4) tipo de pergunta
  (conduta, diagnóstico, exame) como segundo eixo — uma heurística na última
  frase do enunciado classifica ~70% do banco; (5) "acertei no chute" valer
  menos e tempo por item no Simulado; (6) Simulado como medida de prontidão
  (tendência, nota projetada, resultado por tema); (7) plano da semana com o
  antes e depois de cada tema. Fora, de propósito: TRI e modelos de previsão,
  sem alunos para isso (2 reais em 2026-09-15). Pesa em quase tudo a mediana de
  4 questões por tema: importar o Revalida 2020, 2021 e 2022-1 ajuda.
  1. Itens 1 a 3 (feita, 2026-09-15). Quadro, aproveitamento geral e acerto
     diário contam só a primeira resposta a cada questão
     (`db._PRIMEIRAS_TENTATIVAS`); na demo, 400 respostas com 58% de acerto
     viraram 203 questões com 51%. O domínio de um tema parte da especialidade
     (e ela, da área) com peso de 5 respostas (`db.estimar_dominio`). "Onde você
     ganha mais pontos", no Painel, mostra os 3 temas de maior fração dos
     cadernos do INEP × (1 − domínio) (`db.priorizar_temas`, pura e testada), com
     "Praticar {n}" já filtrado pelo tema. Limite conhecido: questão respondida
     pela primeira vez na Revisão (marcada sem responder) não entra no domínio,
     porque a Revisão só grava em `revisao_eventos`.
  2. Item 4 (feita, 2026-09-15). `questoes.tipo_pergunta` diz o que a questão
     pede, pelo que as alternativas são: Diagnóstico, Exames, Conduta ou
     Conceitos (`db.TIPOS_PERGUNTA`, validado no código, sem CHECK). Pedindo
     mais de uma coisa, vale a etapa mais adiante (Conduta > Exames >
     Diagnóstico). As 986 questões estão classificadas: a heurística na última
     frase acertou 74% e o resto foi corrigido lendo cada questão. Deu 566
     Conduta, 161 Diagnóstico, 143 Conceitos (83 deles de Preventiva, a única
     área com mais Conceitos que Conduta) e 116 Exames.
     `scripts/classificar_tipos.py` grava um JSON `{"tipos": {id: tipo}}`, com
     simulação e backup. No Painel, "Por tipo de pergunta" mostra o acerto na
     primeira resposta por tipo (`db.desempenho_por_tipo`) e aponta o ponto
     fraco quando o melhor e o pior diferem 15 pontos ou mais; no Praticar, o
     tipo virou filtro. Limite conhecido: o formulário e o importador do
     Streamlit não preenchem o tipo, e questão sem tipo fica fora do filtro e
     da seção.
  3. Item 5 (feita, 2026-09-15). No domínio, o acerto marcado como chute vale
     meio (`pontos` em `db._PRIMEIRAS_TENTATIVAS`), em todo o Painel; os
     acertos podem ter vírgula, e a legenda do quadro explica. Meio, e não zero:
     o chute costuma ser entre duas alternativas, e o SM-2 já o trata como
     acerto difícil (qualidade 3). O Simulado grava o tempo de tela de cada
     questão (`simulado_itens.tempo_ms`, `POST /simulados/{id}/tempo`): a tela
     soma as passagens e manda ao sair da questão, ao finalizar e quando a aba
     some, sem contar a aba escondida; finalizado, não muda mais. O resultado
     mostra o tempo médio por questão respondida contra o ritmo do simulado (3
     min na prova oficial), em quantas passou dele e o tempo de cada uma na
     revisão completa. O tempo segue para `respostas` e `revisao_eventos`, como
     no Praticar. Limites conhecidos: simulado antigo não tem tempo; no
     Simulado não há como marcar chute, então lá todo acerto conta inteiro.
     No QA pelo Chrome automatizado, a aba se declara escondida
     (`document.hidden`, mesmo com foco) e o tempo não conta: para testar,
     forçar `document.hidden` falso na página antes de começar a prova.
  4. Item 6 (feita, 2026-09-15). "Nota projetada na prova" no Painel
     (`db.projetar_nota`, pura e testada): o domínio estimado de cada tema, o
     mesmo das prioridades, pesado pelas questões de caderno do INEP do tema,
     com faixa de 95% que soma a incerteza das respostas à variação de uma
     prova de 100 questões (por isso nunca fica abaixo de uns 10 pontos para
     cada lado). Aparece a partir de 50 questões respondidas
     (`VOLUME_CONFIAVEL`, o mesmo do título do Painel). Ao lado, as provas
     oficiais feitas, com quantas questões o aluno já tinha visto antes de
     começar: o banco é feito dos próprios cadernos, e nessas a nota mede
     memória. Só a prova oficial entra, porque só ela é feita em condição de
     prova. No resultado do Simulado, "Temas para revisar" lista os temas com
     erro ou em branco, com "Praticar" já filtrado. Achado no caminho:
     `GET /simulados/{id}/desempenho` devolvia o acerto por área durante a
     prova, o que entregava o gabarito; agora ele e o novo `/temas` só
     respondem depois de finalizado. Limites conhecidos: a faixa usa a
     aproximação binomial e sai um pouco estreita quando as respostas se
     concentram em poucos temas; edições têm dificuldades diferentes, e nada
     aqui corrige isso; nenhuma prova oficial tinha sido feita até
     2026-09-15. Conferido no navegador no mesmo dia, com dois simulados de
     teste de 10 questões na conta demo.
  5. Item 7 (feita, 2026-09-15). "O que mudou nesta semana" no Painel
     (`db.progresso_semana`): desde segunda-feira, as questões novas de cada
     tema praticado, o domínio estimado antes e agora e o que a Revisão cobrou
     do tema na semana (`repeticao_espacada.retencao_por_tema`, a mesma
     definição de teste de `classificar_eventos`). O "plano da semana" da
     proposta virou isto mais a seção de prioridades, que já lista os temas e
     abre o Praticar: uma lista congelada toda segunda seria uma cópia quase
     igual dela na mesma tela. Limites conhecidos: o "antes" são as respostas
     até segunda, então quem começou nesta semana fica só com o agora; o
     domínio estimado se move devagar de propósito (encolhimento); e a seção
     some quando a semana ainda não teve questão nova. Com ele, a lista dos 7
     itens fecha.

### Próximos passos sugeridos (enquanto o deploy espera)
Levantados em 2026-09-14, em ordem de valor. O deploy continua sendo o item
mais importante assim que houver acesso SSH.

**Onde paramos (2026-09-15).** Os 7 itens do acompanhamento do desempenho estão
feitos, a Revalida 2021 foi importada (banco em 1 074 questões) e os passos 4, 5
e 6 desta lista saíram. A próxima tarefa é o **passo 3, o QA no navegador das
questões com figura**: depende de @browser e do login feito pelo usuário (conta
de QA ou demo, senha da demo no `DEPLOY.md`), e entram nele também as três
figuras novas da Revalida 2021 — questões 41, 99 e 100 —, conferidas só como
recorte, nunca dentro do app. Para subir o ambiente: `uvicorn api.main:app
--port 8000` na raiz e `npm run dev` em `frontend/`. Nada do que foi feito desde
13/09 está no servidor: o deploy segue bloqueado por SSH. Há também uma
brincadeira de boas-vindas para uma conta específica
(`frontend/src/lib/brincadeira.ts`, diálogos mostrados uma vez por navegador,
e-mail guardado só como hash): a ideia fica, mas o texto é provisório e ainda
será revisto.

1. **Próxima edição do ENAMED.** É a prova que faz hoje a seleção de acesso
   direto e entra no peso do INEP que alimenta as prioridades e a nota projetada
   do Painel, então é a coleta de maior valor. As abas por ano da página do INEP
   (`…/revalida/provas-e-gabaritos/{ano}`) trazem os links dos PDFs no próprio
   HTML; foi assim que 2025/2, 2026/1 e a 2021 foram achadas depois de o padrão
   de nome falhar. Seguir o roteiro do `CLAUDE.md` e gravar com
   `scripts/importar_prova.py`. A USP precisa ser coletada todo ano, porque a
   FUVEST só mantém a edição corrente no ar.
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
4. **Tempo do simulado oficial por banca** (conferido em 2026-09-15; nada a
   mudar). Todas as bancas do banco usam o mesmo ritmo de 3 minutos por questão:
   Revalida, 100 questões em 5 h; UNICAMP 2023, 80 em 4 h; e a USP, que era a
   dúvida, 120 questões em 6 h, segundo as instruções do próprio caderno AD1 de
   2026 — a conta antiga desconfiava de diferença porque partia das 113 questões
   que entraram no banco, e não das 120 do caderno. Do ENAMED o Inep não publica
   a duração (não está na página do exame, nas perguntas frequentes, na
   legislação nem na nota de gabarito), e como metade das questões de 2025 é a
   mesma da Revalida 2025/2, fica valendo o ritmo do INEP. Guardar ritmo por
   banca só se aparecer prova com ritmo diferente.
5. **Questões comuns a mais de uma prova** (feito, 2026-09-15). São 43, todas
   entre o ENAMED 2025 e o Revalida 2025/2, e o selo mostrava só um caderno
   porque saía de `questoes.banca`/`ano`. Agora `db.provas_das_questoes` devolve
   os cadernos de um lote de questões numa consulta só,
   `serialize.questoes_publicas` anexa a lista a toda questão que sai da API
   (Praticar, Revisão e Simulado passam por lá) e o selo mostra todas —
   "Revalida 2025/2 · ENAMED 2025" —, caindo para banca + ano quando a questão
   não veio de caderno oficial.
6. **Importador reutilizável em `scripts/`** (feito, 2026-09-15). Os scripts das
   importações de 2026-09-14 ficaram no scratchpad da sessão e se perderam;
   agora existe `scripts/importar_prova.py`, que recebe o JSON montado
   (enunciado, alternativas, gabarito, área, especialidade, tema, tipo,
   explicação, imagem, banca, edição e número), valida os nomes contra a
   taxonomia, recusa duplicata pelo início do enunciado e número repetido na
   edição, simula por padrão e, com `--aplicar`, grava questões e vínculos de
   `questoes_provas` numa transação, com backup dos ids em `backups/`. Armadilha
   achada na estreia: `db.obter_tema` devolve a linha do tema, não o id, e a
   simulação não pega esse tipo de erro porque não chega a montar o INSERT.

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

### 2026-09-15
- **Revalida 2021 importada:** +88 questões, de 986 para 1074. Das 100 do
  caderno 1, 12 foram anuladas pelo INEP e ficaram de fora; o gabarito usado é o
  definitivo. A extração saiu por recorte de coluna com pdfplumber, mas a
  questão 100 precisou de leitura em largura total, porque a figura ocupa a
  página inteira e o corte por coluna embaralhou o texto. Armadilha nova do
  parser: linha de enunciado que começa com "A " (como "A conduta indicada é")
  era lida como alternativa A e sumia do enunciado — passou a valer só a
  sequência A–D completa, e a última delas. As figuras das questões 41, 99 e 100
  foram recortadas e conferidas uma a uma: o primeiro recorte da 100 pegou a
  primeira alternativa junto do eletrocardiograma, o que entregaria a resposta,
  e o da 41 cortava a legenda no meio. Explicações escritas do zero, com
  checagem automática de que cada uma defende a letra oficial (uma não citava a
  alternativa e foi corrigida). Backup dos ids em
  `backups/importacao_revalida_2021_*.json`.
- **Duas explicações corrigidas na revisão clínica** das cinco marcadas em
  2026-09-14; as outras três estavam certas. Na Revalida 2025/2 Q91 (id 1803), o
  texto defendia o gabarito dizendo que o Mycoplasma incuba 2 a 3 semanas, o que
  não é exato (1 a 4 semanas): agora defende a letra oficial pelo padrão
  radiológico e pelo contexto de aglomeração e diz ao aluno que o Mycoplasma é o
  diferencial clássico nessa idade. Na USP 2026 Q116 (id 2405), o SIU de
  levonorgestrel aparecia como escolha pacífica: o texto agora registra que,
  pelos critérios de elegibilidade da OMS, com anticorpos antifosfolípides o DIU
  de cobre é categoria 1 e o SIU é categoria 3 no início do uso, de modo que a
  outra alternativa é defensável. Correção por UPDATE, com o texto anterior em
  `backups/correcoes_explicacoes_*.json`.

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
