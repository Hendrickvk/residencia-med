# Prompt: redesign visual completo — plataforma de residência médica / ENAMED

> Cole o bloco abaixo inteiro na ferramenta que está construindo o app (Claude Code, Cursor, v0, Lovable, etc.).
> Se o app for Streamlit, mantenha a seção 9. Se for React/Next, apague a seção 9 e diga o stack no início.

---

## CONTEXTO

Você é o design lead responsável pela identidade visual de um produto comercial de educação médica. O produto é uma plataforma de preparação para provas de residência médica do Brasil (USP, Unifesp, Einstein, SUS-SP) e para o ENAMED.

O público: estudantes de medicina e médicos recém-formados, 23 a 30 anos, que estudam 4 a 8 horas por dia, muitas vezes de madrugada, em telas grandes, e que já pagam por concorrentes com acabamento visual alto. Eles comparam o produto com Medcof, Estratégia MED, Aristo e Qconcursos. Se a interface parecer um protótipo acadêmico, o produto perde credibilidade antes da primeira questão.

O trabalho principal da interface: **(1) colocar o aluno respondendo questões no menor número de cliques possível e (2) dizer com clareza brutal onde ele está errando.** Tudo que não serve a esses dois objetivos é decoração e deve ser cortado.

A versão atual tem a lógica certa (banco de questões, simulado, revisão espaçada, materiais, gráficos de erro) mas a aparência é de ferramenta interna: componentes padrão do framework, cartões genéricos, gráfico com rótulos girados na vertical, hierarquia tipográfica fraca, nenhuma reação a hover ou clique.

**Reconstrua toda a camada visual e de interação do zero.** Não preserve nada da tela atual: nem a sidebar, nem os botões, nem os cartões de métrica, nem a paleta verde-petróleo, nem a ordem dos elementos. A estrutura de informação abaixo substitui a atual.

---

## 1. DIREÇÃO ESTÉTICA

O vocabulário visual vem do mundo clínico, não do mundo SaaS: prontuário, laudo, exame laboratorial. Isso significa **densidade de informação alta, alinhamento rigoroso, números como protagonistas e cor usada como sinal, nunca como enfeite**. Um laudo de exame não tem gradiente. Ele tem valor, referência e um marcador quando algo está fora da faixa.

Regras não negociáveis:

- **A cor só aparece quando significa alguma coisa.** Verde = acerto, vermelho = erro, âmbar = atenção/revisão vencida, azul = ação. Nada é colorido "para ficar bonito".
- **Gaste ousadia em um lugar só.** O elemento memorável da plataforma é o painel de diagnóstico do dashboard (item 4.1). Todo o resto é quieto, cinza e disciplinado.
- **Proibido**: gradientes decorativos, cartões idênticos empilhados com a mesma sombra, emojis como ícones, rótulos em CAIXA ALTA espaçada acima de cada título, sombras difusas em tudo, ilustrações genéricas de estoque, setas "→" grudadas no texto dos botões, glassmorphism, cantos de 20px+ de raio.
- Sombras: no máximo duas, ambas quase imperceptíveis. Elevação se resolve com contraste de superfície e borda de 1px, não com blur.

## 2. TOKENS DE DESIGN

Declare tudo como variáveis CSS em `:root` e use apenas elas. Nenhum valor hexadecimal solto no código.

### Cor

```
--ink-900: #0D1B2A   /* fundo da barra de navegação, títulos de maior peso */
--ink-700: #1B2D42
--ink-500: #46586E   /* texto secundário */
--ink-300: #8797AB   /* texto terciário, placeholders */
--line:    #E1E6EC   /* todas as bordas e divisores */
--canvas:  #F4F6F9   /* fundo da área de conteúdo (cinza-frio, nunca creme) */
--surface: #FFFFFF   /* fundo de tabelas, painéis e questões */

--action:      #1F4FD8   /* azul de ação: botões primários, links, foco */
--action-hover:#1A43B8
--action-soft: #EAF0FF   /* fundo de estados selecionados */

--correct: #0F7A5A
--wrong:   #C2344B
--warn:    #B87309
--correct-soft: #E7F4EF
--wrong-soft:   #FBEBEE
--warn-soft:    #FDF3E3
```

