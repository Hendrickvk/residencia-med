# Histórico de decisões — Conduta

Resumo do **porquê** das decisões que continuam valendo. Primeiro o que está
pendente, depois as frentes que andaram em fases (já concluídas), as decisões
por data e as armadilhas das telas admin. Regras, comandos e arquitetura atuais
ficam no `CLAUDE.md`; o histórico superado (paletas antigas, telas de aluno em
Streamlit, transcrições) só existe no git, no antigo `contextoconversaclaude.txt`.

## Pendências

- **Crítica de interface de 25/09** (skill Impeccable, 31/40). Ordem combinada
  com o usuário, um item por vez, conferido no localhost e subido só com
  autorização:
  1. *Celular primeiro* — no ar desde 25/09 (commit `731bd06`; ver a data).
  2. *Chute antes de confirmar* — no ar desde 25/09 (commit `c014a57`; ver a
     data).
  3. *Painel começando por "Hoje"* — no ar desde 25/09 (commit `8619822`; ver
     a data). O próximo é o 4.
  4. *Triagem de entrada* — **descartada pelo usuário** em 25/09, depois de
     testar (ver a data). Não repropor como caminho sugerido para a conta nova.
  5. Menores. Feitos em 25/09 (ver a data), esperando autorização para subir:
     a ofensiva contando a Revisão e os cartões, o fim da meta fixa de 20 no
     cabeçalho e os `window.confirm` dos baralhos pelo `Dialog`. Em aberto, e
     só se o usuário pedir: o botão de tema no menu da conta (é gosto, não
     defeito); modo metrô (service worker e a fila de respostas no
     `localStorage` — o service worker pode prender alunas numa versão velha
     depois de um deploy, então precisa de plano de atualização antes);
     página de entrada no `/login` (da mesma família da triagem de entrada
     que ele descartou: perguntar antes); busca no celular.
- **Pedir ao suporte do GitHub que apague os commits antigos do
  `residencia-med`.** A reescrita de 24/09 tirou o roteiro da brincadeira do
  histórico, mas o GitHub continua servindo os commits antigos por link direto
  (conferido: um commit antigo e o arquivo bruto dele respondem 200), e os
  hashes deles aparecem nos eventos públicos de push. O pedido é em
  support.github.com, como remoção de dados sensíveis ("cached views" dos
  commits antigos); a lista dos 35 hashes antigos está em
  `backups/shas_antigos_reescrita.txt`, fora do git. Só o dono da conta pode
  pedir.
- **Regra de ingresso da porta 8080 na Security List da Oracle**, a última
  sobra do deploy de 22/09 e a única que não depende de código. Não expõe
  nada, porque nada escuta lá e o iptables do host já a fechou, mas ficou para
  trás. O caminho é Console → Networking → Virtual Cloud Networks →
  `residencia-med-vcn` → Security → Default Security List → apagar a regra de
  ingresso da 8080. O OCI CLI não está no servidor, e instalá-lo com instance
  principals só para isso seria desproporcional. A outra sobra, o login real
  no navegador pelo https, saiu da lista: as contas reais entram por ele desde
  23/09.
- **Próximas provas.** A próxima edição do ENAMED é a coleta de maior valor —
  é a prova que faz hoje a seleção de acesso direto e entra no peso do INEP que
  alimenta as prioridades e a nota projetada do Painel —, mas está
  **bloqueada até 04/12/2026**: a prova foi aplicada em 13/09 e o INEP só
  publicou o gabarito preliminar, que muda em anulação e em letra depois dos
  recursos. A Revalida 2026/2 está no mesmo estado. As abas por ano da página
  do INEP (`…/revalida/provas-e-gabaritos/{ano}`) trazem os links dos PDFs no
  próprio HTML; foi assim que 2025/2, 2026/1 e a 2021 foram achadas depois de o
  padrão de nome falhar. Seguir o roteiro do `CLAUDE.md` e gravar com
  `scripts/importar_prova.py`. A USP precisa ser coletada todo ano, porque a
  FUVEST só mantém a edição corrente no ar. A Revalida 2020 e a 2022/1 também
  não entraram: a sugestão de 15/09 era importá-las junto com a 2021, porque o
  domínio por tema se apoia numa mediana de 4 questões por tema (ver
  Acompanhamento do desempenho), e só a 2021 saiu.
- **Flashcards, o que ficou fora:** imagem no cartão e busca nos cartões
  esperam uma semana de uso (desde 23/09), que é quem vai dizer qual importa
  mais; juntar as duas filas de revisão continua adiado, por decisão do
  usuário. O backup semanal, que tinha de vir antes da imagem (ela multiplica o
  tamanho do dump), já roda.
- Se o shape ARM `VM.Standard.A1.Flex` (1 OCPU/6 GB, Always Free) aparecer em
  São Paulo e 1 GB apertar, recriar a instância nele.
- Tema escuro do Triagem só existe por tokens, sem protótipo próprio.

## Frentes concluídas

Trabalho que andou em fases por mais de um dia, reunido num lugar só.

### Temas por especialidade (2026-09-14 e 15)

Decisão do usuário (2026-09-14): um
nível abaixo da especialidade, para o aluno saber exatamente o que a questão
cobra (ex.: Psiquiatria > Transtornos de ansiedade). Usa a tabela
`subtopicos`, que já existia e não tinha nenhuma questão ligada. Fonte: Portaria
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

### Acompanhamento do desempenho (2026-09-15)

Decisão do usuário (2026-09-15):
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
4 questões por tema: importar o Revalida 2020, 2021 e 2022-1 ajuda
(a 2021 entrou no mesmo dia; as outras duas estão nas Pendências).

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

### Revisão clínica das explicações (2026-09-16 a 18)

Começou em 2026-09-16 pela USP 2026 e terminou pela Revalida 2021.
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
saíram em 15/09 (duas corrigidas, três conferidas e certas). As ~500
explicações escritas do zero em 14/09 (Revalida 2025/2 e 2026/1, USP 2026,
UNICAMP 2023) só tinham passado pela checagem automática de que cada uma
defende a letra oficial — isso não pega raciocínio clínico ruim defendendo a
letra certa, e por isso a revisão foi feita lendo cada uma.

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
  estava certo: a senha do admin trafegaria em texto claro. Superado em
  22/09: com o HTTPS, a 8080 foi fechada e o admin ganhou endereço próprio.

### 2026-09-13
- **Nome "Conduta"** no título, login, menus e API. Identificadores internos
  (usuário systemd `residenciamed`, serviços, cookie, e-mail da demo, paths)
  ficaram iguais porque mudar quebraria deploy e sessões abertas.
- **HTTPS via DuckDNS:** domínio pago descartado por custo.
  `conduta.duckdns.org` e `admin.conduta.duckdns.org` já apontavam para o
  servidor e a config foi commitada (`59cd72a`, `f8bb4d1`). Só foi aplicada
  em 22/09, junto com o domínio próprio, e o DuckDNS virou redirect (ver
  2026-09-22).
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
- **Tempo do simulado oficial por banca: conferido, nada a mudar.**
  Todas as bancas do banco usam o mesmo ritmo de 3 minutos por questão:
  Revalida, 100 questões em 5 h; UNICAMP 2023, 80 em 4 h; e a USP, que era a
  dúvida, 120 questões em 6 h, segundo as instruções do próprio caderno AD1 de
  2026 — a conta antiga desconfiava de diferença porque partia das 113 questões
  que entraram no banco, e não das 120 do caderno. Do ENAMED o Inep não publica
  a duração (não está na página do exame, nas perguntas frequentes, na
  legislação nem na nota de gabarito), e como metade das questões de 2025 é a
  mesma da Revalida 2025/2, fica valendo o ritmo do INEP. Guardar ritmo por
  banca só se aparecer prova com ritmo diferente.
- **Questões comuns a mais de uma prova.** São 43, todas
  entre o ENAMED 2025 e o Revalida 2025/2, e o selo mostrava só um caderno
  porque saía de `questoes.banca`/`ano`. Agora `db.provas_das_questoes` devolve
  os cadernos de um lote de questões numa consulta só,
  `serialize.questoes_publicas` anexa a lista a toda questão que sai da API
  (Praticar, Revisão e Simulado passam por lá) e o selo mostra todas —
  "Revalida 2025/2 · ENAMED 2025" —, caindo para banca + ano quando a questão
  não veio de caderno oficial.
- **Importador reutilizável em `scripts/`.** Os scripts das
  importações de 2026-09-14 ficaram no scratchpad da sessão e se perderam;
  agora existe `scripts/importar_prova.py`, que recebe o JSON montado
  (enunciado, alternativas, gabarito, área, especialidade, tema, tipo,
  explicação, imagem, banca, edição e número), valida os nomes contra a
  taxonomia, recusa duplicata pelo início do enunciado e número repetido na
  edição, simula por padrão e, com `--aplicar`, grava questões e vínculos de
  `questoes_provas` numa transação, com backup dos ids em `backups/`. Armadilha
  achada na estreia: `db.obter_tema` devolve a linha do tema, não o id, e a
  simulação não pega esse tipo de erro porque não chega a montar o INSERT.

