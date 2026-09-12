# Migração: Streamlit → FastAPI + React

> Para o agente que vai executar: leia este arquivo, depois `REDESIGN.md` (os tokens e o comportamento de cada tela continuam valendo integralmente) e `HANDOFF_REDESIGN.md` (o que já existe e por quê). Antes de escrever código, leia `db.py`, `repeticao_espacada.py` e `app.py` inteiros e confirme o contrato da seção 2 contra o que está de fato no código — este documento foi escrito sem acesso aos arquivos.

## 0. Objetivo e critério de sucesso

O produto é uma plataforma de preparação para residência médica / ENAMED, hoje em Streamlit, com o redesign visual já implementado. O trabalho atual **não é mudar o design** — é mudar a camada de execução, para que o produto tenha a fluidez que o Streamlit não permite.

A migração está concluída quando, no fluxo de Praticar:

1. Clicar numa alternativa mostra o feedback **no mesmo frame**, sem esperar resposta do servidor.
2. A questão seguinte já está em memória quando o aluno avança — avançar não tem carregamento visível.
3. `A`–`E` seleciona, `Enter` confirma, `→` avança, `M` marca para revisão, sem tocar no mouse.
4. Nada na tela se desloca quando um dado chega (sem layout shift).
5. Navegar entre telas não recarrega a página.

Esses cinco pontos são o critério. Se algum não for atingido, a migração não cumpriu seu propósito, porque o objetivo declarado é impressionar pela fluidez da interface.

## 1. Stack e o que sobrevive

**Sobrevive inteiro** (não reescrever, não reimplementar em JS): `db.py`, `repeticao_espacada.py` e toda a lógica de SM-2, filtros, ofensiva e estatísticas. O algoritmo de repetição espaçada continua sendo executado em Python, em um único lugar. Lógica de agendamento duplicada no cliente é a forma mais rápida de criar bug silencioso de estudo.

**É descartado**: `app.py` e `ui.py` — a camada de view.

**Backend**: FastAPI, importando os módulos Python existentes. SQLite continua, com WAL habilitado (`PRAGMA journal_mode=WAL`). Postgres só quando houver concorrência real de escrita; até lá é complexidade sem retorno.

**Frontend**: Vite + React + TypeScript, com TanStack Query para dados e Tailwind para estilo. Não use Next.js nesta fase: o backend já é Python, então SSR e rotas de API do Next não servem para nada aqui, e o build estático do Vite é mais simples de hospedar. Se depois houver landing page pública com SEO, ela é um projeto separado, não este.

**Roteamento**: React Router, com rotas por chave estável (`/praticar`, `/banco`), nunca derivadas do rótulo exibido no menu. Esse acoplamento já quebrou sessões uma vez neste projeto.

## 2. Contrato da API extraído (confirmado contra `db.py`, `repeticao_espacada.py` e `app.py` — 2026-09-12)

> Esta seção foi reescrita depois de ler os três arquivos por inteiro. O esqueleto original (abaixo, riscado no histórico do git) foi escrito sem acesso ao código e errava em pontos estruturais: assumia SQLite (o projeto já é 100% Postgres/Neon, com pool de conexões — isso já está resolvido, não precisa WAL nem decisão de concorrência), tratava `POST /respostas` como uma escrita isolada (é sempre duas: resposta + revisão SM-2), e omitia telas inteiras que já existem e funcionam (Simulado, Áreas/Subtópicos, imagem de questão, edição/exclusão de questão). A lista abaixo é a real.

```
POST   /auth/signup                   → {email, senha} → cria usuário (bcrypt), token
POST   /auth/login                    → {email, senha} → token
POST   /auth/logout

GET    /me                            → email, is_admin, tema, prova_alvo, ofensiva,
                                        respondidas_hoje, contadores (questões/materiais)
PATCH  /me/tema                       → {tema}
PATCH  /me/prova-alvo                 → {data_iso | null}

GET    /painel                        → desempenho por área (+ por banca, hoje não
                                        consumido pela tela mas já calculado em 1 query),
                                        série de 14 dias, revisões de hoje (contagem)
GET    /praticar/sessao?filtros...    → lote de questões JÁ COM gabarito, comentário e
                                        estado "marcada" embutidos (função nova — hoje só
                                        existem ids filtrados, sem batch fetch)
POST   /respostas                     → {questao_id, alternativa, confianca, tempo_ms}
                                        grava resposta E aciona o SM-2 na mesma chamada
                                        (qualidade derivada de acerto+confiança)
GET    /questoes/{id}/distribuicao    → % de escolha por alternativa
POST   /questoes/{id}/marcar
DELETE /questoes/{id}/marcar

GET    /revisao/leva                  → orquestra 3 fontes com dedup (pendentes + nunca
                                        revisadas + marcadas) — hoje só existe montado
                                        dentro de app.py, não é uma função de db.py
POST   /revisao/{id}/avaliar          → {qualidade} → agenda no SM-2 e desmarca a questão
                                        se estava marcada e qualidade != 1

GET    /areas                         GET  /areas/{id}/subtopicos
POST   /areas                         POST /areas/{id}/subtopicos

GET    /questoes?...                  → banco, paginado
GET    /questoes/bancas               GET /questoes/anos      (metadados de filtro)
POST   /questoes                      → nova questão
PUT    /questoes/{id}                 → editar questão
DELETE /questoes/{id}
POST   /questoes/{id}/imagem          (multipart)   DELETE /questoes/{id}/imagem
POST   /questoes/importar             → planilha
GET    /questoes/importar/template    → download do modelo .xlsx

GET    /materiais?area=&subtopico=&tipo=&q=
POST   /materiais
DELETE /materiais/{id}
DELETE /materiais                     → zona de risco, admin only
GET    /sincronizacao                 → status do MediaFire
POST   /sincronizacao                 → ver nota sobre progresso ao vivo, abaixo

POST   /simulados                     → cria simulado + sorteia questões
GET    /simulados                     → histórico
GET    /simulados/{id}                GET /simulados/{id}/itens
POST   /simulados/{id}/respostas      → {questao_id, alternativa} (não revela gabarito)
POST   /simulados/{id}/finalizar
GET    /simulados/{id}/desempenho

GET    /busca?q=                      → questões + materiais (ver seção 5) — hoje não
                                        existe NENHUMA função de busca combinada
```