Modo escuro é obrigatório (o público estuda de madrugada): inverta para `--canvas: #0B1420`, `--surface: #121E2C`, `--line: #22313F`, e clareie os sinais para manter contraste AA. Alternância manual no topo, com preferência persistida.

### Tipografia

Uma família para tudo: **IBM Plex Sans** (400, 500, 600, 700). Ela tem caráter institucional e técnico, não tem cara de startup, e tem números tabulares excelentes.

**IBM Plex Mono** é permitido em um único contexto: colunas numéricas, cronômetro do simulado e códigos de questão. É proibido em rótulos, botões ou títulos.

Escala (base 16px, alinhamento à esquerda em todo o produto, nunca centralizado exceto estados vazios):

```
display   34px / 1.15 / peso 600 / tracking -0.02em   — número-herói do diagnóstico
h1        24px / 1.25 / peso 600 / tracking -0.01em
h2        18px / 1.35 / peso 600
corpo     15px / 1.55 / peso 400
apoio     13px / 1.45 / peso 400 / cor --ink-500
numérico  variantes acima + font-variant-numeric: tabular-nums
```

Enunciado de questão: 17px, altura de linha 1.65, largura máxima de 68 caracteres. Esse é o texto que o aluno lê milhares de vezes; ele tem prioridade de legibilidade sobre qualquer outra coisa na tela.

### Espaço, forma, movimento

- Grade de 4px. Espaçamentos válidos: 4, 8, 12, 16, 24, 32, 48, 64.
- Raio: 6px em botões, campos e linhas de lista; 10px em painéis; 999px apenas em selos de status.
- Bordas: 1px sólido `--line`. É o recurso principal de separação.
- Transições: 120ms para hover, 180ms para abrir/fechar, curva `cubic-bezier(0.2, 0, 0.2, 1)`. Nada animando sozinho no carregamento da página. Respeitar `prefers-reduced-motion`.

## 3. ESTRUTURA DA APLICAÇÃO

```
┌──────┬────────────────────────────────────────────────────────┐
│      │  barra superior: contexto · busca · ofensiva · tema · ⦿ │
│ rail ├────────────────────────────────────────────────────────┤
│ 232  │                                                        │
│ px   │   conteúdo — coluna de 1160px, alinhada à esquerda     │
│      │                                                        │
└──────┴────────────────────────────────────────────────────────┘
```

**Barra lateral (rail), 232px, fundo `--ink-900`, altura total, sem sombra.**
Topo: marca em 15px peso 600 com um traço de 3px na cor `--action` à esquerda. Abaixo, botão primário de largura total **"Praticar agora"** — é o atalho mais usado do produto e fica sempre visível.

Itens de navegação, em dois grupos separados por um divisor de 1px em `rgba(255,255,255,.08)` com um rótulo de grupo discreto em 12px `--ink-300`:

- *Estudo*: Painel, Praticar, Simulado, Revisão espaçada, Materiais
- *Acervo*: Banco de questões, Nova questão, Importar planilha, Sincronizar MediaFire

Cada item: ícone de traço 1.5px (Lucide ou Phosphor, nunca emoji) + rótulo 14px, altura de 40px, padding lateral 12px.

- Repouso: texto `rgba(255,255,255,.72)`, fundo transparente.
- Hover: fundo `rgba(255,255,255,.06)`, texto branco, 120ms. Sem deslocamento.
- Ativo: fundo `rgba(255,255,255,.10)`, texto branco, e uma barra de 3px na cor `--action` colada na borda esquerda do item.
- Foco por teclado: contorno de 2px `--action` com 2px de deslocamento.

Rodapé do rail: "458 questões · 1.646 materiais" em 12px `--ink-300`, e o avatar do usuário com menu (Perfil, Assinatura, Sair) que abre para cima.

Colapso para 64px com clique no ícone de recolher; nesse estado só os ícones ficam visíveis e o rótulo aparece como tooltip 300ms após o hover. Estado persistido.