### 2026-09-16
- **USP 2026 revisada.** Ver Frentes concluídas, Revisão clínica das explicações.
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
- **Revisão das explicações, 302 de 1 074 lidas neste dia:** USP 2026 (113,
  com as 10 marcadas já reescritas), ENAMED 2025 (90) e Revalida 2026/1 (99).
  As 4 marcadas do ENAMED, nenhuma grave, foram reescritas em 17/09.
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
- **QA no navegador das questões com figura.** As 13
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
  revisadas.** Ver Frentes concluídas, Revisão clínica das explicações.

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
    ACME). Resolvido em 22/09, com o domínio próprio autenticado no Brevo.
  - No servidor, `BREVO_API_KEY`, `EMAIL_REMETENTE` e `APP_URL` entraram no
    `.env.production` com o deploy de 22/09 (modelo em
    `deploy/.env.production.example`); sem `APP_URL` o link do e-mail apontaria
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
  final em Frentes concluídas, Revisão clínica das explicações.
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
- **Brincadeira de boas-vindas reescrita** (`frontend/src/lib/brincadeira.ts`,
  para uma conta específica, mostrada uma vez por navegador, e-mail guardado só
  como hash): um alerta de ameaça como ato de abertura, com as linhas da
  varredura aparecendo uma a uma, e oito diálogos de frase curta em que os
  botões são a fala da convidada. Concluída e funcionando, segundo o usuário
  em 2026-09-24.

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
  falhar em silêncio era o pior jeito de descobrir. O HTTPS entrou em 22/09.
- **Três defeitos que só existem em tela pequena, achados no celular.**
  1. **A barra da Revisão comia o "Sair"** — o `DESIGN_TRIAGEM.md` §5 exige a
     saída visível em toda sessão, e em 390px o conteúdo somava 416px, com o
     "Sair" por último na fila. O vão entre itens da barra de foco caiu para
     12px no celular (`gap-3 sm:gap-6`) e o "Recomeçar fila" virou só ícone
     abaixo de 640px, como o Simulado já fazia. Deu 274px.
  2. **O bloco em digitação desalinhava do histórico.** `text-indent` vale só
     para a primeira linha de um parágrafo: com o texto todo num `<p>` e `\n`,
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
     `frontend/src/lib/brincadeira.ts` trazia o nome completo da convidada,
     gostos, o nome de outra pessoa e o SHA-256 do e-mail — com o nome ao
     lado, adivinhar o e-mail e confirmar pelo hash é trivial. Esconder do
     repositório não bastaria, porque o bundle servido também é público; o
     conserto de verdade era mover o roteiro para trás de autenticação.
     **Feito em 2026-09-24**, e o histórico do git foi reescrito no mesmo dia
     (ver lá).
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

### 2026-09-22
- **Deploy feito: 60 commits de uma vez** (`bf5798d`, de 12/09, → `c36550a`), e
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
  `https://admin.conduta.duckdns.org` (no mesmo dia,
  `admin.qualaconduta.com.br`), e o motivo da restrição por IP (senha do
  Streamlit em texto claro) deixou de existir. O websocket do Streamlit negocia
  `101 Switching Protocols` através do Caddy, que é o que costuma quebrar em
  proxy novo.

- **Domínio próprio: `qualaconduta.com.br`.** "Qual a conduta?" é a pergunta
  que o enunciado faz — o domínio não precisa ser explicado para quem estuda
  para a prova, e o nome do app continua dentro dele. `conduta.com` é premium e
  `conduta.com.br` já estava registrado (consultado por RDAP, junto com
  `.med.br` e `condutamed.*`, todos tomados). O critério de escolha não foi
  estética e sim **entrega de e-mail**: gTLD novo e barato (`.study`, `.site`)
  é o que filtro de spam olha torto, e pagar para continuar com problema de
  entrega seria o pior dos mundos. `.com.br` custa R$ 40/ano fixos.
- **Comprado na Hostinger, não no Registro.br** — descoberto pelo RDAP, que
  mostrou os nameservers `*.dns-parking.com` e o domínio resolvendo para a
  página de estacionamento deles. O DNS é gerenciado no painel da Hostinger.
- **O DuckDNS não foi descartado, virou redirect.** `conduta.duckdns.org` e
  `admin.conduta.duckdns.org` continuam respondendo com 302 para os endereços
  novos, e o Caddy mantém os certificados dos dois. Custa nada e nenhum link já
  compartilhado morre.
- **Autenticação do domínio no Brevo, pelo método manual.** A opção
  "Automatic" conecta o Brevo à conta do provedor de DNS para criar os
  registros sozinho — autorização de terceiro na conta do usuário, que não é
  decisão de ferramenta. Manual: quatro registros (posse, DKIM 1, DKIM 2,
  DMARC) postos à mão no painel. **A prova de que funcionou** está na própria
  API do Brevo: o envio de 22/09 saiu de `acesso@qualaconduta.com.br`, os de
  19/09 saíram de `hendrickvk@12189774.brevosend.com`. Sem domínio autenticado
  o Brevo reescreve o `From:` de um freemail, senão o DMARC de quem recebe
  reprova a mensagem.
- **Trocar de domínio custa quatro lugares, e só um exige rebuild** (está no
  `DEPLOY.md` §2): Caddyfile, `.env.production`, `frontend/.env.production` e
  Brevo. O bundle embute **apenas** o `VITE_STREAMLIT_URL`, porque
  `VITE_API_URL=/api` é relativo — foi o que permitiu, no mesmo dia, o mesmo
  bundle servir http e https e depois dois domínios diferentes.
- **Armadilha do painel da Hostinger**, para a próxima vez: escolher o tipo TXT
  **renomeia o campo de valor** (`pointsTo` → `txtValue`), e o formulário
  re-renderiza sozinho com frequência suficiente para matar qualquer referência
  de DOM guardada. Automatizar por seletor deu `null` três vezes seguidas; o
  caminho visual (clicar e digitar, conferindo por screenshot antes de salvar)
  funcionou de primeira. Vale a regra: **em painel de terceiro, olhar a tela
  antes de salvar** — o formulário desloca entre o clique e a digitação, e foi
  exatamente assim que o campo Valor ficou com o IP antigo numa das tentativas.
- **Senha publicada do demo rotacionada.** A nova vive no `.env` local, de onde
  o `seed_demo_user.py` a lê; conferido no site público: a antiga devolve 401.

