# Histórico de decisões — Conduta

Resumo do **porquê** das decisões que continuam valendo, pendências e
armadilhas das telas admin. Regras, comandos e arquitetura atuais ficam no
`CLAUDE.md`; o histórico superado (paletas antigas, telas de aluno em
Streamlit, transcrições) só existe no git, no antigo `contextoconversaclaude.txt`.

## Pendências

- **O que sobrou do deploy (2026-09-22).** O servidor está em dia — HTTPS,
  código e variáveis conferidos (ver `DEPLOY.md` §2 e §8). Três coisas não
  dependem de código e continuam abertas: **trocar a senha do
  `demo@residenciamed.com`**, que foi publicada e ainda funciona; **login real
  no navegador pelo https**, já que o resto foi verificado por curl; e limpar a
  regra de ingresso da porta **8080** na Security List da Oracle, que não expõe
  nada (nada escuta lá) mas ficou para trás.
- **Domínio próprio, agora com dois motivos (2026-09-19).** A decisão de não
  pagar domínio foi tomada quando o único uso era HTTPS, que o DuckDNS resolve
  de graça. O e-mail de redefinição de senha criou o segundo motivo, e o
  DuckDNS não atende: ele aceita **um único registro TXT**, já ocupado pelo
  ACME do certificado, e autenticar domínio no Brevo pede 2 a 3 registros
  (DKIM e DMARC). Consequência hoje: o Brevo reescreve o remetente para
  `hendrickvk@12189774.brevosend.com` — porque `From:` de freemail sem domínio
  autenticado quebraria o DMARC do Gmail — e o nome de exibição "Conduta" é o
  que segura a aparência. Funciona e entrega (conferido em 18 e 19/09), mas o
  endereço é feio e a entrega depende da boa vontade do filtro alheio.
  Caminhos, do mais barato ao melhor:
  1. **Ficar como está.** Zero custo. Nome "Conduta" na caixa de entrada,
     endereço `@…brevosend.com` no cabeçalho, risco de spam que até agora não
     se materializou (o teste foi aberto na caixa de entrada).
  2. **Domínio grátis com DNS próprio** (`is-a.dev`, `eu.org`): permite DKIM e
     DMARC, resolve o e-mail, aprovação por pull request e nome com cara de
     projeto de dev. Não resolve bem o site, porque o certificado e o endereço
     público ficariam num domínio de terceiro com cara informal.
  3. **Domínio pago barato** (~R$ 40/ano num `.com.br`, ou US$ 5–12 num
     `.site`/`.com`): resolve os dois de uma vez — `acesso@conduta.xxx` com
     DKIM alinhado **e** HTTPS no lugar do DuckDNS, aposentando o
     `conduta.duckdns.org` e o `deploy/Caddyfile` que depende dele.
  Enquanto nada disso for decidido, o fluxo de senha está completo e
  funcionando; o que muda com o domínio é só o valor de `EMAIL_REMETENTE` (e
  os registros de DNS), não o código.
- **Backup fora da máquina: feito; falta agendar (2026-09-20).** O banco tem
  cópia num repositório privado do GitHub (`Hendrickvk/conduta-backups`),
  conferida no remoto. O que resta é uma linha, no PowerShell do usuário, para
  que isso aconteça sem ninguém lembrar:

      schtasks /create /tn "Conduta - backup semanal" /tr "C:\Users\Hendrick\Documents\Codes\residencia-med\scripts\backup_semanal.cmd" /sc weekly /d SUN /st 19:00

  Duas ressalvas conhecidas: com a máquina desligada no horário, o Agendador
  **pula** a execução em vez de adiar (a caixa "Run task as soon as possible
  after a scheduled start is missed" fica nas propriedades da tarefa, só pela
  interface), e o único sinal de que o backup parou de acontecer é o
  `backups/backup_semanal.log` — vale olhar de vez em quando.

  Em aberto, se um dia houver alunos em volume: cifrar o dump antes de subir
  (`age`, ou 7-Zip com AES). Hoje não compensa — perder a senha de cifra
  transforma o backup em nada, o que é pior que o risco que ela evita num
  repositório privado de uma conta com 2FA.
- **Dados pessoais dela num repositório público (2026-09-20).** O
  `frontend/src/lib/brincadeira.ts` tem nome completo, gostos pessoais, o nome de
  outra pessoa e o SHA-256 do e-mail dela. Ela não sabe que isso está público, e
  quem achar o repositório também estraga a surpresa. Três caminhos:
  1. **Tornar o repositório privado.** Resolve isto, o histórico da senha
     publicada, o e-mail e qualquer coisa futura de uma vez. **Não é só um
     clique**: o servidor clonou por HTTPS anônimo e atualiza com `git pull`,
     que passa a falhar — precisa de uma chave de deploy só de leitura, e os
     comandos estão no `DEPLOY.md` (§3). Como o deploy já está parado por falta
     de SSH, o custo real é fazer isso na mesma visita ao servidor.
  2. **Mover o roteiro para trás de autenticação**: um endpoint que só devolve o
     texto para a conta dela (a comparação do hash passa a ser no servidor), com
     o roteiro num arquivo fora do git. Resolve de verdade, inclusive para quem
     baixa o bundle do site — que é público mesmo com o repositório privado — ao
     preço de um arquivo a mais no deploy e de um jeito novo de a brincadeira
     falhar calada (arquivo ausente no servidor).
  3. Não fazer nada: o risco é alguém achar o repositório antes dela ver a
     brincadeira.
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
     tipo virou filtro. O limite conhecido (o formulário e o importador do
     Streamlit não preenchiam o tipo, e questão sem tipo fica fora do filtro e
     da seção) foi fechado em 2026-09-17: os dois passaram a exigir o tipo.
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

**Onde paramos (2026-09-18).** Os 7 itens do acompanhamento do desempenho estão
feitos, a Revalida 2021 foi importada (banco em 1 074 questões) e os passos 2, 3,
4, 5 e 6 desta lista saíram. **A revisão das explicações foi encerrada: 1 074 de
1 074 lidas, 51 reescritas, nenhuma marcação pendente** (resumo por edição no fim
do passo 2). Com isso, o único passo desta lista que sobra é o 1, e ele está
bloqueado. O **passo 1, a próxima edição do ENAMED**, está
bloqueado até 04/12/2026: a prova foi aplicada em 13/09 e o INEP só publicou o
gabarito preliminar, que muda em anulação e em letra depois dos recursos (a
Revalida 2026/2 está no mesmo estado). Para subir o
ambiente: `uvicorn api.main:app --port 8000` na raiz e `npm run dev` em
`frontend/`. Nada do que foi feito desde
13/09 está no servidor: o deploy segue bloqueado por SSH. Há também uma
brincadeira de boas-vindas para uma conta específica
(`frontend/src/lib/brincadeira.ts`, mostrada uma vez por navegador, e-mail
guardado só como hash). Reescrita em 2026-09-18: um alerta de ameaça como ato
de abertura, com as linhas da varredura aparecendo uma a uma, e oito diálogos
de frase curta em que os botões são a fala da convidada.

1. **Próxima edição do ENAMED.** É a prova que faz hoje a seleção de acesso
   direto e entra no peso do INEP que alimenta as prioridades e a nota projetada
   do Painel, então é a coleta de maior valor. As abas por ano da página do INEP
   (`…/revalida/provas-e-gabaritos/{ano}`) trazem os links dos PDFs no próprio
   HTML; foi assim que 2025/2, 2026/1 e a 2021 foram achadas depois de o padrão
   de nome falhar. Seguir o roteiro do `CLAUDE.md` e gravar com
   `scripts/importar_prova.py`. A USP precisa ser coletada todo ano, porque a
   FUVEST só mantém a edição corrente no ar.
