# Plataforma de Estudos para Residência Médica

Aplicação local (roda no seu computador) para apoiar a preparação para
provas de residência médica (ENAMED e principais instituições de SP),
inspirada em plataformas como a Medcof.

## Funcionalidades da versão atual (MVP)

- **Banco de questões**: cadastro de questões por área/subtópico, com
  alternativas, resposta correta, explicação, banca e ano.
- **Responder questões**: modo de estudo em lote, com correção imediata.
- **Dashboard de desempenho**: gráficos de % de acerto por área e por
  subtópico, evolução diária e ranking das questões mais erradas —
  para você enxergar rápido onde estão seus pontos fracos.
- **Repetição espaçada**: fila de revisão baseada em um algoritmo
  estilo Anki/SM-2 — questões erradas voltam mais cedo, questões
  dominadas voltam com intervalos maiores.
- **Materiais de estudo (MediaFire)**: biblioteca organizada por
  área → subtópico → tipo de material (Apostila, Videoaula, Vídeo
  Bônus, Vídeo Apostila etc.), com botão que abre o link da sua pasta
  compartilhada do MediaFire.
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

## Como importar questões em massa

1. Abra **"Importar Questões (planilha)"** no menu lateral.
2. Baixe o modelo `.xlsx`, preencha suas questões seguindo o mesmo
   formato (uma linha por questão) e salve.
3. Suba o arquivo (.xlsx ou .csv) — o app mostra uma prévia antes de
   importar.
4. Clique em **"Importar todas as questões"**. Você recebe um
   relatório com quantas foram importadas, quantas já existiam
   (ignoradas) e quais linhas tiveram problema (com o motivo).

## Próximos passos sugeridos

- Simulados cronometrados no formato das provas (ENAMED, SP).
- Estatísticas comparando seu desempenho por banca/instituição.
- Baixar e cachear os arquivos do MediaFire localmente (hoje a
  sincronização importa os links, não o conteúdo dos arquivos).