### 2026-09-23
- **Endurecimento de segurança, em fases (plano de 2026-09-22).** A auditoria
  de 20/09 e o deploy de 22/09 fecharam o que era urgente; o que sobrava está
  abaixo, em ordem de proporção entre risco e custo. Medido em produção, não
  suposto. **Os quatro itens foram escritos em 2026-09-23 e a suíte passa (122
  testes).** Os itens 1 e 3 estão **no ar** desde 2026-09-23 (conferidos com
  `curl`: os cinco cabeçalhos no app, `401 + WWW-Authenticate: Basic` no
  admin). Os itens 2 e 4 subiram no mesmo dia (commit `848ede3`, `git pull` +
  `systemctl restart residencia-api` + troca atômica do `dist`): conferido que
  `usuarios.token_version` e a tabela `cota_pratica` existem no Neon e que o
  bundle servido é o construído aqui. **Esse deploy derrubou todas as sessões
  abertas, uma vez** — é o preço único do `token_version` e estava previsto.

  **O que já está feito e não precisa ser refeito:** limite de
  tentativas no login (10 por IP+e-mail em 5 min, contando conta inexistente —
  `api/routers/auth.py`, `tests/test_login_limite.py`), senha mínima de 8,
  segredos e e-mail de admin fora do código, HTTPS com cookie
  `HttpOnly; Secure; SameSite=lax`, `.env.production` em 600, senha publicada do
  demo rotacionada. **O que foi conferido e está correto:** SQL todo
  parametrizado, nenhum IDOR (todo endpoint de simulado empurra `usuario_id`
  para dentro do WHERE), gabarito escondido durante a prova, CSRF coberto pelo
  `SameSite=lax` + corpo JSON, `comentario` de relato limitado a 1000
  caracteres, e `npm audit --omit=dev` com **0 vulnerabilidades**.

  1. **Cabeçalhos de segurança no `deploy/Caddyfile`.** Um snippet `(seguranca)`
     importado pelos dois sites com `Strict-Transport-Security` (sem
     `preload`: entrar na lista dos navegadores é fácil, sair leva meses),
     `X-Content-Type-Options`, `Referrer-Policy` e `Permissions-Policy`. O CSP
     é por site: o app tem a política inteira (`fonts.googleapis.com` no
     `style-src` e `fonts.gstatic.com` no `font-src`, senão a tipografia
     quebra; `unsafe-inline` só em `style-src`, porque o React escreve
     atributos `style=`; `data:` em `img-src`, porque o Vite embute imagem
     pequena no build), e o admin leva **só** `frame-ancestors 'none'` —
     clickjacking é o risco real lá, e o Streamlit injeta script e estilo
     inline à vontade, então um CSP completo quebraria a tela sem ganho.
     **No ar desde 2026-09-23**, conferido com
     `curl -I https://qualaconduta.com.br/`: os cinco cabeçalhos aparecem e o
     CSS do Google Fonts continua carregando (é a tipografia que quebra se o
     CSP estiver errado). O backup é `/etc/caddy/Caddyfile.antes-headers`.
  2. **Teto diário por usuário no `/praticar/sessao`** — **feito em
     2026-09-23.** Era o item que não é de checklist, é do produto: o endpoint
     devolve gabarito e explicação embutidos por decisão de arquitetura
     (MIGRACAO.md §0/§2, é o que dá o feedback instantâneo) e aceitava
     `quantidade=200`, ou seja **1074 ÷ 200 = 6 requisições** para levar o
     banco inteiro com qualquer conta válida. Entrou `db.TETO_DIARIO_PRATICA`
     = 500 casos/dia, tabela `cota_pratica (usuario_id, dia, entregues)` e
     `db.consumir_cota_pratica`. Três decisões que não são estilo: conta **no
     banco**, porque em memória o contador zeraria no `systemctl restart` que
     é justamente o que alguém faria para continuar baixando; cobra **por caso
     entregue e depois do corte**, para que um recorte de 12 casos gaste 12 e
     não os 20 pedidos; e lê o saldo com `FOR UPDATE`, senão duas abas da mesma
     conta gastariam o mesmo saldo duas vezes. Estourado, o endpoint devolve
     429 e a tela mostra a frase do servidor **sem** "Tentar de novo" — até
     amanhã a resposta é a mesma, e o botão mentiria (mesma regra do
     `EstadoFalha`). De quebra, o `queryClient` parou de repetir 4xx: nenhum
     deles melhora na segunda tentativa. `tests/test_cota_pratica.py` prende o
     teto, o 429 e o gasto proporcional ao recorte.
  3. **Segundo fator no admin** — **no ar desde 2026-09-23.** O `admin.qualaconduta.com.br` estava
     aberto à internet protegido só pela senha da conta, e é de lá que se
     apaga questão (e `questoes.area_id` é `ON DELETE CASCADE`). Entrou o
     `basic_auth` do Caddy, usuário `admin`, senha escolhida pelo usuário em
     2026-09-23. **O hash não está no repositório**: mora em
     `/etc/caddy/admin-auth.conf` (`root:caddy 640` — ver a armadilha do
     reload no fim deste item), e o `deploy/Caddyfile` o puxa com
     `import admin-auth.conf` — caminho relativo ao próprio Caddyfile. O
     motivo de nem o hash entrar aqui é que o repositório é público e bcrypt de
     senha curta se quebra offline. Efeito colateral a conferir no navegador:
     o Streamlit fala por websocket, e é o navegador que reenvia a credencial
     no upgrade. Conferido: sem credencial o admin devolve `401` com
     `WWW-Authenticate: Basic`, e com ela o `/_stcore/stream` ainda negocia
     `101 Switching Protocols`. Sem o arquivo o Caddy recusa a config inteira,
     e um `reload` que falhe mantém a config antiga no ar.
     Trocar a senha depois: `caddy hash-password`, editar o arquivo, reload.

     **Armadilha do reload, custou o primeiro reload (2026-09-23).** O
     `admin-auth.conf` foi instalado `root:root 600` e o `systemctl reload caddy`
     falhou com `permission denied`: o `ExecReload` do unit roda como **usuário
     `caddy`**, não como root, e ele não lê um arquivo 600 do root. O certo é
     `root:caddy 640` — o grupo do serviço lê, o mundo não. O Caddy se comportou
     como devia: reload inválido falha e mantém a config antiga no ar, então o
     site nunca saiu do ar. Diagnóstico rápido para a próxima:
     `journalctl -u caddy` mostra a linha exata, e
     `curl -s localhost:2019/config/ | grep -c basic_auth` diz se o que está
     rodando é mesmo o que está no disco (o arquivo pode estar novo e a config
     velha).

  4. **Revogação de sessão de verdade** — **feita em 2026-09-23.** O JWT é
     stateless com 12 h: `POST /auth/logout` limpava o cookie, mas um token já
     copiado valia até expirar. Entrou `usuarios.token_version`, que vai
     assinada no JWT como `tv` e é comparada em `deps.usuario_atual` — sem
     consulta nova, o usuário já era lido ali. Incrementam a versão o
     **logout** e a **redefinição de senha** (esta na mesma transação que
     troca a senha, via `db.invalidar_sessoes(usuario_id, conn)`: quem redefine
     costuma estar desconfiando de alguém, e trocar a senha sem derrubar a
     sessão desse alguém seria metade do conserto). Token **sem** o `tv` é
     recusado de propósito, e não tratado como versão 0 — por isso **o deploy
     desta mudança desloga todas as sessões abertas, uma vez**, o que o usuário
     aceitou em 2026-09-23. `tests/test_sessao_revogada.py` prende os três
     casos. No mesmo dia caiu também o que sobrava disto: o
     `/me` era a **única** porta de autenticação da interface, então um 401 no
     meio de uma sessão de estudo aparecia como "pode ser a conexão", com um
     "Tentar de novo" que falharia para sempre. Agora qualquer 401 fora de
     `/auth/*` invalida o `["me"]` dentro do `lib/api.ts`, e o `RequireAuth`
     manda para o login (a sessão de prática fica no `localStorage` e as
     respostas na fila, então ela volta de onde parou). `/auth/*` fica de fora
     porque senha errada também é 401, e ali não há sessão a derrubar.

  **Decisão do usuário, tomada em 2026-09-23: o cadastro continua aberto.**
  Não restringir quem cria conta, e ao mesmo tempo não deixar barato para quem
  quer abusar. Lista de e-mails autorizados foi recusada por isso. Entrou o
  limite por IP no `POST /auth/signup` — 5 contas por IP por hora
  (`MAX_SIGNUPS_IP`/`JANELA_SIGNUP_S`), reaproveitando o mesmo contador do
  login. Sem ele o item 2 não valia nada: o teto é por conta, e conta era
  grátis e ilimitada, então 3 cadastros levavam o banco inteiro. Conta a
  tentativa **antes** de saber se deu certo, senão o 409 de e-mail repetido
  sairia de graça. `tests/test_login_limite.py` prende os dois casos.

  **Medido, não suposto (2026-09-23): o limitador não é falsificável por
  `X-Forwarded-For`.** Importa porque o limite é por IP e a API só vê o Caddy.
  O `uvicorn` roda sem flag de proxy e, no padrão dele, confia no cabeçalho
  vindo de 127.0.0.1 e lê o **último** item da cadeia; o Caddy **anexa** o IP
  real no fim. Conferido contra a produção: 10 logins errados com um
  `X-Forwarded-For` forjado dão 429, e o 11º com outro forjado continua 429 —
  a chave não mudou. Se algum dia o uvicorn subir com `--forwarded-allow-ips`
  diferente, ou o Caddy passar a sobrescrever em vez de anexar, refazer esta
  medição: é ela que sustenta os dois limitadores.

  **O que o limite por IP não resolve: quem tem muitos IPs.** Ele encarece o
  script ingênuo e não impede um pool de proxies — cada conta nova custa só um
  IP. O que fecha de verdade é confirmar o e-mail antes de liberar o conteúdo,
  e foi o que entrou em seguida.

  **Confirmação de e-mail — feita e no ar em 2026-09-23** (commit `ab08571`),
  a pedido do usuário, logo depois de o limite por IP entrar. Conferido em
  produção: a tabela existe, as 6 contas reais seguem confirmadas, a rota
  `/confirmar/:token` é servida pelo SPA, e o Brevo aceitou o `htmlContent`
  num disparo real para o e-mail do usuário antes do deploy. É o que fecha o buraco descrito acima sem
  fechar o cadastro: qualquer pessoa continua criando conta, e cada conta passa
  a custar uma caixa de e-mail que funcione. Como foi:

  - `usuarios.email_confirmado_em` (NULL = pendente) e a tabela
    `confirmacao_tokens`. **Tabela separada da `senha_tokens`, não uma coluna
    `tipo` nela**: com uma coluna só, esquecer o filtro em UMA consulta faria
    um token de confirmação valer como token de redefinição de senha. Duas
    tabelas tornam a confusão impossível em vez de improvável, ao preço de três
    funções parecidas. Mesmas regras do fluxo de senha, que já foi revisado:
    guarda só o SHA-256, uso único, confirmar queima todos os pendentes da
    conta, e token inexistente, vencido ou já usado devolvem a mesma mensagem.
    Validade de 48 h, e não os 60 min da senha: o link de senha responde a um
    pedido que a pessoa acabou de fazer; este chega junto com o cadastro e pode
    esperar ela voltar do plantão.
  - **As contas que já existiam entraram confirmadas**, por um UPDATE único
    dentro do `init_db` — trancar quem já estudava aqui para provar um ponto
    seria absurdo. Conferido à mão: as 6 contas reais estão confirmadas.
  - **O que a confirmação tranca é o conteúdo, não a porta.** Quem se cadastra
    entra, vê o Painel e a faixa com o botão de reenviar; o 403 está só no
    `/praticar/sessao` e na criação de simulado (`api/deps.usuario_confirmado`).
    Trancar no login faria quem não recebeu o e-mail não ter nem onde pedir
    outro. A Revisão não precisa de trava: ela só devolve questão que a conta
    já respondeu. É **403 e não 401** de propósito: 401 mandaria a tela para o
    login, e ela está logada — o que falta é outra coisa.
  - Confirmar **não** cria sessão. O link viraria um link mágico, e esse poder
    o e-mail não precisa ter (quem tem a caixa já pode redefinir a senha).
  - Reenvio exige sessão, então não é oráculo de quem tem conta — ao contrário
    do `/senha/esqueci`. Limite de 3 por 15 min, o mesmo `LIMITE_PEDIDOS`.
  - **Armadilha encontrada:** `criado_em > NOW() - (%s * INTERVAL '1 minute')`
    com o número parametrizado **devolve zero sempre** — o psycopg2 não dá ao
    parâmetro o tipo que o operador de intervalo espera, e a contagem passa a
    não limitar nada. O `contar_tokens_recentes` da senha já calculava o corte
    em Python; agora os dois fazem igual. Um limite que silenciosamente não
    limita é pior que não ter limite, porque ninguém vai conferir de novo.
  - **Segunda armadilha, esta de teste:** um teste que cria conta pelo
    `/auth/signup` e guarda o id só depois da resposta deixa a conta para trás
    quando o endpoint quebra **depois** de inserir a linha — foi o que
    aconteceu, e 6 contas `pytest_conf_*` ficaram no banco de produção até
    serem apagadas à mão. A fixture agora sorteia o e-mail **antes** da chamada
    e apaga por e-mail no teardown. Vale para qualquer teste novo que crie
    conta pela API.
  - `tests/test_confirmacao_email.py` (6 casos) e o `confirmar_email()` do
    `conftest.py`, que todo teste que busca conteúdo precisa chamar.

  Nota lateral, baixa gravidade e conhecida: o signup devolve 409 "Já existe
  uma conta com esse e-mail", o que é um oráculo de quem tem conta aqui — o
  `/senha/esqueci` foi desenhado para não vazar isso. Trocar por mensagem
  genérica piora a usabilidade do cadastro; fica registrado como aceito.

