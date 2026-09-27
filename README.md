# Conduta

As provas oficiais do Revalida e do ENAMED, comentadas. O Conduta é uma plataforma de estudo para o Revalida, o ENAMED e provas de residência médica, no ar em **[qualaconduta.com.br](https://qualaconduta.com.br)**.

## O que tem

- **Provas oficiais, questão por questão.** Os cadernos do Revalida e do ENAMED na ordem em que caíram, e provas de residência de São Paulo (USP e UNICAMP). As questões anuladas ficam de fora.
- **O porquê de cada alternativa.** Você responde, vê na hora qual era a conduta e lê por que cada alternativa está certa ou errada.
- **Painel.** O desempenho por grande área, em níveis ancorados na nota de corte, e os temas onde você mais perde pontos.
- **Revisão espaçada.** Cada caso respondido volta no dia certo: dez minutos depois de um erro, e cada vez mais espaçado quando você lembra.
- **Simulados.** A prova inteira ou em blocos de até 25 questões, com 3 minutos por questão, como no dia. No Revalida, o resultado vem ao lado da nota de corte da edição.
- **Cartões.** Flashcards próprios, que seguem o mesmo ritmo da revisão.

As questões são das provas oficiais publicadas pelo INEP, pela FUVEST e pela COMVEST. As explicações são próprias do Conduta, escritas para cada questão e revisadas uma a uma.

## Como é feito

| Parte | O que é |
|---|---|
| `frontend/` | O app dos alunos: React 19, Vite, TypeScript e Tailwind CSS 3, no sistema visual descrito em `DESIGN_TRIAGEM.md`. |
| `api/` | A API, em FastAPI. A sessão fica num cookie httpOnly. |
| `db.py`, `repeticao_espacada.py` | Toda a regra de negócio — filtros, revisão espaçada (SM-2), ofensiva, painel —, usada igual pela API e pelo admin. |
| `app.py`, `ui.py`, `auth.py` | As telas de administração, em Streamlit: banco de questões, importação e uso da plataforma. |
| `scripts/` | Importação de provas oficiais, rotina diária (relatório e lembretes), backup e manutenção do banco. |

O banco é Postgres (Neon), o e-mail sai pelo Brevo, e a produção roda num servidor da Oracle Cloud atrás do Caddy, com HTTPS.

## Rodar localmente

Precisa de Python 3, Node.js e um banco Postgres. A conexão vem de `DATABASE_URL`, como variável de ambiente ou em `.streamlit/secrets.toml` (fora do git).

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload     # API em http://localhost:8000

cd frontend
npm install
npm run dev                       # app em http://localhost:5173

streamlit run app.py              # admin em http://localhost:8501
```

Outras variáveis, todas opcionais para desenvolver:

| Variável | Para quê |
|---|---|
| `JWT_SECRET_KEY` | Assina as sessões. Sem ela, cada processo sorteia uma e as sessões caem quando a API reinicia. |
| `ADMIN_EMAILS` | E-mails com acesso de admin, separados por vírgula. Sem ela, ninguém é admin. |
| `BREVO_API_KEY`, `EMAIL_REMETENTE` | Envio de e-mail: a chave do Brevo e o endereço de quem envia. Sem as duas, o e-mail — com o link de confirmação ou de troca de senha — vai para o log da API. |
| `EMAIL_REMETENTE_NOME` | Nome de quem envia os e-mails (padrão: Conduta). |
| `COOKIE_SECURE` | `true` quando o site é servido em HTTPS. |
| `CORS_ORIGENS` | Origens que podem chamar a API, separadas por vírgula. |
| `DATABASE_URL_TESTES` | Banco separado para os testes (abaixo). |

## Testes

```bash
pytest                                  # tudo
pytest tests/test_sm2.py                # um arquivo
pytest tests/test_sm2.py::test_nome     # um teste
cd frontend && npm run lint && npm run build
```

Os testes gravam no banco. Defina `DATABASE_URL_TESTES` apontando para um banco separado: sem ela, eles usam o mesmo `DATABASE_URL` do app.

## Documentação

- `CLAUDE.md` — a arquitetura e as regras do código, incluindo decisões que não se mudam sem motivo.
- `DEPLOY.md` — como a produção está montada e como subir uma versão.
- `HISTORICO.md` — por que as coisas são como são, e o que está pendente.
- `MIGRACAO.md` — a passagem do Streamlit para FastAPI + React.
- `DESIGN_TRIAGEM.md` — o sistema visual.
