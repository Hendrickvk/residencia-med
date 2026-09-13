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
enunciado   18px / 1.7  / 400, largura máxima 68ch
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
- Transições: 120ms hover, 180ms revelação de resposta, `cubic-bezier(0.2, 0, 0.2, 1)`.
  Nada anima sozinho ao carregar. `prefers-reduced-motion` zera tudo.

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
  do nível. Clique leva ao Praticar filtrado; hover revela "Praticar 10".
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
quando houver revisões vencidas, e Materiais — aba ativa com sublinhado de 2px
`--ink`. Entre 1024 e 1279px a etiqueta de ofensiva mostra só o número. Direita: busca global (atalho
`/`), etiqueta de ofensiva (t4-soft se já respondeu hoje, t2-soft se não), botão de
tema e avatar. O menu do avatar tem e-mail, prova alvo, **Acervo** (links do
Streamlit, só para `is_admin`) e Sair.

Abaixo de 1024px as abas viram um menu em gaveta aberto pelo botão à esquerda da
marca; abaixo de 640px a busca some da barra.

**Modo foco** (sessão de Praticar, Simulado em andamento, Revisão com fila): a barra
superior troca as abas por "Sessão de prática · {área}", progresso, cronômetro,
Marcar e Encerrar. O conteúdo fica numa coluna de 840px centralizada.

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
   botão "Praticar 10". Abaixo, legenda das faixas e a linha "Amostra insuficiente".
   Em telas estreitas, as colunas viram grupos empilhados.
3. **Rodapé** em duas colunas: "Fila de revisão" (número em display, "questões
   aguardando reavaliação hoje", botão "Revisar agora") e "Acerto nos últimos 14
   dias" (linha em `--ink` sobre as faixas de nível em transparência, último ponto
   marcado e rotulado; menos de 3 dias: "Histórico começa a aparecer no terceiro dia
   de estudo.").

### Praticar
- **Configurador**: título "Praticar"; campos área, assunto, banca, ano; quantidade
  como botões segmentados (10/20/30/50); dois interruptores; filtros escolhidos
  viram etiquetas removíveis; botão "Iniciar sessão de {n} casos".
- **Sessão (modo foco)**: acima do cartão, "Caso" + número em display à esquerda,
  área · assunto e selo de prova oficial à direita. Cartão com enunciado, imagem,
  pergunta, alternativas e, antes de confirmar, dicas de atalho + "Confirmar
  resposta". Progresso na barra superior: um quadrado por caso (t4 acerto, t1 erro,
  `--line` pendente).
- **Após confirmar**: estados de alternativa (§4) com percentual de escolha;
  bloco "Discussão do caso" com "Resposta correta: {letra}", "Você marcou {letra},
  como {x}% dos outros alunos" (só quando a distribuição chegar; o espaço fica
  reservado; sem respostas de outros alunos: "Ninguém mais respondeu este caso
  ainda." e nenhum percentual nas alternativas) e a explicação. Acertou: "Acertei com segurança" (primário) e "Acertei
  no chute" (secundário). Errou: "Volta na sua revisão em 10 min" (é verdade: o SM-2
  agenda qualidade abaixo de 3 para 10 minutos, `repeticao_espacada.py`) e "Próximo
  caso" com `Enter`.
- **Resumo**: acertos em display, etiqueta de nível do aproveitamento da sessão,
  tempo médio por caso e desempenho por assunto em linhas com barra de nível.

### Simulado
- Mesmo cartão e alternativas do Praticar, sem feedback.
- Barra superior em modo foco com o cronômetro regressivo em display condensado:
  `--ink` normal, t2 com menos de 10 min, t1 com menos de 1 min. Sem piscar.
- Grade de navegação com três estados: respondida (fundo `--ink`), marcada (canto
  t3), em branco (só borda). Questão atual com anel `--focus`.
- Diálogo de finalização informa quantas ficaram em branco.
- Resultado: aproveitamento com etiqueta de nível e quadro de triagem por área do
  simulado.

### Revisão espaçada
- Um caso por vez, contagem restante na barra superior.
- "Mostrar resposta" revela a alternativa correta e a discussão.
- Os quatro intervalos usam a escala: "Errei — 10 min" (t1), "Difícil — 1 dia"
  (t2), "Bom — 4 dias" (t4), "Fácil — 10 dias" (t5). São botões secundários com um
  quadrado de 10px da cor do nível antes do rótulo; nada de borda lateral colorida.
- Fila vazia: estado vazio com a próxima leva ("As próximas 8 vencem na quinta.") e
  "Praticar casos novos".

### Materiais
- Faixa de sincronização discreta no topo.
- Duas colunas: lista de áreas (240px) e tabela densa (ícone por tipo, título com
  destaque do trecho buscado, assunto, tamanho, "Abrir" no hover).

### Login
- Marca grande com o símbolo, frase "Sua plataforma de estudos para residência
  médica", cartão com abas Entrar / Criar conta. Fundo `--ground`.

## 7. Voz

Português do Brasil, direto, sem "Parabéns!". A metáfora da triagem aparece nos
nomes de nível e na organização, não em piadas: nada de "paciente", "óbito" ou
"alta" aplicados ao aluno. Botões no infinitivo ou com o objeto explícito
("Revisar agora", "Próximo caso").