**Barra superior, 56px, fundo `--surface`, borda inferior 1px.**
À esquerda, o nome da tela atual em 15px peso 600. À direita, nesta ordem: campo de busca global (atalho `/`), selo de ofensiva ("12 dias"), contagem regressiva para a prova alvo ("ENAMED em 87 dias"), alternador de tema, avatar. O selo de ofensiva usa `--warn-soft` se o dia de hoje ainda não tem questão respondida e `--correct-soft` se já tem.

## 4. TELAS

### 4.1 Painel

Não use três cartões de métrica idênticos. A abertura é **um painel de diagnóstico único**, largura total, fundo `--surface`, borda 1px, raio 10px, dividido em três faixas verticais por divisores de 1px:

- **Faixa 1 (40%)** — a leitura em linguagem direta: `21,4%` em `display`, e abaixo, em corpo, uma frase construída a partir dos dados reais: "3 acertos em 14 questões. Psiquiatria é a sua maior lacuna." Se o aproveitamento estiver abaixo de 50%, a frase orienta sem dramatizar: "Volume ainda baixo para conclusões. Responda 50 questões para o diagnóstico ficar confiável."
- **Faixa 2 (35%)** — minigráfico de linha dos últimos 14 dias com o percentual de acerto, 48px de altura, sem eixos, sem grade, com apenas o último ponto marcado e rotulado. Se não houver histórico suficiente, mostre a frase "Histórico começa a aparecer no terceiro dia de estudo" no lugar, e não um gráfico vazio.
- **Faixa 3 (25%)** — meta do dia: anel fino de progresso (20 questões, por exemplo) e o botão "Continuar de onde parei".

Abaixo, **"Onde você está errando"** — abandone o gráfico de barras verticais com rótulos girados. Use **uma lista onde a própria linha é a barra**: fundo da linha preenchido proporcionalmente ao percentual de acerto, nome da área alinhado à esquerda em texto horizontal legível, e à direita o percentual em mono tabular mais a fração (`14,3% · 1/7`). Ordenação por prioridade de revisão, não por alfabeto. Faixa de cor por desempenho: abaixo de 40% usa `--wrong-soft`, de 40 a 69% usa `--warn-soft`, 70% ou mais usa `--correct-soft`.

- Hover na linha: borda de 1px `--action`, cursor pointer, e aparece à direita um botão discreto "Praticar 10 desta área".
- Clique na linha: abre a sessão de prática já filtrada por aquela área.
- Áreas com menos de 5 questões respondidas aparecem em uma seção recolhida "Amostra insuficiente (3)", porque 50% de 1/2 não é informação.

Terceiro bloco: **"Revisões de hoje"**, lista compacta com os cartões vencidos da repetição espaçada e um botão "Revisar 12 itens".

### 4.2 Praticar

Antes da sessão, um configurador de uma tela só: área, assunto, banca, ano, dificuldade, quantidade, e dois interruptores ("apenas questões que errei", "excluir questões já respondidas"). Os filtros escolhidos viram *chips* removíveis no topo. Botão primário "Iniciar sessão de 20 questões" — o rótulo muda conforme o número escolhido.

Durante a sessão:

- Cabeçalho fixo: progresso "7 de 20" com uma barra de 3px, cronômetro em mono, e ações "Marcar para revisão" e "Encerrar sessão".
- Metadados da questão em uma linha discreta: banca, ano, área, assunto. Sem caixa alta, sem pontos médios enfileirados.
- Alternativas como linhas clicáveis de altura mínima 52px, com a letra dentro de um quadrado de 28px com borda 1px.
  - Hover: fundo `--action-soft`, borda `--action`.
  - Selecionada (antes de confirmar): borda 2px `--action`, letra com fundo `--action` e texto branco.
  - Teclado: `A`–`E` seleciona, `Enter` confirma, `→` avança. Mostre os atalhos discretamente no rodapé.