- **"O que mudou" — a caixa de novidades (2026-09-23).** Pedido do usuário: um
  jeito de mostrar à aluna o que foi acrescentado ou corrigido, "não muito
  denso em informação". Decisões que valem daqui para a frente:
  - **A lista mora no front** (`frontend/src/lib/novidades.ts`), não no banco, e
    o servidor não conhece as entradas — ele só guarda o id da última lida
    (`usuarios.novidades_vistas`). Uma tabela e uma tela de admin para escrever
    novidade seria construir um CMS para duas pessoas: a entrada é escrita no
    mesmo commit que entrega a mudança, que é justamente quando se sabe o que
    ela ganhou.
  - **No banco e não no `localStorage`**, porque ela estuda no celular e no
    computador e a caixa apareceria duas vezes. É o mesmo precedente do
    `RelatoResolvidoAviso`, que já avisa "uma vez" por coluna no banco.
  - **`id` de entrada publicada nunca muda** — é a chave do "já viu", então
    mudar reabre a caixa para todo mundo. Id desconhecido (entrada removida, ou
    conta que viu uma versão anterior do arquivo) cai como "nunca viu": o outro
    lado esconderia uma novidade para sempre.
  - **Abre sozinha uma vez, e só no Painel.** Uma caixa por cima de um caso no
    meio da sessão seria a plataforma atrapalhando o estudo, que é contra o
    MIGRACAO.md §0. Um `ref` garante uma abertura automática por carga: sem
    ele, voltar ao Painel antes de o `PATCH` chegar reabria a caixa recém
    fechada. Fecha primeiro e grava depois — a caixa não espera a rede, e se a
    gravação falhar o pior caso é ela aparecer de novo na próxima visita.
  - **Primeira vez mostra só a entrada mais recente**, não o histórico inteiro:
    a estreia não pode ser um muro de texto. Depois disso, mostra tudo o que
    entrou desde a última leitura.
  - Sem cor de triagem em nada disso (DESIGN_TRIAGEM.md §2: a escala só
    codifica nível de aproveitamento). "Novo"/"Corrigido" são rótulo em caixa
    alta, e o ponto de pendência no menu é tinta.
  - `tests/test_novidades.py` cobre a metade do servidor; a lista é do front.

- **Perfil: nome, cor e foto (2026-09-23, as duas fases).** O usuário mandou
  a plataforma para amigas e a primeira reação delas foi querer "uma fotinho ou
  mudar a cor do meu perfil". Decisões:
  - **Nome antes de foto.** A plataforma não guardava nome nenhum: o avatar era
    a primeira letra do **e-mail** e o menu mostrava o endereço inteiro. Nome
    próprio resolve metade do "quero que seja meu" com uma fração do trabalho
    de um upload. Por isso ele veio primeiro; a foto entrou logo depois, na
    fase 2.
  - **Foto (fase 2).** Vive em `fotos_perfil`, **tabela separada e não uma
    coluna de `usuarios`**: o `obter_usuario` faz `SELECT *` e roda em toda
    requisição autenticada — um BYTEA ali seria a foto descendo do Postgres a
    cada chamada de API, para nada. Em `usuarios` fica só `foto_versao`, uma
    string curta, que é o sha do conteúdo e entra na URL da imagem: foto nova é
    URL nova, então o servidor manda cachear por um ano (`immutable`) e a troca
    aparece na hora. O resto copia o `/questoes/{id}/imagem`: ETag do conteúdo,
    `private` porque depende da sessão, e 304 no `If-None-Match`.
  - **O recorte e a redução são do navegador** (`lib/foto.ts`: recorte quadrado
    pelo centro, 256px, JPEG 0.85 — uma foto de câmera vira ~5 KB). Não é
    preguiça: o servidor não tem biblioteca de imagem e não precisa ganhar uma
    só por isto. O que ele faz é o que **não** dá para delegar ao cliente, já
    que quem chama a API pode ser qualquer coisa: confere o **tamanho** dos
    bytes decodificados (teto de 200 KB) e a **assinatura** do arquivo contra o
    tipo declarado. Sem essa segunda conferência, um SVG com script dentro
    entraria como `image/png` e voltaria a ser servido da nossa origem — por
    isso SVG não está na lista de tipos aceitos, e por isso a lista existe.
  - A imagem chega em **base64 dentro do JSON**, não como multipart: evita a
    dependência `python-multipart` e casa com o `canvas.toDataURL()` que o
    navegador já produz ao redimensionar.
  - `tests/test_foto_perfil.py` prende o ciclo inteiro (sobe, 304, sai) e as
    três recusas: tipo mentido, tipo fora da lista e tamanho.
  - **A paleta do perfil não pode sair da escala de triagem**
    (DESIGN_TRIAGEM.md §2): t1–t5 significam nível de aproveitamento, e um
    avatar verde leria como "vai bem". As seis cores evitam os matizes da
    escala (vermelho, laranja, amarelo, verde, azul) e ficam em neutros, roxo,
    rosa, turquesa e marrom. **A cor não muda com o tema** — é a cor da pessoa,
    não deveria virar outra quando ela alterna claro/escuro.
  - **Só no avatar**, decisão do usuário: o Painel é onde a cor tem significado
    clínico, e competir com ele seria confundir a leitura.
  - **O banco guarda a chave (`ameixa`), não o hex**, e `db.CORES_PERFIL`
    valida: cor vinda do cliente vira CSS na tela, então valor fora da lista
    cai no padrão. As classes do Tailwind ficam escritas por extenso em
    `lib/perfil.ts` — `bg-perfil-${cor}` montado em tempo de execução não
    existiria no CSS (mesma armadilha do `CLASSES_NIVEL`).
  - Nome vazio volta a NULL e a tela mostra o e-mail de novo, em vez de um
    avatar em branco. `tests/test_perfil.py`.

