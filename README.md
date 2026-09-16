# Plataforma de Estudos para Residência Médica

Aplicação local (roda no seu computador) para apoiar a preparação para
provas de residência médica (ENAMED e principais instituições de SP),
inspirada em plataformas como a Medcof.

## Funcionalidades da versão atual (MVP)

- **Banco de questões**: cadastro de questões por área/subtópico, com
  alternativas, resposta correta, explicação, banca e ano.
- **Responder questões**: modo de estudo em lote, com correção imediata.
- **Dashboard de desempenho**: gráficos de % de acerto por área, por
  subtópico e por banca/instituição (com comparativo cruzado
  banca × área), evolução diária e ranking das questões mais
  erradas — para você enxergar rápido onde estão seus pontos fracos.
- **Repetição espaçada**: fila de revisão baseada em um algoritmo
  estilo Anki/SM-2 — questões erradas voltam mais cedo, questões
  dominadas voltam com intervalos maiores.
- **Simulado cronometrado**: monte uma prova no formato ENAMED/SP —
  escolha o número de questões, filtre por área e/ou banca, defina o
  tempo limite e responda sem correção imediata (igual numa prova de
  verdade). Ao final (ou quando o tempo acaba), você vê a nota, o
  desempenho por área naquele simulado e a revisão completa de cada
  questão, com gabarito e explicação.
- **Importação em massa de questões**: sobe um Excel (.xlsx) ou CSV
  com centenas de questões de uma vez (tem botão para baixar um
  modelo pronto). Detecta duplicatas e mostra um relatório de erros
  linha a linha.

## Como importar questões em massa

1. Abra **"Importar Questões (planilha)"** no menu lateral.
2. Baixe o modelo `.xlsx`, preencha suas questões seguindo o mesmo
   formato (uma linha por questão) e salve.
3. Suba o arquivo (.xlsx ou .csv) — o app mostra uma prévia antes de
   importar.
4. Clique em **"Importar todas as questões"**. Você recebe um
   relatório com quantas foram importadas, quantas já existiam
   (ignoradas) e quais linhas tiveram problema (com o motivo).

## Como fazer um simulado cronometrado

1. Abra **"Simulado"** no menu lateral.
2. Escolha o número de questões (10/20/30/50 ou um valor
   personalizado), filtre por área e/ou banca se quiser, e ajuste o
   tempo limite (o app já sugere um valor com base na quantidade de
   questões, mas você pode editar).
3. Clique em **"Iniciar simulado"**. Se não houver questões
   suficientes para o filtro escolhido, o botão fica desabilitado e o
   app avisa quantas estão disponíveis.
4. Responda as questões na ordem que preferir — dá para navegar entre
   elas (Anterior/Próxima ou pelo seletor "Ir para questão") e as
   respostas ficam salvas mesmo se você voltar. Não há correção
   imediata, só o cronômetro no topo da tela.
5. Ao clicar em **"Finalizar Simulado"** (ou quando o tempo acabar
   sozinho), você vê a nota final, o desempenho por área daquele
   simulado e a revisão completa — cada questão com sua resposta, o
   gabarito e a explicação. As respostas também alimentam o Dashboard
   geral e a fila de Repetição Espaçada, como se você tivesse
   respondido na tela "Responder Questões".
6. Um histórico dos últimos simulados concluídos fica disponível na
   própria tela de configuração.
