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
- **Materiais de estudo (MediaFire)**: biblioteca organizada por
  área → subtópico → tipo de material (Apostila, Videoaula, Vídeo
  Bônus, Vídeo Apostila etc.), com botão que abre o link da sua pasta
  compartilhada do MediaFire — e um botão para baixar cada material
  para um cache local (acesso offline), um de cada vez.
- **Importação em massa de questões**: sobe um Excel (.xlsx) ou CSV
  com centenas de questões de uma vez (tem botão para baixar um
  modelo pronto). Detecta duplicatas e mostra um relatório de erros
  linha a linha.
- **Sincronização automática com o MediaFire**: cole o link da pasta
  raiz compartilhada e o app varre sozinho toda a árvore (áreas →
  assuntos → arquivos), cadastrando tudo como material. Pode rodar
  de novo quantas vezes quiser — arquivos já importados não duplicam.

## Como instalar e rodar

1. Tenha o **Python 3.10+** instalado.
2. Abra um terminal dentro da pasta `residencia_med`.
3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

4. Rode a aplicação:

   ```bash
   streamlit run app.py
   ```

5. O navegador vai abrir automaticamente em algo como
   `http://localhost:8501` — essa é a sua plataforma rodando localmente.

Os dados ficam salvos em `data/residencia.db` (SQLite), então tudo o
que você cadastrar (questões, respostas, materiais) persiste entre
uma sessão e outra.

## Como sincronizar a pasta do MediaFire

1. Abra a tela **"Sincronizar MediaFire"** no menu lateral.
2. Cole o link da sua **pasta raiz compartilhada** (o link que começa
   com `https://www.mediafire.com/folder/...`). Só funciona com pastas
   com compartilhamento público (não pede login).
3. Clique em **"Sincronizar agora"**. O app usa a API pública de
   leitura do MediaFire para listar recursivamente todas as subpastas
   e arquivos — sem precisar cadastrar link por link.
4. A estrutura esperada é: `Pasta raiz → Área (ex: Cardiologia) →
   Assunto (ex: Arritmias) → arquivos`. Subpastas extras dentro do
   assunto (ex: "Apostilas", "Videoaulas") também são lidas
   normalmente. O tipo de cada material (Apostila, Videoaula, Vídeo
   Bônus, Vídeo Apostila) é inferido automaticamente pelo nome do
   arquivo/pasta.
5. Pode rodar de novo sempre que adicionar arquivos novos: o que já
   foi importado antes é reconhecido e não duplica.

⚠️ Isso depende de conexão com a internet (a API é chamada em tempo
real) e do formato de pastas públicas do MediaFire — se a Mediafire
mudar sua API sem aviso, a sincronização pode passar a falhar; nesse
caso, o cadastro manual (tela "Materiais de Estudo") continua
funcionando como alternativa.

## Como baixar materiais para acesso offline

A sincronização acima só importa os **links** dos arquivos — o
conteúdo continua hospedado no MediaFire. Se quiser acesso offline a
algum material específico:

1. Na tela **"Materiais de Estudo"**, ao lado de cada material, clique
   em **"⬇️ Baixar para cache"**.
2. O app resolve o link direto de download da página do MediaFire e
   baixa o arquivo para `data/materiais_cache/` no seu computador.
   Isso é sempre manual, material por material — vídeos podem ter
   centenas de MB, então nada baixa sozinho.
3. Um material já em cache mostra o tamanho do arquivo baixado e um
   botão **"🗑️"** para remover o cache (libera espaço em disco sem
   apagar o material cadastrado nem o link original).
4. O total de espaço ocupado pelo cache aparece no topo da lista de
   materiais.

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