- **Página de perfil (2026-09-23).** O diálogo virou tela (`/perfil`), fora do
  `NAV` — conta não é aba de estudo, e o caminho é o menu da conta, agora no
  topo dele. **Dois lugares para editar a mesma coisa é pior que um**, então o
  diálogo foi apagado em vez de conviver com a página.

  A página existe porque havia conteúdo esperando por ela, não porque faltava
  tela: `db.listar_questoes_marcadas` e `db.definir_prova_alvo` estavam no
  banco e **não eram alcançáveis de lugar nenhum**. Ou seja, a aluna marcava
  uma questão com "M" e nunca mais a reencontrava, e a contagem regressiva da
  prova aparecia na barra sem haver como definir a data.

  - **A lista de marcadas não devolve gabarito, alternativas nem explicação**
    (`db.resumo_questoes_marcadas`). Não é economia de bytes: os ids das
    questões são sequenciais, então marcar as 1074 e pedir a lista uma vez
    levaria o banco inteiro, contornando o teto diário do `/praticar/sessao`.
    Rever de verdade é pelo botão "Praticar as N", que entra pelo filtro
    `apenas_marcadas` — o conteúdo continua saindo por uma porta só.
    `tests/test_pagina_perfil.py` prende justamente isso: se alguém
    "completar" o retorno da lista com as alternativas, o teste quebra.
  - O botão usa o mesmo `location.state` com `iniciarImediato` que o "Praticar
    10" do Painel já usava.
  - `textoProva` saiu da `Topbar` para o `lib/format`: a página mostra a mesma
    contagem ao lado do campo, e duas versões dessa conta divergiriam.
  - A data usa `<input type="date">`, sem biblioteca: o calendário nativo já
    resolve formato, fuso e teclado no celular.

- **Flashcards da aluna: pasta > baralho > cartão (2026-09-23, fase 1).**
  Sugestão do usuário depois do retorno das amigas. Decisões que valem daqui
  para a frente:
  - **Um SM-2 só no projeto.** `repeticao_espacada.calcular_proximo_estado` é
    pura e não sabe o que está agendando, então o cartão usa exatamente a
    mesma conta das questões — `avaliar_cartao` só escolhe onde o estado mora.
    Um segundo algoritmo seria duas verdades sobre o mesmo aluno.
  - **Tabela `revisao_cartao` separada de `revisao`**, porque aquela tem chave
    estrangeira para `questoes` e cartão não é questão. Com `revisao_cartao_eventos`
    desde o primeiro dia, pelo mesmo motivo do `revisao_eventos`: retenção ao
    longo do tempo não se reconstrói depois, e log que não foi gravado não volta.
  - **As filas continuam separadas** (decisão do usuário): a Revisão de casos
    tem meta diária calibrada para questões e o Painel mede memória de
    questões — misturar no primeiro dia mudaria esses números sem aviso.
    Juntar depois é a união de duas consultas, não um algoritmo novo.
  - **`usuario_id` repetido em baralho e cartão** é desnormalização
    deliberada: sem ela, conferir dono exigiria um JOIN em toda consulta, e é
    essa conferência que impede pedir o baralho de outra pessoa pelo id. Com a
    coluna, o dono entra no WHERE sempre.
    `tests/test_cartoes.py::test_cartoes_de_outra_conta_nao_sao_alcancaveis`
    prende isso endpoint por endpoint.
  - **As 12 cores de pasta não saem da escala de triagem**
    (DESIGN_TRIAGEM.md §2), pela mesma razão da cor do avatar: vermelho,
    laranja, amarelo, verde e azul significam aproveitamento, e uma pasta
    verde ao lado de uma vermelha seria lida como "vou bem nesta, mal
    naquela". Sobra gama em roxos, rosas, turquesas, terrosos e neutros. A cor
    aparece como **faixa**, não como fundo do cartão — fundo colorido
    competiria com a leitura do resto da tela.
  - Aba própria no topo, e não dentro do perfil: perfil é onde se configura a
    conta, baralho é onde se estuda todo dia. O usuário tinha sugerido o
    perfil ("é algo mais seu"); a coleção é dela, mas a frequência de uso é
    que decide onde fica.
  - O estudo herda o que o Praticar já provou: lote inteiro numa requisição
    (MIGRACAO.md §0), avaliação fire-and-forget, `BarraFoco` e atalhos de
    teclado (espaço vira, 1–4 dão a nota).

  **Fase 2 (mesmo dia):**
  - **"Virar cartão" na discussão do caso**, ao lado de "Relatar erro" e pelo
    mesmo critério de lugar: só onde o gabarito já apareceu (Praticar, Revisão
    e resultado do Simulado), **nunca durante a prova**. O verso já vem com a
    alternativa correta — que é o fato — e a frente fica vazia, porque a pista
    é ela quem inventa e um enunciado de 900 caracteres seria um cartão
    impossível de responder. O último baralho usado fica no `localStorage`
    (conveniência por navegador) e o valor é **derivado no render**, não posto
    por efeito.
  - **`cartoes.questao_id`**, nullable, gravado quando o cartão nasce de um
    caso. Ainda **sem leitor na tela**, de propósito: procedência não se
    recupera depois, e ninguém vai lembrar de onde veio um cartão escrito há
    seis meses.
  - **Mover baralho de pasta** pelo botão "Ajustar" (nome e pasta no mesmo
    PATCH, que é o caso real de "reorganizei isto"). A pasta de destino
    também é conferida contra o dono — mandar o id de uma pasta alheia não
    move nada, e o teste cobre isso.

  **Visual, direção "baralho de verdade" (escolhida pelo usuário em
  2026-09-23, entre três protótipos).** A primeira versão ficou crua — lista de
  linhas, cor só numa listra fina. Montei três direções num HTML com os tokens
  reais (ficha sóbria · baralho tátil · painel denso estilo Anki) e ele
  escolheu a tátil. O que isso fixou:
  - **O baralho é um maço**: as bordas dos cartões de trás aparecem acima do
    bloco, e a pilha **só é desenhada quando há mais de um cartão** — um maço
    de um cartão só seria mentira, e a tela depende de a metáfora ser honesta.
    Na tela de estudo a pilha encolhe conforme a fila anda.
  - **Cor cheia no banner da pasta** e tom suave na faixa de cada baralho —
    três níveis: cor forte (pasta) → véu (baralho) → papel (conteúdo).
  - **Paleta viva, e ainda fora da triagem.** O usuário pediu cores mais vivas
    duas vezes; na segunda, o verde (`musgo`) e o dourado (`areia`) **saíram**:
    apagados dava para conviver, vivos iam gritar "vai bem" e "atenção" na tela
    errada. Entraram `ciano` e `lavanda`, e a paleta passou a cobrir o arco
    índigo → ciano com dois neutros e um marrom. As **chaves do banco não
    mudaram de significado sem migração**: o `init_db` move `musgo`→`ciano` e
    `areia`→`lavanda`, para a pasta de quem já escolheu não cair no padrão.
  - **`--pasta-*-on`, um texto por cor**, medido contra 4,5:1 — o mesmo
    mecanismo do `--tN-on`. Branco fixo sobre a cor cheia falharia no ciano, no
    rosa, na lavanda, na orquídea e na turquesa; o magenta teve de escurecer de
    `#c026d3` para `#a21caf` para o branco passar. O título da pasta é
    17px/700, que **não** conta como "texto grande" pela WCAG, então vale 4,5 e
    não 3.
  - **Notas em pílula colorida** com `bg-tN text-tN-on`. O `-on` não é detalhe:
    no tema claro o laranja e o amarelo pedem tinta e o resto pede branco, no
    escuro todos pedem tinta (DESIGN_TRIAGEM.md §2). Branco fixo quebraria o
    contraste em metade dos casos.
  - O cartão vira em 3D (`rotateY`), com as duas faces no mesmo lugar.
  - Barra de estágios por baralho — novo · aprendendo · consolidado, a mesma
    régua de 21 dias da Revisão de casos.

  **Três defeitos que só apareceram olhando a tela, e que os testes não
  pegariam:** o Tailwind não gera classe nova sem reiniciar o dev server (as
  cores subiriam invisíveis para produção); os tons suaves precisaram ser
  refeitos duas vezes, porque sumiam no escuro e encostavam no papel no claro;
  e o plural de "cartão" saía "cartãos" — agora existe um `plural()` só, no
  `lib/cartoes.ts`, porque a interpolação ingênua erra sempre.

  **Quatro ajustes de uso, depois de eu usar a feature como aluna
  (2026-09-23).** Nenhum é enfeite; todos vieram de atrito real:
  - **Estudar tudo numa sessão só** (`GET /cartoes/estudar`, sem baralho).
    Oito baralhos vencidos custavam oito sessões — era o maior atrito diário
    que tinha sobrado. Cada cartão traz o nome e a cor do baralho, que é o que
    a barra de foco mostra quando a fila atravessa baralhos.
  - **Editar o cartão durante o estudo.** O momento em que ela vê que o cartão
    está mal escrito é o de respondê-lo; tendo de sair para achar o baralho,
    ela não corrige. O texto reescrito fica num estado local da sessão, porque
    o lote tem `staleTime: Infinity` e não vai ser refeito.
  - **Desfazer a última nota** (`POST /cartoes/{id}/desfazer`, atalho
    Ctrl/Cmd+Z). Com atalho de 1 a 4, tecla errada é questão de tempo. **É
    para isto que o `revisao_cartao_eventos` existe desde o primeiro dia**: o
    estado anterior está no `*_depois` do evento anterior, então desfazer é
    apagar o último evento e restaurar do que sobrou; sem evento nenhum antes,
    a linha de agendamento some e o cartão volta a ser novo. Guardar só o
    estado atual teria tornado isto impossível.
  - **Fila embaralhada.** A ordem do SELECT continua por vencimento, porque o
    `LIMIT` precisa pegar os mais atrasados; **a embaralhada vem depois**, no
    Python. Apresentar sempre na mesma sequência ensina a ordem, não o
    conteúdo.

  **O que continua fora** está nas Pendências.