2. **Revisão clínica das explicações — encerrada em 2026-09-18** (1 074 de
   1 074, 51 reescritas). Começou em 2026-09-16 pela USP 2026 e terminou pela
   Revalida 2021; o resumo por edição está no fim deste passo.
   **Resultado da USP 2026: 113 de 113 lidas, 10 marcadas e as 10 reescritas
   em 2026-09-16.** As letras guardadas no banco foram conferidas contra o
   gabarito oficial retificado da FUVEST e as 113 batem — o dado está íntegro, o
   problema é texto. A marcada mais grave é a **Q22 (id 2317)**: a explicação
   defende a alternativa A e descarta explicitamente a B, que é o gabarito, de
   modo que quem estuda por ela erra a questão. Quatro descrevem errado o que
   está na imagem (Q11 id 2306, Q40 id 2335, Q41 id 2336, Q64 id 2356) e cinco
   são de clareza ou lacuna (Q2 id 2297, Q44 id 2339, Q88 id 2380, Q101 id 2393,
   Q111 id 2401). As notas de cada uma estão em
   `backups/revisao_explicacoes.json` e aparecem na tela Revisar explicações.
   Lição que vale para o resto: a checagem automática que o `CLAUDE.md` descreve
   ("cada explicação defende a letra oficial") não pegou a Q22 — não dá para
   confiar nela sozinha. As cinco de gabarito discutível já
   saíram em 15/09 (duas corrigidas, três conferidas e certas). O que resta são
   as ~500 explicações escritas do zero naquele dia (Revalida 2025/2 e 2026/1,
   USP 2026, UNICAMP 2023), que só passaram pela checagem automática de que cada
   uma defende a letra oficial — isso não pega raciocínio clínico ruim
   defendendo a letra certa, e por isso depende de leitura do usuário.
   **Resultado da Revalida 2025/2 (2026-09-17): 93 de 93 lidas, 4 reescritas**
   (texto anterior em `backups/explicacoes_20260917_201155.json`, que também
   guarda a correção de uma grafia na ENAMED Q4).
   Só 50 eram inéditas — as outras 43 são as mesmas questões do ENAMED 2025, já
   revisadas em 16/09 e marcadas ok. A leitura achou 1 erro factual e 3 lacunas:
   a Q58 (id 1772) afirmava "CHA2DS2-VASc zero" numa mulher de 30 anos, quando o
   sexo feminino vale 1 ponto (conclusão de não anticoagular não muda, a conta
   ensinada estava errada); a Q49 (id 48) não tinha a ressalva dos critérios da
   OMS que a USP Q116 ganhou em 15/09; a Q8 (id 80) deixava passar que o padrão
   pontilhado fino denso (anti-DFS70) depõe contra doença autoimune sistêmica; e
   a Q5 (id 49) atribuía ao S. schenckii a esporotricose do gato, que no Brasil é
   do S. brasiliensis. As 4 figuras da edição foram abertas uma a uma e batem com
   o texto. **Achado que vale para o resto:** as 3 lacunas estavam em questões já
   marcadas ok na primeira passada, ou seja, reler questão já revisada rende
   lacuna, não defeito — vale a pena quando uma questão irmã recebeu correção
   que a outra não recebeu, não como auditoria geral.
   **Resultado da UNICAMP 2023 (2026-09-17): 79 de 79 lidas, 5 corrigidas**
   (textos em `backups/explicacoes_20260917_202535.json`, imagem em
   `backups/imagem_q2415_20260917_202538.json`). As 12 figuras, a maior
   densidade depois da USP, foram abertas uma a uma, e o único achado de
   prioridade média foi de **imagem, não de texto**: o recorte da Q7 (id 2415)
   trazia uma tira de 12 px da figura vizinha, a histologia da Q9, na borda
   direita. Os outros quatro são de texto: a Q53 (id 2460) sem a ressalva dos
   critérios da OMS; a Q38 (id 2445), que dizia "nádegas e membros inferiores,
   como na figura" quando a figura mostra só os membros; a Q64 (id 2471), que
   atribuía à história a pele esbranquiçada do líquen escleroso, que está na
   figura; e a Q50 (id 2457), com "terceiro trimestre (entre 24 e 28 semanas)",
   que se contradiz. **Achado de método:** a ressalva da OMS faltando era a
   terceira ocorrência do mesmo dilema, então em vez de esperar a quarta uma
   consulta varreu o banco (questões que citam lúpus, antifosfolipíde ou
   trombofilia e cujas alternativas são métodos contraceptivos, checando se a
   explicação cita "categoria" ou "elegibilidade"): das 7, 6 já tinham a
   ressalva e a UNICAMP era a última. Padrão fechado.
   **Resultado da Revalida 2025/1 (2026-09-17): 97 de 97 lidas, 1 corrigida** —
   a menor taxa de defeito de todas as edições até agora, coerente com o padrão,
   porque a edição tem só 2 figuras. O achado vale pela natureza: na Q77 (id 898,
   ATLS) a explicação escrevia "a primeira prioridade é a via aérea (A)", com (A)
   significando o A do ABCDE, e duas frases depois usava "(A)" para a alternativa
   A, que é a errada (tomografias) — quem lê rápido conclui que o gabarito é A,
   e é C. Mesma família da USP Q22. As duas figuras foram conferidas, com a tira
   de ritmo do ECG da Q1 ampliada para checar a afirmação de que há ondas P sem
   QRS (confere). **Varredura feita de passagem:** 5 das 79 questões com imagem
   do banco não citam a figura no enunciado (ids 49, 897, 1812, 2320, 2396). Não
   é frase perdida na extração: é como os cadernos publicam, e a figura aparece no
   app de todo jeito. Conferido, sem ação.
   **Resultado da Revalida 2024/2 (2026-09-17): 94 de 94 lidas, 9 corrigidas** —
   a pior taxa de todas as edições, e por um motivo que a hipótese das figuras não
   explica: o caderno tem **uma única figura**. O que distingue esta edição é o
   estilo das explicações, mais antigo e terso, que afirma fórmula, dose, corte
   numérico e artigo de lei com confiança — e é exatamente aí que os erros
   estavam. As duas graves: a **Q17 (id 115)** mandava calcular a reposição da
   queimadura por Parkland (4 mL x kg x %SCQ), que dá 1.000 e 500 mL/h, os números
   da alternativa B, **errada** — o gabarito só fecha com os 2 mL do ATLS 10ª
   edição (500 e 250 mL/h), e a questão diz "preconizado pelo ATLS"; e a **Q5
   (id 103)** afirmava que comissão de PCCS e plano de saúde não são exigências da
   Lei 8.142, quando os dois estão no artigo 4º, que lista seis requisitos (o que
   derruba aquelas alternativas é o outro item de cada par, prontuário eletrônico
   e central de marcação). As outras sete: a Q84 (id 177) dizia "sem fator de
   risco adicional" numa paciente com mãe com câncer de mama aos 42; a Q2 (id 101)
   afirmava que exercício agrava a hipertensão venosa, quando a panturrilha é a
   bomba que a reduz; a Q28 (id 125) e a Q57 (id 151) ignoravam o dado do enunciado
   que puxa contra o gabarito (dor em flancos e epistaxe na reação transfusional;
   tabagismo ativo na retocolite); a Q34 (id 130) dava o intervalo do ASC-US sem a
   estratificação por idade que a questão testa; a Q25 (id 122) definia causa
   básica de óbito ao contrário; e a Q1 (id 100) chamava de "a paciente" um homem
   de 46 anos. Texto anterior em `backups/explicacoes_20260917_204647.json`.
   **Varredura que nasceu disso** (`scripts/auditar_numeros.py`, novo): lista numa
   tela todas as afirmações de fórmula, dose por kg e referência legal do banco.
   No banco inteiro deu 2 frases de fórmula, 18 de dose por kg e 19 de referência
   legal, e **só aquelas duas estavam erradas** — ou seja, a falha não era
   sistêmica. O achado mais útil da varredura é que a outra questão de queimadura
   do banco (Revalida 2026/1 Q60, id 1871) **já usava os 2 mL certos**: o banco se
   contradizia, que é o mesmo padrão da ressalva da OMS e da mamografia.
   **Resultado da Revalida 2024/1 (2026-09-17): 95 de 95 lidas, 5 corrigidas**
   (texto anterior em `backups/explicacoes_20260917_210145.json`). O achado de
   prioridade média é outra contradição interna do banco: a **Q15 (id 207)**
   afirmava que a larva migrans cutânea "não se trata com tiabendazol tópico" —
   trata, e é o que a Revalida 2024/2 Q48 (id 142) e a UNICAMP 2023 Q33 (id 2440)
   já diziam; a alternativa errava pelo diagnóstico, não pelo tratamento. As
   outras quatro são lacunas: a Q46 (id 236) não nomeava o abscesso pulmonar que
   a radiografia mostra e chamava 20 dias de antibiótico de "tratamento clínico
   prolongado" (são 4 a 6 semanas, com imagem que melhora atrasada), o que torna
   "manter e acompanhar" defensável na prática; a Q66 (id 255) não nomeava o
   flutter atrial que o enunciado entrega em "linha de base serrilhada" e "onda
   F"; a Q69 (id 258) afirmava desaceleração "espelhada" sem encarar que as
   quedas do traçado são mais profundas e abruptas que a precoce clássica, quando
   o discriminador seguro é a linha de base somada à variabilidade; e a Q89
   (id 277) dava o intervalo do LSIL sem o corte por idade.
   **Resultado da Revalida 2023/2 (2026-09-17): 90 de 90 lidas, 2 corrigidas**
   (texto anterior em `backups/explicacoes_20260917_210751.json`) — 8 figuras,
   todas abertas uma a uma, nenhuma descrita errada. A Q75 (id 987) tinha frase
   truncada ("A mistura percentil com escore Z…" sem a palavra que identificava a
   alternativa), mesma família do defeito da ENAMED id 17; e a Q26 (id 946)
   afirmava ver na foto a úlcera "em moldura" que a resolução do caderno não
   permite cravar.
   **Resultado da Revalida 2023/1 (2026-09-17): 93 de 93 lidas, 5 corrigidas**
   (texto anterior em `backups/explicacoes_20260917_211407.json`). Duas são de
   corte numérico, o padrão desta safra: a **Q44 (id 327)** chamava de sepse
   neonatal "de início tardio" um quadro com 36 horas de vida, que é precoce — e a
   distinção muda a etiologia presumida; e a **Q97 (id 378)** dava pancreatite
   aguda por amilase e lipase cerca de 2 vezes o limite, abaixo do corte de 3
   vezes que define o diagnóstico, e descartava isquemia mesentérica sem encarar o
   lactato, o pH e o perfil vascular do paciente. Mais três: a Q8 (id 295), que
   não registrava que 25,6 mg/dL de bilirrubina nessa idade já alcança o limiar de
   exsanguineotransfusão — exatamente o que a questão irmã da 2023/2 Q83 (id 995)
   ensina; a Q92 (id 373), que tratava qualquer pólipo achado como suficiente para
   subir a categoria de risco, quando o hiperplásico não é lesão precursora; e a
   Q77 (id 358), que não descrevia a radiografia sobre a qual a questão é
   construída.
   **Resultado da Revalida 2022/2 (2026-09-18): 86 de 86 lidas, 5 corrigidas**
   (texto anterior em `backups/explicacoes_20260918_002625.json`). A mais grave é
   a **Q45 (id 422)**, de um tipo que ainda não havia aparecido: a questão diz
   "conforme os dados dos gráficos apresentados" e a explicação nunca lia os
   gráficos — argumentava pela disparidade racial documentada nos boletins do
   Ministério da Saúde, o que é verdade mas não é a resposta. Nas figuras, a fatia
   das pessoas brancas cai de 65,1% das internações para 56,6% dos óbitos
   enquanto a das pardas sobe de 26,9% para 34,6%, e é só dessa comparação que
   sai a "melhor sobrevida" do gabarito; quem olhasse apenas a figura 2, onde a
   maior fatia dos óbitos é branca, concluiria o oposto. As outras quatro: a Q27
   (id 405) não descrevia a radiografia (ortostase, níveis hidroaéreos em alças
   distendidas do andar superior, pelve sem gás); a Q17 (id 396) ignorava o "sem
   ponto de flutuação" do enunciado, que é o dado posto para empurrar ao
   antibiótico isolado (flutuação é sinal tardio e falta nos abscessos
   profundos); a Q97 (id 464) inventava um dado, descrevendo o fluxo no equipo
   como "ascendente **e pulsátil**" quando o enunciado não fala de
   pulsatilidade; e a Q90 (id 457) refutava a alternativa só pela idade, sem
   dizer o que ela erra de verdade — os requisitos do método definitivo são
   alternativos (Lei 9.263/1996 na redação da Lei 14.443/2022: 21 anos **ou** dois
   filhos vivos), e não cumulativos.
   **Resultado da Revalida 2021 (2026-09-18): 88 de 88 lidas, 1 corrigida**
   (texto anterior em `backups/explicacoes_20260918_003233.json`) — a edição mais
   limpa do banco, e a última a ter sido importada. A única correção é lacuna de
   figura: a Q100 (id 3283) dizia "onda Q e supradesnivelamento em evolução" sem
   dizer onde olhar (supra convexo, em abóbada, em V2, V3 e V4, com padrão QS em
   V1 e V2 — necrose estabelecida, que é o que tira a paciente da janela da
   fibrinólise). A Q41 e a Q99 foram conferidas e batem, e a Q82 (Parkland) já
   usava os 2 mL certos.
   **Revisão encerrada em 2026-09-18: 1 074 de 1 074 lidas, 51 reescritas
   (4,7%), nenhuma marcação pendente.** Por edição: USP 2026 10/113, ENAMED 2025
   4/90, Revalida 2026/1 0/99, Revalida 2025/2 4/93, UNICAMP 2023 5/79, Revalida
   2025/1 1/97, 2024/2 9/94, 2024/1 5/95, 2023/2 2/90, 2023/1 5/93, 2022/2 5/86 e
   2021 1/88. Depois da USP Q22 e da 2025/1 Q77, nenhuma das 49 restantes
   defendia a letra errada: o que a leitura humana acha é raciocínio incompleto,
   número errado e figura não lida. **Se for para varrer o banco de novo, varrer
   por padrão** (como se fez com a ressalva da OMS e com `auditar_numeros.py`), e
   não questão por questão outra vez.
   Ferramenta: a tela **Revisar explicações** no Acervo do Streamlit (`app.py`),
   que abre na USP 2026 e mostra uma questão por vez na ordem do caderno —
   enunciado, imagem, alternativas com a correta em verde, o gabarito por
   extenso e a explicação —, com um campo de nota e os botões "Está certa" e
   "Precisa de ajuste", que gravam e pulam para a próxima. Cada edição recomeça
   na primeira questão ainda não revisada. Reaproveita
   `ui.render_cabecalho_questao` e `ui.render_alternativas_resultado`, as mesmas
   do Banco de questões. As marcas ficam em
   `backups/revisao_explicacoes.json` (`{questao_id: {status, nota, em}}`), não
   numa tabela: é varredura de um admin só, numa máquina só, e `backups/` é
   gitignorado — vira tabela se algum dia precisar ser compartilhada com o
   servidor. As correções entram depois em lote, por UPDATE com backup, nunca
   apagando a questão. Armadilha conferida na estreia: o `st.text_area` mostra
   "Press Ctrl+Enter to apply", mas clicar direto no botão comita a nota e
   registra a marca na mesma ação — a nota não se perde.