- **Ao confirmar**: a alternativa correta ganha fundo `--correct-soft` e borda `--correct`; se o aluno errou, a escolhida ganha `--wrong-soft` e borda `--wrong`. A transição dura 180ms e nada mais na tela se move. Aparece o percentual de acerto dos demais usuários por alternativa como uma barra fina dentro de cada linha.
- O comentário abre abaixo, com o botão "Ver comentário" já expandido por padrão, e dois botões de calibração: "Acertei com segurança" / "Acertei no chute" — isso alimenta a repetição espaçada.
- Ao final: tela de resumo com acertos, tempo médio por questão, desempenho por assunto e o botão "Adicionar os 6 erros à revisão espaçada".

### 4.3 Simulado

Mesmo motor, modo diferente: cronômetro regressivo em destaque no topo, sem feedback por questão, grade de navegação lateral com as questões numeradas em três estados (respondida, marcada, em branco), e um diálogo de confirmação ao finalizar que informa quantas questões ficaram em branco. Aviso visual quando restarem 10 minutos: a cor do cronômetro passa para `--warn`, sem piscar e sem som.

### 4.4 Revisão espaçada

Fila em formato de cartão único centralizado, um por vez. Pergunta, botão "Mostrar resposta", e quatro botões de intervalo com o próximo prazo escrito por extenso em cada um ("Errei — 10 min", "Difícil — 1 dia", "Bom — 4 dias", "Fácil — 10 dias"). Contador de itens restantes no topo. Quando a fila zera, um estado vazio que orienta: "Nenhuma revisão vencida hoje. As próximas 8 vencem na quinta." com o botão "Praticar questões novas".

### 4.5 Materiais

Navegação em duas colunas: árvore de áreas à esquerda (240px, rolagem própria), conteúdo à direita. Os itens são linhas de tabela, não cartões: ícone por tipo (apostila, vídeo aula, vídeo bônus), título, assunto, tamanho, e um botão "Abrir" que só aparece no hover da linha. Busca no topo filtrando em tempo real com destaque do trecho encontrado. Estado de sincronização do MediaFire como uma faixa discreta: "Sincronizado há 2 horas · Sincronizar agora".

### 4.6 Banco de questões, Nova questão, Importar planilha

Tabela densa com cabeçalho fixo, listras de 1px em vez de fundos alternados, altura de linha de 44px, colunas numéricas alinhadas à direita em mono. Seleção múltipla com caixas, barra de ações em lote que sobe do rodapé quando há seleção. Formulário de nova questão em coluna única de 640px, com rótulo acima do campo, texto de ajuda em 13px e validação no *blur*, nunca a cada tecla. O importador de planilha mostra pré-visualização das 10 primeiras linhas com mapeamento de colunas antes de confirmar, e relatório de erros por linha depois.

## 5. ESTADOS OBRIGATÓRIOS PARA CADA COMPONENTE

Nenhum componente é considerado pronto sem os oito estados: repouso, hover, pressionado, foco por teclado, selecionado, desabilitado, carregando, erro.

- **Botão primário**: fundo `--action`, texto branco, altura 40px, peso 500. Hover escurece para `--action-hover`. Pressionado desce 1px. Carregando substitui o rótulo por um spinner de 16px mantendo a largura original para não sacudir o layout. Desabilitado usa `--line` com texto `--ink-300` e `cursor: not-allowed`.
- **Botão secundário**: fundo `--surface`, borda 1px `--line`, texto `--ink-700`. Hover troca a borda para `--ink-300`.
- **Botão de texto**: sem fundo; hover ganha sublinhado, não mudança de cor.
- **Campo de texto**: borda 1px `--line`; foco troca para 1px `--action` mais um halo de 3px `--action-soft`; erro usa `--wrong` com a mensagem abaixo em 13px dizendo o que fazer ("Informe o ano da prova", não "Campo inválido").
- **Carregamento**: *skeletons* com as mesmas dimensões do conteúdo final. Proibido spinner ocupando a tela inteira.
- **Estado vazio**: uma frase que orienta e um único botão de ação. Sem ilustração.
- **Foco por teclado**: sempre visível, `outline: 2px solid var(--action); outline-offset: 2px`. Nunca remover.
- **Notificação (toast)**: canto inferior direito, 4 segundos, uma linha, com o mesmo verbo da ação ("Questão salva" depois de "Salvar questão").

## 6. GRÁFICOS