- **Backup semanal agendado e restauração testada (2026-09-23).** Era a
  pendência mais antiga da lista, e a única que não era melhoria: é o que
  decide se um acidente é incidente ou é a perda das 79 figuras recortadas à
  mão.
  - **Tarefa do Windows "Conduta - backup semanal"**, domingo às 20h,
    chamando `scripts/backup_semanal.cmd`. Criada com `-StartWhenAvailable`:
    num notebook que passa domingo à noite desligado, sem isso a semana
    inteira é pulada em silêncio, que é exatamente como o backup deixa de
    acontecer sem ninguém perceber. Roda como o usuário, em sessão
    interativa, então não guarda senha nenhuma e enxerga o `BACKUP_ESPELHO`.
  - **A restauração foi testada de ponta a ponta, pela primeira vez.** Um
    `CREATE DATABASE restauracao_teste` no próprio Neon (banco separado,
    conexão **direta**, sem o `-pooler`, porque `CREATE DATABASE` não passa
    pelo pooler nem dentro de transação), `pg_restore --no-owner
    --no-privileges` do dump mais recente, e contagem lado a lado com a
    produção: 13 tabelas, **nenhuma divergência**, e as 79 figuras chegaram
    inteiras (19,5 MB). Levou 25 segundos. O banco de teste foi apagado.
  - **O `--empurrar` continua sendo ato do usuário.** O dump tem e-mail e
    hash de senha de todas as contas; a tarefa agendada roda na conta dele e
    faz o envio, o que é diferente de eu empurrar. O espelho local estava com
    o dump de 22/09 sem commit, e o primeiro disparo da tarefa resolveu: no
    mesmo dia, às 22h34, espelhou o dump novo e o empurrou para o remoto
    (resultado 0 no agendador; o registro fica em `backups/backup_semanal.log`).
  - Medido no mesmo dia: o dump tem **23,9 MB** e o banco estava em 1078
    questões — 4 delas eram sobra de teste, apagadas em 24/09. Imagem no
    cartão de flashcard multiplicaria isso — foi por causa disto que o backup
    veio antes dela.

### 2026-09-24
- **O roteiro da brincadeira saiu do código.** Só o e-mail da convidada estava
  em hash; o resto do `brincadeira.ts` era texto puro — nome completo, gostos,
  o nome de outra pessoa, o tom inteiro — e ia no `index-*.js`, o arquivo
  principal que qualquer visitante baixa já na tela de login. O hash protegia
  pouco: com o nome no mesmo arquivo, os e-mails prováveis se testam em
  segundos. Apagar o arquivo resolveria, mas ela perderia a reprise pelo menu
  da conta, e o usuário não quis. Decisões:
  - **O roteiro mora na tabela `brincadeiras`** (`usuario_id` → `roteiro` e
    `reprise`, JSONB) e desce no campo `brincadeira` do `/me`, preenchido só
    para a conta que tem um. **No `/me`, e não numa rota própria**: para quem
    ainda não viu a brincadeira neste navegador — todo mundo menos ela — a
    tela inteira espera a verificação antes de aparecer, e uma rota à parte
    seria uma ida a mais ao servidor antes de qualquer tela abrir, para todas
    as contas. O custo é o roteiro (3,7 KB) descer em cada `/me` dela, que é
    refeito a cada resposta enviada; para uma conta só, aceito.
  - **Quem é a convidada virou um fato do banco**, e não uma comparação no
    navegador: sem hash no código e sem `crypto.subtle`, então a dependência de
    HTTPS anotada em 19/09 deixou de existir. O atalho `?brincadeira=1` de
    desenvolvimento saiu junto; para testar, grava-se o roteiro na própria
    conta.
  - O efeito que abre a sessão depende de *existir* roteiro, um booleano, e não
    do objeto: o `/me` refeito traz um objeto novo, que reabriria a reprise
    recém-fechada.
  - **Para mudar a piada**: editar `backups/brincadeira.json` (fora do git) e
    rodar `scripts/gravar_brincadeira.py` (simula; `--aplicar` grava). O JSON
    acha a conta pelo SHA-256 do e-mail. A cópia que vale é a do banco, que o
    backup semanal leva.
  - `tests/test_brincadeira.py` prende que outra conta recebe `null`, e o
    bundle construído foi varrido atrás do texto antigo: nada.
  - **No ar no mesmo dia.** API reiniciada e bundle trocado; conferido que o
    `index-*.js` servido é o construído aqui e não tem o texto. Depois disso o
    `dist.antigo` do servidor, que guardava o bundle anterior com o texto, foi
    apagado; a próxima subida recria a cópia de rollback.
- **Histórico do git reescrito, a pedido do usuário.** Com `git filter-repo`,
  numa cópia recém-clonada e conferida antes do envio: as três versões antigas
  do `brincadeira.ts` saíram de todos os commits, a lista de detalhes das duas
  versões antigas deste arquivo virou "gostos pessoais", o nome de exemplo do
  `tests/test_perfil.py` foi trocado e uma mensagem de commit perdeu o detalhe
  pessoal. Na história nova, a varredura não acha nenhuma das marcas, nem em
  arquivo nem em mensagem. Consequências:
  - **Todo commit desde 15/09 mudou de hash** (35 de 98), porque a árvore de
    cada um mudou; os de antes ficaram iguais. Os três hashes citados aqui e no
    `DEPLOY.md` foram atualizados.
  - O envio foi com `--force-with-lease` preso ao hash antigo, para não
    atropelar nada que tivesse chegado ao GitHub no meio. O servidor e esta
    máquina foram para a história nova com `fetch` + `reset --hard` e tiveram
    os objetos antigos apagados (`reflog expire` + `gc --prune=now`).
  - **O que a reescrita não alcança.** O GitHub continua servindo os commits
    antigos por link direto até a coleta de lixo dele, e só o suporte do GitHub
    apaga isso (ver Pendências). E qualquer clone feito antes guarda a história
    velha: nele, nunca `pull` com merge, que traria tudo de volta — é `fetch` +
    `reset --hard origin/main`, ou clonar de novo.
- **Uma área de teste aparecia para os alunos**, no filtro de Áreas do
  Praticar: `__pytest_area_…`, o ".py" que o usuário viu. Era sobra de uma
  rodada da suíte interrompida — teardown só roda se o pytest chega ao fim, e
  o provável é uma rodada cortada pelo limite de tempo de quem chamou (a suíte
  leva uns 7 minutos). A sobra era pior que o nome no filtro: a área tinha 4
  questões de teste (banca `PYTEST`), que entravam no sorteio de qualquer
  sessão sem filtro de área; ninguém chegou a respondê-las. Com ela ficaram uma
  especialidade de teste e 3 contas de teste. Tudo apagado por id, depois de um
  backup completo, numa transação que só gravava se apagasse exatamente o
  conferido; o banco voltou a 1 074 questões. **O conserto de raiz** está no
  `tests/conftest.py`: a suíte começa apagando o que casa com os dois padrões
  de dado de teste (`__pytest_area_*` e `pytest_*@teste.local`) — conferido
  plantando uma sobra falsa e rodando um arquivo de teste. Por isso todo dado
  de teste novo precisa cair num desses padrões.
- **No celular, a alternativa respondida ficava uma palavra por linha.** A
  etiqueta "Conduta correta" (~140px) ia na coluna da direita, junto do
  percentual, e sobravam ~30px para o texto; as palavras compridas passavam por
  baixo dela. Abaixo de `sm` ela desce para baixo do texto (regra anotada na
  Alternativa, no `DESIGN_TRIAGEM.md`). Achado pelo usuário no celular, de
  novo a classe de defeito que o desktop esconde. Conferido com uma página de
  teste com as classes do componente e o CSS do build, fotografada pelo Edge
  sem janela: ele não desce de ~500px de largura, então é uma caixa de 393px
  dentro dele que faz o papel do celular — com a janela "de 393", a foto sai
  cortada e parece defeito que não existe.