3. **QA no navegador das questões com figura** (feito, 2026-09-16). As 13
   figuras (USP 1, 11, 14, 33, 40, 49, 66, 69, 70 e 72; Revalida 2021 41, 99 e
   100) foram vistas dentro do Simulado de prova oficial, na conta demo, em
   largura de desktop e de celular. As de alternativa-imagem mostram os rótulos
   (A)–(D) legíveis e as quatro opções "Imagem A." a "Imagem D."; a USP 70 é a
   mais alta (1814 px renderizados numa coluna de 590, ~2,3 telas até as
   alternativas) mas está completa; a Revalida 2021 Q100, cujo primeiro recorte
   pegava a primeira alternativa junto do ECG, está limpa. Na USP 1 as legendas
   do painel de ultrassonografia ficam pequenas (render de 590 px a partir de
   1274), legíveis em tela cheia. Dois defeitos achados e corrigidos:
   - **Revalida 2021 Q41 (id 3232) tinha a legenda cortada.** O caderno lista 11
     siglas e o recorte parava em "AG – Agressões", perdendo AS, LAI, a fonte
     (DATASUS) e o título "Figura 1…" — e AS e LAI são barras do gráfico de
     15 a 29 anos, que ficavam sem explicação. Não mudava o gabarito (a
     alternativa certa usa AG e EII). Recorte refeito da página 12 do caderno
     (bbox 38,164–292,570 a 200 dpi) e gravado com o novo
     `scripts/substituir_imagem.py` (simula por padrão, backup em
     `backups/imagem_q3232_*.json`, `--aplicar` grava). As figuras da Q99 e da
     Q100 foram conferidas contra o PDF e estão completas.
   - **A barra do Simulado estourava a tela abaixo de ~545 px de viewport**, com
     o Finalizar cortado e rolagem horizontal — contra a regra do
     `DESIGN_TRIAGEM.md` §5 de que toda sessão tem uma saída na própria barra.
     Precisava de 376 px num espaço de 300, por causa do cronômetro de 24 px
     somado a "Questão N de M" e ao Finalizar. Praticar e Revisão passavam na
     mesma largura. Correção em dois pontos: o texto "Conduta" da marca some
     abaixo de `sm` e fica só o símbolo (`Marca.tsx`; no login, que usa
     `grande`, o texto continua), e o contador "Questão N de M" some abaixo de
     `sm` (`EmAndamento.tsx`), já que o número aparece grande no corpo e no
     navegador de questões. Com isso a barra cabe até ~320 px. Não se mexeu no
     tamanho do cronômetro.
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