Tema único aplicado a todos os gráficos, sem as cores padrão da biblioteca.

- Barras horizontais sempre que os rótulos forem nomes de áreas ou assuntos. Texto girado na vertical é proibido.
- Sem linhas de grade verticais; horizontais apenas em `--line` a 50% de opacidade.
- Rótulo de valor direto na ponta da barra, o que elimina a necessidade de eixo numérico.
- Máximo de três cores por gráfico, sempre as semânticas.
- Tooltip com fundo `--ink-900`, texto branco, 13px, canto de 6px, aparecendo em 100ms.
- Todo gráfico tem um estado "dados insuficientes" com texto explicativo no lugar de uma área em branco.

## 7. CONTEÚDO E VOZ

Português do Brasil, tom direto e sem bajulação. Frases em caixa baixa com inicial maiúscula, nunca CAIXA ALTA. Verbos no infinitivo nos botões de ação ("Iniciar sessão", "Importar planilha"). Nada de "Parabéns!", "Incrível!" ou motivação vazia — o aluno quer diagnóstico, não elogio. Mensagens de erro dizem o que aconteceu e o que fazer. Números sempre no formato brasileiro: vírgula decimal e ponto de milhar.

## 8. QUALIDADE MÍNIMA

- Contraste AA em todo texto, inclusive nos rótulos de 13px.
- Navegação completa por teclado, com `Tab` seguindo a ordem visual e `Esc` fechando qualquer camada sobreposta.
- Responsivo até 1024px, quando o rail colapsa automaticamente para 64px; abaixo de 768px, entrega uma leitura de coluna única com navegação em gaveta.
- Nenhuma ação destrutiva sem confirmação nomeada ("Excluir 12 questões").

## 9. NOTAS DE IMPLEMENTAÇÃO EM STREAMLIT

Boa parte da sensação de amadorismo vem do framework, não das cores. Trate estes pontos como parte do redesign:

1. Remova a cromagem padrão: `[client] toolbarMode = "minimal"` no `.streamlit/config.toml`, e esconda `#MainMenu`, `header`, `footer` e o botão de Deploy por CSS. Defina também `[theme]` com as cores dos tokens para que os widgets nativos não destoem.
2. Injete um único bloco de CSS global no início do app (um arquivo `style.css` lido e inserido via `st.markdown(..., unsafe_allow_html=True)`), com as variáveis de `:root` e todas as classes. Não espalhe estilo por vários pontos do código.
3. **Elimine o piscar de tela a cada clique.** É o maior sintoma de protótipo. Use `st.session_state` para todo estado de sessão e envolva o bloco da questão em `@st.fragment` para que responder uma alternativa atualize só aquele trecho, não a página inteira. Evite `st.rerun()` global em interações locais.
4. Substitua `st.metric` e `st.bar_chart` por marcação própria e por Altair com tema customizado — os padrões dessas duas funções carregam a estética que estamos abandonando.
5. Construa a navegação como um componente próprio em HTML/CSS dentro de `st.sidebar`, ou use `st.navigation` com estilização completa. Não use `st.radio` como menu.
6. Padronize larguras com `st.columns` de proporções fixas e um contêiner central com `max-width: 1160px` por CSS, para o conteúdo não se esticar em monitores largos.
7. Carregue as fontes uma vez via `@import` no topo do CSS e declare `font-family` no seletor raiz do app, não em cada componente.

> Se for viável no projeto, considere migrar a camada de interface para React (Next.js + Tailwind + shadcn/ui) mantendo o Python como backend via FastAPI. O nível de acabamento descrito acima é alcançável no Streamlit, mas exige gambiarras de CSS que ficam frágeis a cada atualização do framework.

## 10. ENTREGA

1. Antes de escrever código, apresente o plano de design em um bloco curto: paleta com os hex nomeados, papéis tipográficos, conceito de layout e as três decisões que diferenciam este produto dos concorrentes. Aguarde aprovação.
2. Depois, implemente na ordem: tokens e CSS global → shell (rail + barra superior) → Painel → Praticar → demais telas.
3. Ao final de cada tela, liste o que ficou fora do especificado e por quê.