**O ponto crítico continua sendo `GET /praticar/sessao`**, e é o item que mais diverge do código real: hoje `app.py` não carrega lote nenhum — carrega só os ids filtrados (`db.ids_questoes_filtro_pratica`), embaralha no cliente Streamlit, e busca cada questão individualmente (`db.obter_questao`) conforme o aluno avança. Não existe hoje nenhuma função que busque N questões completas a partir de uma lista de ids — precisa ser escrita (`obter_questoes_por_ids` ou similar). É a função mais importante da Fase 1, porque o critério de sucesso do §0 depende inteiramente dela.

Isso significa que o gabarito trafega para o cliente antes de o aluno responder. Para um app de estudo, isso é aceitável — quem inspecionar o network para colar está sabotando o próprio preparo. Não invente autenticação de gabarito por questão; custa a fluidez inteira para proteger nada.

`POST /respostas` é fire-and-forget do ponto de vista da interface: o cliente não espera a resposta para mostrar o feedback. Enfileire as gravações e trate falha com retry silencioso e um aviso discreto se a fila não drenar. Internamente, porém, esse endpoint faz duas escritas (resposta + revisão SM-2), nunca uma só — replicar exatamente o par `db.registrar_resposta` + `sr.registrar_revisao` que `app.py` sempre chama junto.

`POST /sincronizacao` hoje transmite progresso ao vivo (`mediafire_import.sincronizar_pasta_raiz(..., on_progress=callback)` atualizando a tela linha a linha). Um request/response comum não reproduz isso. Decidir explicitamente: aceitar perder o log ao vivo (mostrar só o relatório final) ou implementar SSE/WebSocket. Como esta é uma das telas administrativas da seção 5 (candidata a ficar no Streamlit), a decisão pode ser adiada até lá.

## 3. Autenticação

O login do Streamlit não migra como está. Use sessão por cookie `httpOnly` assinado, ou JWT curto com refresh. Hash de senha com `bcrypt` ou `argon2` — se o código atual guardar senha em texto ou com hash fraco, corrija nesta migração e force redefinição. Isso precisa ser resolvido antes de qualquer link público existir.

## 4. Ordem de execução

Execute nesta ordem e pare para revisão ao fim de cada fase. Não comece a fase seguinte sem aprovação.

**Fase 1 — API.** FastAPI expondo autenticação e os endpoints da seção 2, com Pydantic em todas as respostas. Testes `pytest` cobrindo o SM-2, o cálculo de ofensiva e os filtros de prática. Esses testes são a única rede de segurança da migração: se a lógica Python continuar correta, o resto é camada de apresentação. O Streamlit continua rodando em paralelo o tempo todo, apontando para o mesmo banco.

**Fase 2 — Fundação do frontend.** Vite + React + TS, tokens do `REDESIGN.md` portados para `theme.css` como variáveis CSS e mapeados no `tailwind.config`, IBM Plex Sans/Mono, tema claro/escuro por classe no `<html>` com preferência persistida, shell (rail + topbar) e roteamento. Sem telas de conteúdo ainda.

**Fase 3 — Praticar. Esta é a fase que define o resultado.** Os cinco critérios da seção 0 valem aqui e são verificados antes de seguir adiante. Detalhes de implementação:

- O lote de questões vive em estado de cliente. Responder não dispara requisição bloqueante.
- Atalhos registrados num `useEffect` com `keydown` no `document`, desativados quando o foco está num campo de texto. Mostre os atalhos discretamente no rodapé — parte do efeito é a pessoa descobrir que existem.
- `A`–`E` seleciona, `Enter` confirma, `→` avança, `M` marca, `Esc` fecha overlay.
- A revelação do resultado é uma transição de 180ms na alternativa; nada mais na tela se move. Reserve o espaço do comentário antes de ele aparecer.
- Cronômetro por questão em `requestAnimationFrame` ou intervalo de 1s, com numerais tabulares para não tremer.
- `prefers-reduced-motion` respeitado.
- Nada de spinner de tela cheia em lugar nenhum: skeletons com as dimensões finais.

**Fase 4 — Painel.** Uma chamada só para todos os dados. Gráficos com Recharts ou D3, seguindo as regras da seção 6 do `REDESIGN.md`: barras horizontais, rótulo direto na ponta, sem grade vertical, no máximo três cores semânticas, estado de dados insuficientes com texto.

**Fase 5 — Revisão Espaçada e Simulado.** Aproveite para resolver duas dívidas registradas no handoff: os três estados da grade de navegação do Simulado (respondida / marcada / em branco), e o campo de timestamp em `revisao.proxima_revisao`, para que "Errei — 10 min" signifique de fato 10 minutos em vez de pular para o dia seguinte.

**Fase 6 — Materiais e busca global.** A busca do topbar precisa funcionar de verdade ou ser removida. Ver seção 5.

**Fase 7 — Telas administrativas. Decidido em 2026-09-12: NÃO migrar — ver seção 5.** Banco de Questões, Nova Questão, Importar Planilha e Sincronizar MediaFire continuam no Streamlit permanentemente, não só como plano B temporário.

## 5. Decisão sobre as telas administrativas

**Decidido em 2026-09-12: manter no Streamlit.** As quatro telas da fase 7 são de administração — só o usuário as usa, e ninguém vai avaliar a fluidez delas. O Streamlit continua rodando *permanentemente* (não só como plano B durante a migração) apontando para o mesmo banco, como ferramenta interna. Migrar também ficaria como opção futura só se a plataforma ganhar outros administradores além do dono.

Consequência prática registrada em `frontend/`: as rotas `/banco`, `/nova-questao`, `/importar` e `/sincronizar` no React nunca vão ganhar tela própria — `pages/PermaneceNoStreamlit.tsx` mostra um estado que explica isso e linka pra raiz do Streamlit (`VITE_STREAMLIT_URL`, default `http://localhost:8501` em dev). Streamlit não roteia por URL (a tela é escolhida por `session_state`), então o link abre a raiz do app, não a tela específica — o usuário clica de novo no menu lateral do Streamlit uma vez lá.

Isso também muda a seção 7 (Publicação): o Streamlit precisa continuar acessível em produção, não só durante a migração — ver nota lá.

A busca global (fase 6, já implementada) usa `ILIKE` (não `LIKE`) em enunciado de questão e nome de material — o Postgres é case-sensitive por padrão em `LIKE`, ao contrário do SQLite que a versão original deste documento assumia estar em uso (ver nota da seção 2). Resultados agrupados por tipo, questões/materiais, funcionando de verdade.

## 6. Erros a não cometer

- **Reimplementar o SM-2 em TypeScript.** Uma fonte de verdade, em Python.
- **Esperar o servidor para mostrar o feedback da alternativa.** Isso anula o motivo inteiro da migração.
- **Migrar tudo antes de mostrar qualquer coisa.** A fase 3 já deve ser demonstrável e impressionante sozinha.
- **Recriar os problemas do Streamlit em React**, como spinner de tela cheia a cada navegação ou layout que pula quando o dado chega.
- **Descartar o Streamlit cedo.** Ele fica no ar até a fase 7 ser decidida; é o seu plano B enquanto a API ainda não está estável.
- **Inventar um design novo.** O `REDESIGN.md` é a especificação. Em React ele finalmente pode ser implementado como foi escrito, sem gambiarra.

## 7. Publicação

Antes de qualquer link ser compartilhado com alguém: build estático do frontend servido por Caddy ou Nginx, API atrás do mesmo domínio em `/api`, HTTPS, e um usuário de demonstração populado com algo como 400 respostas espalhadas por 8 semanas, com desempenho desigual entre áreas. Um dashboard com 14 respostas parece amador independentemente da qualidade do código.

**Ponto não coberto pela versão original deste documento** (a decisão da seção 5 só veio depois): como o Streamlit fica no ar permanentemente, ele também precisa de um lugar em produção — não só em dev. Opções a decidir antes de publicar: um subdomínio próprio (`admin.dominio.com`) ou um path reverso-proxiado (`/admin`) apontando pro processo Streamlit, com o mesmo HTTPS e atrás do mesmo login (o Streamlit tem autenticação própria, separada da sessão JWT da API — hoje são dois logins distintos; avaliar se isso é aceitável pra um único admin ou se vale a pena unificar depois). `COOKIE_SECURE=true` na API e o `VITE_STREAMLIT_URL` do frontend precisam apontar pra URL de produção do Streamlit, não `localhost:8501`.