- **Mais cores: uma paleta só para avatar e pastas, e um seletor radial.** O
  retorno das alunas foi que as cores eram poucas e não variavam. A causa era a
  regra de deixar de fora os cinco matizes da triagem: sobravam roxos, rosas,
  cianos e marrons. Perguntado, **o usuário decidiu que vermelho, laranja,
  amarelo, verde e azul entram em tudo** (avatar e pastas), e que o seletor novo
  vale para os dois. O que continua valendo é a regra dos *tokens*: `t1`–`t5`
  só significam nível (DESIGN_TRIAGEM.md §1 ganhou a exceção por escrito).
  Decisões:
  - **Um JSON para o front e o banco** (`frontend/src/lib/paleta.json`): dez
    famílias de oito tons, do claro ao escuro, com o texto que passa 4,5:1 por
    cima de cada tom. Nove famílias são os degraus 200–900 do próprio Tailwind;
    o marrom, que o Tailwind não tem, foi montado em OKLCH, com o croma caindo
    perto do branco e do preto. Nenhum tom precisou de ajuste para passar
    4,5:1 com branco ou tinta, e `tests/test_paleta.py` prende isso. No front
    as cores vão por estilo inline: 80 classes escritas por extenso seriam o
    `CLASSES_NIVEL` multiplicado por vinte.
  - **Sem migração do banco**, e de propósito: a suíte local roda o `init_db`
    contra a produção, então uma migração ali trocaria as chaves antes de o
    front novo estar no ar, e o front velho mostraria o padrão para todo mundo.
    As 26 chaves antigas viram o tom mais próximo pela tabela `legado` do JSON,
    na leitura e na escrita; a chave nova só é gravada no próximo "Salvar".
  - **A tradução não é só distância de cor.** Pela distância pura em OKLab, a
    `ameixa` apagada do avatar virava cinza, porque os roxos do Tailwind são
    mais saturados que ela. Um corte só por saturação não resolve: o chocolate
    (croma 0,039) e a ardósia (0,041) empatam, e só o matiz diz que um é marrom
    e a outra, cinza. Ficou: distância em OKLab, mas cor com croma acima de 0,08
    nunca cai no cinza. Os 26 casos foram conferidos um a um.
  - **O véu do baralho** é o tom do meio da família misturado ao papel
    (`color-mix`), 20% no claro e 30% no escuro (`--veu-pasta`). Do meio, e não
    do tom escolhido: amarelo quase branco sumiria no papel claro.
  - **O seletor** (`components/SeletorCor.tsx`) mostra as dez famílias; tocar
    numa abre um disco com os oito tons em volta dela, o mais claro no alto,
    escurecendo em sentido horário, e o disco se desloca para caber na janela
    quando a cor está na borda. Setas andam pelo anel, Esc fecha sem fechar o
    diálogo da pasta em volta, e toque fora fecha por `pointerdown`, porque o
    Safari não dá foco a botão tocado.
  - **Movimento pelas skills do Emil Kowalski e do Impeccable** (pedido do
    usuário, instaladas em `~/.claude/skills`, fora do repositório): os tons
    saem de trás da cor tocada, 180ms `suave` com 30ms entre eles, e voltam em
    120ms `brand`; transição e não keyframe, para reabrir no meio retomar de onde
    está. **Entrada por `@starting-style`, e não por dois quadros de
    `requestAnimationFrame`**: a primeira versão esperava quadros, e na aba que
    se declara escondida (a do navegador automatizado, e a de quem troca de aba)
    o disco ficava montado e invisível. Do Impeccable entraram só os textos; o
    `settings.json` dele instala ganchos que rodam um binário baixado da
    internet a cada edição de arquivo, e isso ficou de fora.
  - **Tons extremos ganharam contorno**: o amarelo mais claro sumia no papel e o
    cinza mais escuro no disco escuro, coisa que a paleta antiga não tinha. Uma
    borda de 15% de preto (ou de branco, no escuro) nos círculos e no avatar.
  - **No ar em 2026-09-25** (commit `a53d288`), depois de o usuário testar no
    próprio celular: API reiniciada e bundle trocado, conferido que o site serve
    o seletor, a paleta e o `@starting-style`. Antes disso, o toque foi testado
    num celular emulado pelo protocolo do DevTools (393px, toque, Android): o
    disco cabe nas bordas, o toque escolhe e fecha, tocar fora fecha e não sobra
    anel de foco. Para abrir o dev server no celular pela rede de casa:
    `npm run dev -- --host` e `http://<ip do computador>:5173` — no celular,
    `localhost` é o próprio celular, e a conexão é recusada.
  - **Armadilhas da foto sem janela, para a próxima:** com
    `--virtual-time-budget` o relógio é simulado e não há quadro, então o que
    depende de `requestAnimationFrame` não acontece; o `--timeout` não segurou a
    foto até o clique da página; e o `--dump-dom` chamado pelo `&` do
    PowerShell sai vazio — é pelo `Start-Process -RedirectStandardOutput`.

### 2026-09-25
- **Revisão das animações, pelas skills do Emil Kowalski** (pedido do usuário:
  melhorar o movimento e trazê-lo para troca de página, de aba e features).
  A auditoria (`improve-animations`) achou o movimento já bem cuidado — nada
  de hover que mexe no toque, nenhum `transition-all` ou `ease-in`, botões que
  cedem, abas segmentadas deslizando, números contando nos resultados — e
  quatro correções mais duas lacunas, todas feitas (`animate`). O que ficou
  de fora de propósito, por ser decisão já tomada: casos deslizarem (só o
  ritmo mudou), Painel em cascata, marca animada, cartão virando em 3D e o
  "menos movimento" zerando tudo. Detalhe dos tempos no DESIGN_TRIAGEM.md §3.
  - **Caso novo desliza 12px em 200ms** (eram 20px em 340ms). Pela régua das
    skills, ação de teclado repetida centenas de vezes não deveria animar;
    ficou porque o usuário escolheu, mas no mínimo perceptível.
  - **Entrada padrão em 240ms** (eram 360ms, acima do teto de 300ms para
    interface): vale para telas, blocos e a discussão depois de cada resposta.
  - **Troca de tela com direção**: entre abas pela ordem delas, dentro de uma
    aba pela profundidade do caminho (`direcaoDaNavegacao`, `lib/nav.ts`),
    decidida por estado derivado no AppShell. O `main` ganhou `overflow-x-clip`
    — sem ele, a tela entrando de lado dava rolagem lateral no celular.
  - **Sublinhado da aba e barra do estudo de cartões por `scaleX`**, não por
    `width`, que refazia o layout a cada quadro.
  - **Avisos com saída.** O de respostas pendentes desce por transição
    (`.presenca`, com `@starting-style`; a skill veta keyframe em toast). O de
    relato resolvido, primeiro bloco do Painel, encolhe junto com o vão
    (`-mb-7` anulando o `gap-7` e `pb-7` devolvendo por dentro), e o Painel
    sobe sem salto no fim. **A medição mudou a curva**: com `suave` o Painel
    andava 87px no primeiro quadro, o que ainda parece salto; com `brand`
    (entra e sai devagar), que é a curva para o que se move na tela, o
    movimento se espalha pelos 120ms.
  - **O visto do fim de uma sessão de cartões carimba** — momento raro, onde o
    movimento pode comemorar.
  - **Conferido num navegador controlado pelo protocolo do DevTools**, logado
    com uma conta de teste criada pela API e apagada depois: as cinco trocas
    de aba entram do lado certo, no computador e no celular, e sem rolagem
    lateral. Para medir animação ali, amostrar por `setTimeout`: o
    `requestAnimationFrame` não roda na aba sem janela.
  - A `review-animations` do Emil só roda chamada pelo usuário (`/review-animations`).
  - **No ar no mesmo dia** (commit `1f173df`), só front: conferido que o site
    serve a entrada de lado em 200ms e o aviso por transição. O teste pelo
    celular na rede de casa parecia lento, e não era o código: a API local
    fala com o Neon pela internet de casa a ~260ms por consulta, e o Painel
    faz várias em sequência; em produção a API fica ao lado do banco.

- **Verso comprido vazava do cartão** (achado pelo usuário no iPhone): as duas
  faces ficavam uma sobre a outra com o verso em `absolute inset-0`, então o
  cartão tinha a altura da frente e um verso longo (critérios de CAD e EHH)
  passava por cima do "Editar" e dos botões de nota. Agora as faces dividem a
  mesma célula de uma grade (`col-start-1 row-start-1`), e o cartão tem a
  altura da face mais longa; o giro em 3D não mudou.

- **O baralho vazava da pasta no celular** (também no iPhone): a grade dos
  baralhos só declarava colunas a partir do `sm:`, e a coluna implícita do
  celular cresce até a largura mínima do conteúdo — um nome com `truncate` não
  quebra linha, então empurrava o bloco para fora, e o `overflow-hidden` da
  pasta cortava o "Estudar". `grid-cols-1` (`minmax(0, 1fr)`) prende a coluna;
  medido a 393px com o CSS compilado: vazava 83px, agora fica dentro. A grade
  do cartão que vira tinha a mesma armadilha para uma palavra longa (uma URL
  colada no verso) e ganhou o mesmo `grid-cols-1` e `overflow-wrap: anywhere`.
  **Regra**: grade com coluna só no `sm:` precisa de `grid-cols-1` na base.