### 2026-09-16
- **USP 2026 revisada.** Ver o passo 2 dos próximos passos, acima.
- **Relato de erro em questão, pelo aluno.** Decisão do usuário: com alunos
  reais usando a plataforma, o relato diz onde corrigir, em vez de depender de
  varredura minha questão por questão — que a revisão da USP 2026 mostrou ser
  cara e cega justamente onde o raciocínio está sutilmente torto. Tabela
  `relatos_questao` (questão, usuário, `parte`, comentário, criado, resolvido),
  lógica em `db.py` (`PARTES_RELATO`, `relatar_erro_questao`, `listar_relatos`,
  `contar_relatos_pendentes`, `resolver_relato`) e `POST /questoes/{id}/relato`.
  **A `parte` é uma lista fechada** (Enunciado, Alternativas, Gabarito,
  Explicação, Imagem, Outro), e não texto livre: é ela que diz onde mexer, que
  era o ponto do recurso. No app, `components/RelatarErro.tsx` é um link
  discreto ao lado do `TemaDoCaso` — portanto nos mesmos três lugares em que o
  gabarito já está visível (discussão do Praticar e da Revisão, comentário do
  resultado do Simulado) e **nunca durante a prova**. Depois de enviar, o botão
  vira agradecimento, para o aluno não repetir o relato achando que não foi. No
  admin, os pendentes aparecem no topo de Revisar explicações (a tela de "onde
  preciso corrigir", em vez de uma tela nova) e a contagem vai para o rodapé do
  menu. Relatos repetidos na mesma questão são permitidos de propósito: vindos
  de alunos diferentes, são sinal, não ruído. Testes em `tests/test_relatos.py`.
- **As 10 explicações marcadas da USP 2026 foram reescritas** (a lista do passo
  2 ficou zerada). A Q22 (id 2317) agora defende a letra B pelo estado volêmico
  do dialítico — peso contra peso seco indicando hipervolemia interdialítica,
  com ultrafiltração em vez de anti-hipertensivo — em vez de defender o fundo de
  olho. As outras nove corrigiram descrição de imagem, nomenclatura (cerclagem
  indicada por ultrassom x de emergência) e lacunas de refutação. Ferramenta:
  `scripts/corrigir_explicacoes.py <json>` (simula, backup, `--aplicar`); texto
  anterior em `backups/explicacoes_20260916_223235.json`. Na Q41 as setas 1, 2 e
  4 continuam sem nome: não consegui distinguir ducto de artéria na foto, e o
  texto passou a ensinar a regra de identificação (visão crítica de segurança)
  em vez de fingir precisão que não tenho.
- **`scripts/auditar_explicacoes.py`, com precisão medida e decepcionante.**
  Procura explicações que não citam nenhuma palavra distintiva da alternativa
  correta. Pega a Q22 com o texto antigo (validado contra o backup), que a
  checagem anterior deixara passar. Mas no banco de 1 074 devolve 26 suspeitas
  quase todas falso positivo por sinônimo ("soro fisiológico" x "cloreto de
  sódio 0,9%"). **Não serve como auditoria do banco**; serve como rede logo
  depois de escrever explicações novas, rodando só na edição recém-importada.
  Uma segunda regra — marcar quando todas as frases que citam a alternativa
  correta a negam — foi escrita, medida e **removida**: 6 falsos positivos e
  nenhum acerto, porque prosa clínica é cheia de negação que descreve ("não
  invasivo", "não caseoso") ou que descarta o distrator na mesma frase em que
  afirma o gabarito. Está documentado no script para não ser reinventada.
- **Imagem da questão com altura limitada e ampliação** (`ImagemQuestao.tsx`,
  usado nas quatro telas que mostram figura). A altura limitada é a da *caixa*,
  não a da imagem: um recorte em tira continua em largura cheia e legível e rola
  por dentro. A primeira tentativa limitou a imagem, e a questão 70 da USP virou
  uma miniatura de 179 px, ilegível — o oposto do objetivo. Com a caixa, a Q70
  foi de 1 814 px renderizados e alternativas a 2 427 px do topo para 548 px de
  caixa e alternativas a 1 169 px, sem perder resolução. Clique abre em tela
  cheia, com Esc, clique no fundo e botão Fechar.
- **O aluno é avisado quando o que ele relatou é corrigido**
  (`RelatoResolvidoAviso.tsx` no Painel, coluna `relatos_questao.avisado_em`,
  `GET /me/relatos-resolvidos` e `POST /me/relatos-resolvidos/vistos`). Fecha o
  ciclo: sem a volta, o aluno relata no escuro e para de relatar. O aviso é
  dispensável e não volta. `marcar_relatos_avisados` age por usuário, e não por
  id, para o aviso não reaparecer se outro relato for resolvido entre a leitura
  e o clique.
- **Revisão das explicações, 302 de 1 074 (parada aqui em 2026-09-16).** Feitas:
  USP 2026 (113, com as 10 marcadas já reescritas), ENAMED 2025 (90) e Revalida
  2026/1 (99). **Retomar por: Revalida 2025/2, UNICAMP 2023, depois as edições
  mais antigas.** Estado por questão em `backups/revisao_explicacoes.json`.
  Restam 4 marcadas, todas do ENAMED e nenhuma grave: id 86 (flumazenil
  apresentado como conduta pacífica numa paciente que tomou 30 comprimidos de
  clonazepam e já está intubada — é a letra oficial, mas do jeito que está
  ensina a dar flumazenil em usuário crônico, onde pode precipitar convulsão
  refratária), id 17 (frase truncada "e sem Müller regride normalmente"), id 29
  ("olhos de guaxinim" numa equimose que tem trauma orbital direto) e id 40
  ("útero fixo", que o enunciado não afirma).
  **Achado que redireciona o trabalho:** a hipótese de que a leva de 14/09
  estava ruim por ter sido escrita depressa é falsa — a Revalida 2026/1 é da
  mesma leva e saiu sem um defeito em 99 questões. O que concentra problema é a
  **USP**, a edição com mais alternativa-imagem e recortes difíceis, e 4 dos 10
  defeitos dela eram descrição de imagem que não batia com a figura. Priorizar
  questões com imagem.
- **Backup do banco inteiro** (`scripts/backup_banco.py`). Até 2026-09-16 não
  existia nenhum: os `backups/*.json` só guardam as linhas que cada operação
  toca. São 35 MB com 1 074 questões e 79 imagens recortadas à mão que só
  existiam no Neon. O script roda `pg_dump -Fc`, confere lendo o índice com
  `pg_restore --list` **e contando as linhas de `questoes` dentro do arquivo**
  contra o banco (arquivo com índice certo e conteúdo truncado já é um modo de
  falha conhecido), e mantém os N mais recentes. `pg_dump` fica em
  `C:/Program Files/PostgreSQL/18/bin`, fora do PATH. A restauração é
  deliberadamente manual (`pg_restore --clean --if-exists`). Limite: `backups/`
  é gitignorado, então os dumps só existem nesta máquina — falta uma cópia fora
  dela.
- **QA de celular** (2026-09-16): Painel, Praticar, Revisão e Simulado, as duas
  sessões, os dois diálogos e a caixa de imagem passam a 399 px sem overflow.
  Armadilha nova do método: um iframe estreito se declara `hidden`, o Chrome
  congela as animações em `currentTime: 0` e o estado inicial de
  `animate-entrar-frente` (`translateX(20px)`) vira um overflow fantasma de
  4 px. Injetar `animation:none !important` antes de medir. Mesma família do
  `document.hidden` do tempo do Simulado.
- **Dois bugs achados ao testar o relato:**
  - **O tema nunca apareceu no resultado do Simulado**, apesar de a fase 4 dos
    temas afirmar que sim: `db.listar_itens_simulado` fazia join de `areas` e
    `especialidades` mas não de `subtopicos`, então `item.subtopico` era
    sempre indefinido e o `<TemaDoCaso>` do resultado não renderizava nada.
    Corrigido com um `LEFT JOIN subtopicos sub` (alias `sub`, porque `s` já é o
    simulado). Só apareceu porque o botão novo fica ao lado do tema.
  - **Expander branco no tema escuro** do Streamlit — ver Armadilhas, abaixo.

### 2026-09-17
- **As 4 explicações marcadas do ENAMED 2025 foram reescritas** (a lista de
  pendentes ficou zerada). A id 86 passou a dizer que o flumazenil é a letra
  oficial e o único antídoto entre as opções, mas com a ressalva que faltava: em
  usuário habitual — 30 comprimidos do próprio clonazepam — a reversão abrupta
  pode precipitar convulsão refratária, e com a paciente já intubada o suporte
  costuma bastar. A id 29 deixou de chamar a equimose periorbitária de sinal de
  fratura de base de crânio e passou a ensinar a diferença (os "olhos de
  guaxinim" são bilaterais, tardios e sem trauma direto), indicando a tomografia
  pelo mecanismo, pela amnésia e pelo Glasgow abaixo de 15 por mais de 30
  minutos. A id 40 parou de afirmar "útero fixo", que o enunciado não diz. A
  id 17 teve a frase truncada sobre o ducto de Müller reescrita. Texto anterior
  em `backups/explicacoes_20260917_200146.json`.
- **Tipo de pergunta obrigatório no cadastro** (`db.criar_questao`,
  `db.atualizar_questao`, o formulário compartilhado do `app.py` e
  `importador_questoes.py`). Era o limite conhecido da fase 4 do acompanhamento
  do desempenho: as 986 questões classificadas tinham tipo, mas qualquer questão
  nova cadastrada pelo admin nascia sem ele e ficava invisível no filtro do
  Praticar e na seção "Por tipo de pergunta" do Painel — um furo que só
  apareceria meses depois, num número que não fecha. O formulário ganhou um
  selectbox ao lado da alternativa correta e recusa salvar sem tipo; a planilha
  ganhou a coluna `tipo` (aceita também "tipo_pergunta" e "tipo_de_pergunta"),
  que entrou em `COLUNAS_OBRIGATORIAS` e no modelo `.xlsx`, e a linha vira erro
  se o valor não estiver em `db.TIPOS_PERGUNTA`. Testes em
  `tests/test_importador.py` (inclusive um que confere que o JSON das
  alternativas não deslizou de posição com a coluna nova no INSERT).
- **`db.ids_questoes_da_edicao` passou a comparar a banca com `ILIKE`.** No banco
  a banca está como "REVALIDA", e `dump_explicacoes.py Revalida 2025/2` devolvia
  lista vazia **sem erro nenhum**, o que parece "edição já revisada". O
  `dump_explicacoes.py` também passou a abortar quando a edição não tem
  questão. Mesma família da regra do `CLAUDE.md` de que filtro de texto livre em
  `db.py` usa `ILIKE`.
- **Revalida 2025/2, UNICAMP 2023, 2025/1, 2024/2, 2024/1, 2023/2 e 2023/1
  revisadas.** Ver o passo 2 dos próximos passos, acima.

### 2026-09-22
- **Deploy feito: 60 commits de uma vez** (`bf5798d`, de 12/09, → `04ffc5b`), e
  o HTTPS saiu do papel depois de nove dias parado. O desbloqueio foi o usuário
  trazer a chave original da instância do outro computador: com ela entrei uma
  vez, anexei a chave **deste** notebook ao `authorized_keys` e o acesso passou
  a ser local (`ssh residencia-med`), sem depender mais do arquivo. A chave
  veio como arquivo, nunca colada na conversa, e foi validada derivando a
  pública dela — o conteúdo nunca precisou ser lido.
- **O front passou a ser construído aqui, não no servidor.** A instância tem
  954 MB e **nenhum swap**, com API, Streamlit e Caddy rodando: sobram ~390 MB,
  e `npm install` + build ali é convite a OOM. Agora vai empacotado e entra por
  troca atômica (`dist.novo` → `dist`, com `dist.antigo` guardado para
  rollback). Funciona porque o `frontend/.env.production` usa
  `VITE_API_URL=/api`, caminho relativo: o mesmo bundle serve http e https.
- **`auto_https disable_redirects` não faz o que o nome sugere.** Para escalonar
  a troca — manter a porta 80 servindo caso a 443 estivesse fechada na Oracle —
  apliquei uma configuração com essa opção. Ela só remove o redirect: um site
  declarado como `host { }` passa a ser servido **apenas** em 443, e a porta 80
  ficou sem servir nada por dois minutos. O escalonamento de verdade exige um
  bloco explícito `http://host { }`. Não houve prejuízo porque a 443 estava
  aberta desde sempre — o que faltava era alguém escutando nela.
- **Porta fechada por firewall e porta sem ninguém escutando se distinguem pelo
  tempo**: firewall dá timeout (o `-m` do curl estoura), ausência de serviço dá
  recusa rápida. Foi o que resolveu a dúvida sobre a 443 — e `ss -lntp` no
  servidor teria respondido na hora.
- **O `.env.production` estava 664**, com `DATABASE_URL` e `JWT_SECRET_KEY`
  legíveis por qualquer usuário da máquina. Agora 600. Ganhou também `APP_URL` e
  as três variáveis do Brevo, sem as quais o "esqueci minha senha" em produção
  só escreveria o link no log do servidor.
- **A senha do demo também estava no `DEPLOY.md`**, em texto claro, e não só no
  script — a varredura da auditoria de 20/09 tinha excluído os `.md` da busca
  por e-mails, e a de segredos procurava formatos de chave, não senha comum. A
  lição é sobre a varredura: procurar *padrões de segredo* não acha uma senha
  que parece uma palavra. O que acha é procurar pelo valor conhecido em **todo**
  arquivo rastreado, `.md` inclusive.
- **8080 fechada** no iptables e persistida: o admin virou
  `https://admin.conduta.duckdns.org`, e o motivo da restrição por IP (senha do
  Streamlit em texto claro) deixou de existir. O websocket do Streamlit negocia
  `101 Switching Protocols` através do Caddy, que é o que costuma quebrar em
  proxy novo.

### 2026-09-20
- **Auditoria de segurança do repositório inteiro**, pedida pelo usuário depois
  de notar o próprio e-mail à vista. O que ela achou, em ordem de gravidade:
  1. **Credencial funcional publicada.** O `scripts/seed_demo_user.py` trazia a
     senha da conta `demo@residenciamed.com` escrita, e o `bcrypt.checkpw`
     contra o banco confirmou: ainda funcionava. Como qualquer sessão válida
     baixa o banco inteiro pelo `/praticar/sessao` (gabarito e explicação vêm
     embutidos, por decisão de arquitetura), era acesso aberto ao conteúdo todo.
     A senha saiu do código **e tem de ser trocada** — o histórico do git é
     público para sempre, tirar o literal não desfaz a publicação.
  2. **Segredo do JWT com default fixo no código** (`dev-insecure-...`), num
     repositório público: se a env var faltasse em produção — um
     `EnvironmentFile` esquecido no systemd bastava —, a API subia aceitando
     cookie de sessão assinado por qualquer pessoa, para qualquer usuário. Agora
     sem default: com a variável ausente, o processo gera um segredo aleatório e
     avisa no log. Falha para o lado seguro.
  3. **E-mail do admin escrito em três lugares** (`api/deps.py` como valor
     padrão, `app.py` como única fonte, e o exemplo de produção). Além do spam,
     dizia a quem lesse o repositório qual conta atacar para ter poder
     administrativo — e admin é decidido por string de e-mail. Passou a sair de
     `db.emails_admin()` (secrets.toml, senão ambiente), com o lado seguro sendo
     *ninguém* é admin.
  4. **Login sem limite de tentativas**, enquanto o "esqueci minha senha" já
     tinha três por janela. Agora 10 falhas por (IP, e-mail) em 5 minutos,
     contadas também para conta inexistente — senão o próprio limite viraria
     oráculo de quem tem conta. Senha mínima subiu de 6 para 8.
  5. **Dados pessoais de terceiro no repositório público**: o
     `frontend/src/lib/brincadeira.ts` tem o nome completo dela, gostos pessoais, o nome
     de outra pessoa e o SHA-256 do e-mail dela — com o nome ao lado, adivinhar
     o e-mail e confirmar pelo hash é trivial. Continua em aberto: esconder do
     repositório não basta, porque o bundle servido também é público; o conserto
     de verdade é mover o roteiro para trás de autenticação, e isso é decisão do
     usuário (ver Pendências).
- **O que a auditoria conferiu e estava correto:** SQL todo parametrizado (as
  f-strings do `db.py` interpolam só `?, ?, ?` e nomes de coluna de tupla fixa);
  nenhum IDOR — todo endpoint de simulado passa `usuario_id` para dentro do
  `WHERE`, em vez de confiar no id da URL; gabarito e explicação removidos dos
  itens enquanto a prova corre; nenhum segredo jamais commitado (`.env` e
  `secrets.toml` nunca entraram no histórico); CORS com lista explícita de
  origens; cookie de sessão httpOnly; e nenhum endpoint devolvendo e-mail de
  outro usuário (só o `/me` devolve o do próprio).

- **O banco saiu desta máquina.** Destino escolhido pelo usuário: repositório
  privado no GitHub. O `--empurrar` do `backup_banco.py` manda a pasta espelho
  para o remoto substituindo o histórico por um commit só — com 24 MB por
  snapshot e um git que nunca esquece, guardar histórico faria o repositório
  crescer sem fim; assim o que está lá é exatamente o que está na pasta, e
  quantos snapshots são continua sendo o `--manter`. O branch temporário leva o
  horário no nome porque `--orphan` recusa branch existente: com nome fixo, um
  envio interrompido no meio travaria todos os seguintes.
- **O classificador de segurança barrou o envio, duas vezes, e estava certo.**
  Primeiro o `git remote add` apontando a pasta com o dump para fora, depois o
  push. É literalmente subir e-mail e hash de senha de todas as contas para um
  serviço de terceiro: essa autorização é do usuário, não da ferramenta. O que
  deu para fazer sem ela foi tudo o resto — pasta, `git init`, README com o
  comando de restauração, dump conferido — e prender a mecânica do orphan +
  force num teste contra um repositório `--bare` local, que não manda nada para
  fora. O usuário criou o repositório e rodou o primeiro envio; conferido no
  remoto depois: `main` local e `origin/main` no mesmo commit, dois dumps de
  23.801.710 bytes e um commit de histórico.
- **Antes de subir um byte, conferi se o repositório era privado mesmo**: um
  `GET` anônimo devolve 404 no privado e 200 no público (o `residencia-med`
  serviu de controle). Num repositório público, isso teria vazado os hashes.

### 2026-09-19
- **HTTPS virou pré-requisito da estreia dela, não só melhoria de segurança.**
  A brincadeira usa `crypto.subtle` para comparar o SHA-256 do e-mail, e
  `crypto.subtle` **só existe em contexto seguro** (https ou localhost). Hoje a
  produção serve HTTP puro por IP: se ela entrar antes do HTTPS, a sessão de
  boas-vindas não roda e não há erro nenhum — falha calada, e a estreia
  acontece uma vez só. Descoberto ao testar pelo celular na rede local
  (`http://192.168.1.218:5173`), que tem o mesmo problema. Duas consequências
  no código: um atalho `?brincadeira=1` que só existe em desenvolvimento
  (`import.meta.env.DEV`, eliminado no build) para permitir o teste em
  aparelho real, e um aviso no console quando falta `crypto.subtle`, porque
  falhar em silêncio era o pior jeito de descobrir.
- **Três defeitos que só existem em tela pequena, achados no celular.**
  1. **A barra da Revisão comia o "Sair"** — o `DESIGN_TRIAGEM.md` §5 exige a
     saída visível em toda sessão, e em 390px o conteúdo somava 416px, com o
     "Sair" por último na fila. O vão entre itens da barra de foco caiu para
     12px no celular (`gap-3 sm:gap-6`) e o "Recomeçar fila" virou só ícone
     abaixo de 640px, como o Simulado já fazia. Deu 274px.
  2. **O bloco em digitação desalinhava do histórico.** `text-indent` vale só
     para a primeira linha de um parágrafo: com o texto todo num `<p>` e `
`,
     as linhas seguintes ficavam 12px à direita e saltavam para o lugar ao
     descer para o histórico. Agora o bloco digitado tem a **mesma estrutura**
     do histórico — uma linha por `<p>` —, e é a igualdade de estrutura que
     garante o alinhamento.
  3. **Linhas longas quebravam.** Medidas com a fonte real (canvas), as piores
     davam 376px contra 310px úteis. Duas foram encurtadas, o padding do
     terminal caiu para 16px no celular (`p-4 md:p-6`) e entrou recuo pendente
     para a quebra que sobrar parecer intencional.
- **Lição de método:** o desktop esconde esta classe de defeito inteira. Os
  três só apareceram em 390px, e o segundo foi **criado** pelo conserto do
  terceiro — recuo pendente é invisível enquanto nada quebra.
- **Falha de rede virou "você não tem nada" em três telas.** Procurando o que
  faltava fora do deploy, a medição foi esta: 40 `useQuery` no front, **3**
  arquivos tratando `isError`. O efeito não era tela em branco, era pior — o
  Painel (`if (!data || data.totais.respostas === 0)`), a Revisão e a sessão do
  Praticar caíam todos no mesmo galho do estado vazio, então uma conexão que
  caiu dizia "ainda não há respostas para montar a sua triagem" a quem tem
  histórico, "nenhuma revisão vencida hoje" a quem tem 30 vencidas e "amplie o
  recorte" a quem só perdeu o sinal. Entrou o `EstadoFalha` (borda cheia,
  "Tentar de novo") nas três, e a regra no `DESIGN_TRIAGEM.md` §4: falha não é
  vazio. **A lição não é sobre React** — é que o estado de erro de um app assim
  não aparece no desenvolvimento, onde o servidor está a 1ms de distância, e
  ninguém tinha rodado a plataforma com a rede ruim que o celular dela terá.
- **O teste no navegador achou dois defeitos no próprio conserto.** O primeiro
  saiu da leitura do `RequireAuth`, que já fazia certo: `if (data) return
  <Outlet/>` **antes** de `if (isError)`. A minha condição era `isError ||
  !data`, que jogaria fora dado bom sempre que um refetch de segundo plano
  falhasse — e refetch de segundo plano é o que mais acontece, porque o React
  Query refaz a consulta a cada volta de foco. O segundo só apareceu clicando: o
  "Tentar de novo" não disparava pedido nenhum. A causa está no `retryer.js` do
  query-core — em `networkMode: "online"` (o padrão), depois de uma tentativa
  falha ele chama `canContinue() = focusManager.isFocused() && onlineManager
  .isOnline()` e, se der falso, **pausa** em vez de falhar. Aba em segundo plano
  ou celular sem sinal caem aí: `isError` nunca fica true, `refetch()` é no-op e
  a query volta sozinha quando o foco ou a conexão voltam. Ou seja, eu tinha
  posto um botão morto justo no caso mais comum no celular. Agora são três
  estados (dado > pausado > erro), o pausado diz "carrega sozinho" e não mostra
  botão. Conferido ao vivo: com a aba escondida a query pausou depois de uma
  tentativa e voltou sozinha ao tornar a aba visível; com a aba visível foram 4
  tentativas (1 + 3 padrão) até o erro, e aí o botão funcionou.
- **Nada segurava um erro de renderização.** Zero barreiras de erro no
  `frontend/src`: qualquer componente que lançasse deixava a página em branco,
  sem saída e, no celular, sem console para descobrir o motivo. `BarreiraErro`
  na raiz do `main.tsx` (classe, porque o React não dá hook para isso).
  Conferido forçando um `throw` de verdade na tela de login, não por leitura.
- **A plataforma não tinha ícone.** O `index.html` não tinha `<link rel="icon">`
  — e um `favicon.svg` em `public/` não é descoberto sozinho, o navegador só
  pede `/favicon.ico` —, nem `theme-color`, nem `apple-touch-icon`, nem
  manifesto. Os dois SVGs que existiam em `public/` eram restos de template
  (um logo roxo e um sprite com ícone do Bluesky), sem uma única referência no
  código: apagados. O ícone agora **é** a marca, as cinco barras da triagem,
  em SVG na aba e em azulejo escuro na tela de início. Com o manifesto, "adicionar
  à tela de início" instala de verdade, em modo standalone.
- **O tema não valia fora do `AppShell`.** Ele era aplicado só lá dentro, e o
  login e a redefinição de senha ficam fora: quem usa o escuro via uma tela
  branca justo nas duas telas em que a plataforma se apresenta. Passou para o
  `main.tsx`, antes do primeiro quadro — resolve também o pisca-claro do
  carregamento e o valor inicial do `theme-color`.
- **Figura de questão descia de novo a cada aparição.** A rota da imagem
  devolvia os bytes sem `ETag` nem `Cache-Control`. São ~300 KB por figura, 79
  questões com figura, e a revisão espaçada traz a mesma questão de volta muitas
  vezes — o que no 4G dela é a diferença entre a imagem aparecer na hora ou
  depois de segundos. `private, max-age=86400` + ETag do conteúdo (então trocar
  a imagem pelo `substituir_imagem.py` invalida o cache na revalidação
  seguinte, sem esperar as 24 h).
- **Sessão de prática agora sobrevive a fechar a aba** (`lib/sessaoSalva.ts`,
  12 h, com "Retomar"/"Descartar" no Configurador). Guarda o **lote inteiro** de
  questões, não os ids: `/praticar/sessao` sorteia, e pedir de novo com os
  mesmos filtros traria outras questões. As respostas já dadas nunca estiveram
  em risco (a `respostasQueue` as envia na hora); o que se perdia era o lugar.
- **O `Dialog` prende o foco.** Esc e clique fora já fechavam, mas o Tab
  passeava pela página atrás — para quem navega por teclado ou leitor de tela, o
  diálogo não existia. O detalhe que fez diferença: o `onFechar` é função nova a
  cada render do pai, então o efeito ficou preso só em `aberto`, com o `onFechar`
  numa ref — senão ele se remontava no meio da digitação e devolvia o foco ao
  primeiro campo.

### 2026-09-18
- **"Esqueci minha senha" (pedido do usuário).** O projeto não tinha envio de
  e-mail nenhum — nem `smtplib`, nem provedor, nada no `requirements.txt` —, e
  isso é o que decide o desenho: sem e-mail, "esqueci minha senha" clássico não
  existe. Foram oferecidos três caminhos (link emitido pelo admin sem e-mail;
  e-mail de verdade; só o aviso no login) e o usuário escolheu **e-mail de
  verdade**. Decisões:
  - **Brevo pela API HTTP, não SMTP.** `httpx` já era dependência (SMTP pediria
    lidar com TLS e porta na mão) e o Brevo verifica **remetente por e-mail**,
    sem exigir domínio próprio — que é a situação enquanto o DuckDNS não sai.
    `api/email.py` isola isso; trocar de provedor é mexer num arquivo.
  - **Sem oráculo de cadastro.** `POST /auth/senha/esqueci` responde sempre
    `200 {"ok": true}`: conta inexistente, envio falhado e limite atingido são
    indistinguíveis, senão o endpoint viraria uma forma de descobrir quem tem
    conta. A tela repete a mesma vagueza ("se existe uma conta com esse
    e-mail…").
  - **O banco guarda só o SHA-256 do token.** Quem lê o Postgres não redefine
    nada; o token em claro existe apenas no e-mail. Resgatar queima todos os
    tokens pendentes da conta na mesma transação, e token inválido, expirado ou
    usado devolvem a mesma mensagem.
  - **Sem chave configurada, o fluxo não finge.** `enviar_email` devolve False e
    escreve no log do servidor o e-mail que teria saído, com o link — é assim
    que se testa em desenvolvimento, e em produção o problema aparece no log em
    vez de virar e-mail que nunca chega. Foi como o fluxo foi validado ponta a
    ponta em 18/09: conta de teste criada, link lido do log, senha trocada,
    senha antiga recusada (401), nova aceita (200) e reuso do link recusado
    (400).
  - Limite de 3 pedidos por conta a cada 15 minutos, para o "esqueci minha
    senha" não virar ferramenta de encher a caixa de entrada de alguém.
  - **Ligado de verdade em 18/09.** Conta criada no Brevo, remetente
    `hendrickvk@gmail.com` já verificado por padrão (o Brevo valida sozinho o
    e-mail do cadastro) e chave v3 gerada — a criação da chave exige um código
    de 6 dígitos enviado por e-mail, que só o dono da conta pode digitar. As
    variáveis ficam no `.env` da raiz, que **passou a ser gitignorado nesta
    mudança**: o padrão antigo cobria só `/.env.production`, e chave colada num
    `.env` seria commitável. A API local sobe com `uvicorn … --env-file .env`.
    Envio real conferido pela API do Brevo (`/v3/smtp/statistics/events`), não
    por ausência de erro no log: `requests` às 18:17:29 e `delivered` às
    18:17:30.
  - **Risco conhecido de entrega:** o remetente é um `@gmail.com`, e a própria
    tela do Brevo avisa que domínio de freemail não é recomendado — enviar
    "de" um Gmail por provedor terceiro não alinha DMARC e pode cair no spam.
    Para duas pessoas, aceitável; se algum dia virar problema, a saída é um
    domínio próprio com DKIM (o DuckDNS não serve: só aceita um TXT, usado pelo
    ACME).
  - **Pendência:** preencher `BREVO_API_KEY`, `EMAIL_REMETENTE` e `APP_URL` no
    `.env.production` do servidor quando o deploy sair (ver
    `deploy/.env.production.example`); sem `APP_URL` o link do e-mail aponta
    para localhost. Testes em `tests/test_senha.py` (5), que passam com ou sem
    chave configurada.
- **"A plataforma parece estática" (observação do usuário) — diagnosticado no
  navegador e corrigido em quatro pontos.** O que a leitura do código e a volta
  pelo app mostraram: movimento não era o problema (`src/lib/movimento.ts` já
  animava entrada, contagem de números e listas escalonadas), e a sessão de
  Praticar já responde (teclado A–E/Enter/→/M, barra de progresso, cronômetro,
  feedback sem ida ao servidor). O estático estava no **Painel**, que tinha 20
  elementos clicáveis na tela inteira, e no **Configurador**. As quatro
  correções:
  - **Atalho escondido no hover era inalcançável no toque.** No Quadro de
    triagem, o "Praticar 10" de quatro dos cinco cartões estava em
    `opacity: 0; pointer-events: none` até o hover (medido no console). Em tela
    de toque não existe hover, então no celular o atalho não existia: o dedo
    caía no configurador. Agora é permanente — botão de tinta no cartão de
    destaque, link de texto nos outros. Regra nova no `DESIGN_TRIAGEM.md`:
    nenhuma ação pode depender de hover.
  - **Dados que só o leitor de tela via.** Os dois gráficos do Painel
    dependiam do `title`/`<title>` nativo: ~1s de espera, sem estilo, e
    inexistente no toque. As barras dos próximos 7 dias já carregavam o texto
    inteiro em `aria-label` ("Hoje: 56 casos, 36 acima da meta") e o olho não
    alcançava; no gráfico de acerto, só o último ponto mostrava valor. Agora
    ponto e barra têm `tabindex` e a dica aparece em hover **e** em foco (o
    foco é o que funciona no celular). No gráfico de linha, o rótulo fixo do
    último ponto sai de cena enquanto a dica está na tela.
  - **Tema da semana sem saída.** "O que mudou nesta semana" listava os temas
    com `15% → 42%` e não levava a lugar nenhum — o bloco fechava o ciclo das
    prioridades sem dar como continuá-lo. O tema virou botão e abre 10 casos
    dele, reusando o mesmo `navigate("/praticar", { state })` das prioridades
    (`TemaDaSemana` já trazia area_id, especialidade_id e subtopico_id: não
    precisou de API).
  - **Configurador que não reagia** (`GET /praticar/contagem`, novo). Eram 5
    selects, 2 segmentados e 2 interruptores sem nenhuma contagem: o recorte
    era montado no escuro e o tamanho só aparecia depois de começar a sessão,
    ou no "nenhum caso encontrado". Agora o rodapé diz "{n} casos nesse
    recorte" a cada filtro, o botão anuncia o menor entre a quantidade
    escolhida e o que existe ("Iniciar sessão de 7 casos") e desliga quando o
    recorte é vazio. O endpoint conta pela mesma `db.ids_questoes_filtro_pratica`
    que monta a sessão — um `count(*)` próprio duplicaria o WHERE e sairia da
    sincronia no primeiro filtro novo; `tests/test_api_smoke.py` fixa o
    contrato. Conferido no navegador: 1.074 no recorte vazio de filtros, 153
    em Conceitos, 7 em Conceitos + apenas erros, e 0 (botão desligado) em
    apenas erros + sem casos já respondidos, que se contradizem.
  - **Checagem que não virou conserto:** o recorte da figura da Revalida
    2022/2 Q27 parecia cortado e não estava (ver abaixo), e o vão vazio à
    direita do quadro de triagem era só a janela estreita — em 1540px as cinco
    colunas cabem e as vazias mostram "Nenhuma área nesta faixa".
- **Revisão das explicações encerrada: 1 074 de 1 074, 51 reescritas, nenhuma
  marcação pendente.** As duas últimas edições foram a Revalida 2022/2 (5
  correções em 86) e a Revalida 2021 (1 em 88). Detalhe por edição e o resumo
  final no passo 2 dos próximos passos, acima.
- **Achado novo, e o pior defeito de 2022/2: a explicação que responde a uma
  questão de gráfico sem ler o gráfico.** A Q45 (id 422) argumentava pela
  disparidade racial que os boletins do Ministério da Saúde documentam — verdade
  histórica, resposta errada de método: o enunciado diz "conforme os dados dos
  gráficos apresentados", e a alternativa correta só sai de comparar as duas
  figuras (a fatia branca cai de 65,1% das internações para 56,6% dos óbitos,
  a parda sobe de 26,9% para 34,6%). O teste barato para esse defeito: **se a
  explicação continuaria válida com a figura removida, ela não leu a figura.**
  Em questão que cita os próprios dados, isso é defeito, não estilo.
- **A safra de escrita prediz o defeito melhor que a data.** A Revalida 2021,
  a última edição importada e a de explicações mais longas — que nomeiam
  mecanismo e fecham com uma consequência prática —, deu 1 defeito em 88, e as 3
  figuras estavam certas. A 2024/2, de explicações curtas e assertivas que
  cravam fórmula, dose e artigo de lei, deu 9 em 94 com uma única figura. As
  duas pontas da mesma medida: **o estilo terso e confiante é o fator de risco,
  o estilo que explica o mecanismo é o que se defende sozinho.** Escrever
  explicação nova imitando a safra de 2021.
- **Antes de recortar figura de novo porque "o rótulo está cortado", recortar a
  página com folga e comparar.** A radiografia da 2022/2 Q27 mostra "OSTÁTICO"
  no canto, e o corte parecia ser meu; refeito o recorte da página com 10 pt de
  margem em cada lado, o "ORT" continua faltando — o corte está no raster que o
  próprio caderno publicou, e a imagem guardada é fiel. Custa um comando e evita
  substituir imagem à toa (diferente da legenda da 2021 Q41, que estava cortada
  de verdade e foi consertada em 16/09).

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
- O `<summary>` do `st.expander` traz fundo branco próprio, que no tema escuro
  fica branco sobre branco (texto `rgb(230,235,242)` sobre `rgb(250,251,252)`).
  A regra em `ui.py` pintava só o container `[data-testid="stExpander"]`: o
  `summary` precisa de `background: transparent !important`.
- `st.text_area` mostra "Press Ctrl+Enter to apply", mas clicar direto num botão
  comita o valor e registra o clique na mesma ação — a nota digitada não se
  perde (conferido na tela Revisar explicações).