- **Crítica de interface (skill Impeccable) e "celular primeiro".** A crítica
  deu 31/40; o que pesou foi o celular, onde as alunas estudam. O usuário
  escolheu começar por ele (resto da ordem nas Pendências).
  - *Abas no rodapé* abaixo de 1024px (`Topbar.tsx`), no lugar do menu ☰:
    cinco colunas iguais, ícone e rótulo, a contagem de revisões e de cartões
    no canto do ícone e o traço de 2px `--ink` na borda de cima, deslizando
    como o sublinhado das abas. Somem no modo foco. O `main` reserva 80px
    (56 da barra + o respiro) fora do modo foco; o aviso de respostas
    pendentes, que morava no canto de baixo, sobe para baixo da barra superior
    nessa largura e entra de cima (`--presenca-y`). Sem `viewport-fit=cover`
    no `index.html`, de propósito: com ele o iPhone deitado poria a marca
    embaixo do entalhe, e sem ele o sistema já mantém a página fora da área do
    indicador de início; o `env(safe-area-inset-bottom)` fica na barra para o
    dia em que isso mudar.
  - *A ação da vez no pé da tela* nas sessões de Praticar e Revisão
    (`ACAO_DA_VEZ`, em `lib/estilos.ts`), abaixo de 640px: `sticky`, e não
    `fixed`, porque o caso entra com `transform`; no fim do cartão ela volta ao
    lugar, como rodapé dele. As teclas de atalho (`Kbd`) somem abaixo de 640px.
    Medido a 393px: 69px de rodapé para Confirmar e para Próximo caso ("Volta
    em 10 min" encurtado para caber na mesma linha), 121px para os dois
    botões do acerto no Praticar (empilhados; somem com o item 2 das
    Pendências) e 116px para as três notas da Revisão, numa linha só também a
    360px porque cada botão tem a largura do rótulo, e não um terço da faixa.
  - A lixeira do baralho, que só aparecia no hover, fica visível sem ponteiro
    fino (`@media (hover: none)`): escondida, continuava tocável no canto do
    bloco.
  - Conferido no localhost com uma conta `pytest_…@teste.local` criada pelo
    `/auth/signup` local (sem `BREVO_API_KEY` na máquina, nenhum e-mail sai) e
    confirmada pelo banco como no `conftest.py`, com o cookie posto num Edge
    headless por CDP; apagada no fim. No computador nada mudou: rodapé oculto,
    `pb` de 36px, linha de ação no lugar com as teclas.
  - **No ar em 25/09** (commit `731bd06`), depois de o usuário ver o resultado
    numa janela do Edge simulando o celular no localhost (perfil próprio,
    `setDeviceMetricsOverride` 393×852, toque no lugar do mouse, com o CDP
    preso enquanto a janela vive). Fechar as abas extras que o Edge abre na
    primeira execução de um perfil novo derruba a janela do app junto: abrir
    de novo com o mesmo perfil, que já não abre nada além dela.

- **Chute antes de confirmar** (item 2 da crítica, decidido pelo usuário). O
  "Acertei no chute / Acertei com segurança" era perguntado depois do
  gabarito, quando quase todo mundo lembra de ter tido certeza, e custava um
  toque a mais em todo acerto. Agora o interruptor "Estou chutando"
  ("Chutando" no celular) fica ao lado do Confirmar, e depois de confirmar há
  um "Próximo caso" só, com Enter ou →; o acerto chutado avisa "vale meio no
  Painel". A tecla é `?`, e não o `C` que estava no plano: o C já seleciona a
  alternativa C. O que vai para o servidor: acerto sem a marca = `seguro`
  (qualidade 5), acerto chutado = `chute` (3), erro chutado = `chute`
  (qualidade 1 de todo jeito, mas fica o registro de que era palpite), erro
  sem a marca = nada, como antes — os quatro conferidos no banco com uma conta
  de teste. Backend sem mudança: `praticar.py` já mapeava `seguro` para 5 e o
  resto para 3. No celular o rodapé do acerto caiu de 121px para 69px, o mesmo
  dos outros estados. A dica "M marcar" saiu da linha de ação para o
  interruptor caber ao lado do Confirmar no computador; o atalho continua no
  título do botão Marcar da barra. **No ar em 25/09** (commit `c014a57`),
  depois de o usuário testar na janela que simula o celular.

- **"Conduta de hoje" no Painel** (item 3 da crítica). O Painel tinha oito
  blocos, mais de dez botões de praticar, e a fila de revisão era o sétimo.
  Logo abaixo do título entrou a "Conduta de hoje" (`CondutaHoje.tsx`):
  diagnóstico e depois conduta, a ordem do raciocínio clínico, e o nome é o
  da marca. Até três passos — revisão, cartões (só quando há cartão vencido) e
  o tema nº 1 das prioridades — com um botão primário só, o do primeiro
  pendente. O seletor da meta de revisão veio junto, porque decide a primeira
  linha. Ficou em segundo lugar, e não acima do título, para o h1 continuar
  sendo o primeiro da página e a identidade abrir no diagnóstico; medido a
  393px, ela cabe inteira na primeira tela (379–733px, acima da barra de
  abas). "Onde você ganha mais pontos" perdeu o botão primário (o primeiro
  tema já é o passo da conduta). O `FilaRevisao.tsx` saiu: a contagem, a
  meta e o "Revisar" foram para a conduta, e a previsão de 7 dias foi para a
  seção **Evolução**, recolhida por padrão, junto com Por tipo, os 14 dias e a
  Evolução da memória; fechada ela não desenha nada, e aberta uma vez fica
  aberta no aparelho (`localStorage`). O passo dos cartões abre o "Estudar
  tudo" por `/baralhos?estudar=tudo`, o mesmo padrão do `?estudar=1` do
  baralho. Conferido com uma conta de teste: um primário só na página,
  Evolução fechada sem gráficos no DOM, aberta depois de recarregar, e o link
  dos cartões caindo direto no estudo. **No ar em 25/09** (commit `8619822`),
  depois de o usuário ver na janela que simula o celular e manter a conduta
  abaixo do título.

- **Triagem de entrada — descartada** (item 4 da crítica). Foi construída e
  testada: o Painel sem respostas virava "Comece pela triagem.", com a data da
  prova e uma sessão de 25 casos, 5 de cada grande área, para o quadro
  classificar as cinco no primeiro dia. O usuário viu na janela que simula o
  celular e não quis, por três motivos juntos: longa demais para quem acabou
  de chegar (uns 40 min), a tela de entrada não agradou, e **empurrava para um
  caminho** quando ele prefere que a pessoa escolha livremente o que praticar.
  O código saiu inteiro (nada foi commitado); o Painel da conta nova continua
  o estado vazio com "Praticar agora", que abre o Configurador. Não repropor
  onboarding guiado sem o usuário pedir.
  - Achado no caminho, e mantido: no celular o **resumo da sessão** escondia o
    nome de cada especialidade. A linha era `minmax(0,1fr)` para o nome e
    `minmax(80px,200px)` para a barra, e o algoritmo da grade faz a trilha de
    teto fixo crescer até o teto antes de dar espaço à `1fr` — a 393px o
    nome ficava com 0px. No celular o nome agora ocupa a linha de cima
    (conferido: 319px de largura e a barra embaixo). **No ar em 25/09**
    (commit `169c321`).

- **Itens menores da crítica** (o usuário deixou a escolha comigo).
  - *Ofensiva*: `db.calcular_ofensiva` lia só `respostas`, e a **Revisão de
    casos não passa por lá** (grava em `revisao_eventos`) — então não só os
    cartões: quem passava o dia só revisando casos também perdia a sequência,
    o que era pior do que a crítica tinha visto. Agora é a união das datas de
    `respostas`, `revisao_eventos` e `revisao_cartao_eventos`, os três do
    mesmo relógio (`datetime.now()`); dois testes novos em
    `test_ofensiva.py`, um por fonte. O título da etiqueta diz "estude hoje
    para manter (casos, revisão ou cartões)". O campo continua
    `respondeu_hoje` no `/me`, para não quebrar cliente aberto.
  - *Meta fixa de 20*: o cabeçalho dizia "{n} de 20 questões hoje", uma meta
    que ninguém escolheu, ao lado da meta de revisão da Conduta de hoje.
    Ficou "{n} questões hoje".
  - *Apagar pasta e baralho*: o `window.confirm` virou o `Dialog` do app, com
    o que vai junto ("Os 2 cartões dele vão junto. Não dá para desfazer.") e
    o foco em "Cancelar" ao abrir. Conferido no localhost: cancelar não
    apaga, "Apagar" apaga, pasta vazia diz que está vazia.

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
