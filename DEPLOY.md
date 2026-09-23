# Publicação (MIGRACAO.md §7)

Passo a passo pra publicar de verdade. Os passos marcados com ⚠️ dependem
de acesso que só você tem (domínio, servidor, credenciais) — eu não
consigo executá-los sozinho; os demais eu posso rodar se você me der
acesso SSH ao servidor, ou você mesmo copia/cola os comandos abaixo.

## 1. Servidor ✅ Concluído (2026-09-12)

**Oracle Cloud Free Tier, região São Paulo (sa-saopaulo-1)** — mesma
região da `DATABASE_URL` do Neon (`sa-east-1`), e sem custo (Always Free),
diferente da recomendação original de Vultr (pago).

- Instância: `residencia-med`, shape **VM.Standard.E2.1.Micro** (Always
  Free-eligible, x86/AMD, 1 OCPU / 1GB RAM). O shape ARM
  `VM.Standard.A1.Flex` (mais folgado, 1 OCPU/6GB) também é Always Free
  mas ficou sem capacidade disponível em São Paulo no momento da criação
  — trocamos pro Micro x86, que tem specs menores mas atende bem o uso
  atual (um admin, tráfego modesto). Se quiser mais recursos depois, vale
  tentar recriar com o A1.Flex quando a região tiver capacidade.
- Imagem: Canonical Ubuntu 24.04 Minimal (x86_64).
- VCN: `residencia-med-vcn`, criada via wizard "Create a VCN with internet
  connectivity" (inclui subnet pública/privada, Internet Gateway, NAT
  Gateway, route tables e security lists prontos).
- **IP público**: `64.181.167.174`
- **Usuário SSH**: `ubuntu`
- Chave SSH privada baixada durante a criação — guardar em local seguro
  (não versionar no repo). Conectar com:
  ```bash
  ssh -i caminho/para/ssh-key-2026-09-12.key ubuntu@64.181.167.174
  ```

Também já instalado e testado no servidor: Node 20.20.2, Caddy 2.11.4,
`python3-venv`/`python3-pip`. Firewall do próprio servidor (iptables,
persistido via `netfilter-persistent`) e Security List da Oracle VCN
liberados para as portas necessárias (ver seção 2).

Qualquer outro VPS Ubuntu comum (Hetzner, DigitalOcean, Vultr) funcionaria
igual a partir daqui — só a etapa de provisionamento muda de provedor pra
provedor. Fly.io (região `gru`) é uma alternativa, mas usa um modelo de
deploy diferente (Docker + `fly.toml`, proxy/TLS próprios) — o `Caddyfile`
e os `.service` deste diretório não se aplicam a ele.

## 2. Domínio + HTTPS ✅ Concluído (2026-09-22)

Endereços em produção:

| Endereço | O que serve |
|----------|-------------|
| `https://qualaconduta.com.br` | app do aluno (front + API em `/api`) |
| `https://admin.qualaconduta.com.br` | telas administrativas (Streamlit) |
| `https://conduta.duckdns.org` | redirect 302 para o endereço novo |
| `http://…` e `http://64.181.167.174` | redirect para https |

O domínio é `qualaconduta.com.br` — a pergunta que a prova faz —, comprado na
**Hostinger**, que também hospeda o DNS (`*.dns-parking.com`). O DuckDNS
gratuito serviu enquanto não havia domínio e **continua existindo como
redirect**: link já compartilhado não morre porque a gente mudou de casa.

Registros DNS (todos com TTL 300 — numa migração, TTL curto é o que torna um
erro barato de corrigir):

| Tipo | Nome | Valor | Para quê |
|------|------|-------|----------|
| A | `@` | 64.181.167.174 | o site |
| A | `admin` | 64.181.167.174 | o Streamlit |
| CNAME | `www` | qualaconduta.com.br | veio da Hostinger, o Caddy atende |
| TXT | `@` | `brevo-code:…` | posse do domínio, para o Brevo |
| CNAME | `brevo1._domainkey` | `b1.qualaconduta-com-br.dkim.brevo.com` | DKIM |
| CNAME | `brevo2._domainkey` | `b2.qualaconduta-com-br.dkim.brevo.com` | DKIM |
| TXT | `_dmarc` | `v=DMARC1; p=none; rua=mailto:rua@dmarc.brevo.com` | DMARC |

Os quatro últimos são o que fez o e-mail parar de sair de
`hendrickvk@12189774.brevosend.com`: sem domínio autenticado, o Brevo reescreve
o `From:` de um freemail, porque senão o DMARC de quem recebe reprovaria a
mensagem. Conferido na API do Brevo depois da troca — o envio de 22/09 saiu de
`acesso@qualaconduta.com.br`, os de 19/09 saíram do endereço reescrito.

Portas liberadas (iptables do host + Security List da VCN):

| Porta | Uso | Origem |
|-------|-----|--------|
| 22 | SSH | qualquer IP (protegido pela chave) |
| 80 | redirect para https + validação ACME | qualquer IP |
| 443 | tudo | qualquer IP |

A **8080 foi fechada** no iptables e a regra removida do `/etc/iptables/rules.v4`
(persistida com `netfilter-persistent save`): o Caddy não a usa mais, porque o
admin virou subdomínio com HTTPS. Era ela que precisava ficar restrita a um IP,
porque sem HTTPS a senha do Streamlit trafegava em texto claro — o motivo
deixou de existir. **Sobra uma limpeza no console da Oracle**: a regra de
ingresso da 8080 na Security List continua lá; não expõe nada (nada escuta na
porta), mas é sujeira.

### Trocar de domínio de novo, se um dia precisar

São quatro lugares, e só um exige rebuild:

1. `deploy/Caddyfile` — os blocos de domínio (o Caddy emite o certificado novo
   sozinho; manter o antigo como `redir` custa nada).
2. `.env.production` no servidor — `APP_URL` e `CORS_ORIGENS`.
3. `frontend/.env.production` — `VITE_STREAMLIT_URL`, **o único endereço que o
   bundle embute**; `VITE_API_URL=/api` é relativo de propósito. Exige rebuild
   e envio (§8).
4. Brevo — autenticar o domínio novo e trocar `EMAIL_REMETENTE`.

## 3. Deploy do código ✅ Concluído (2026-09-12)

Migração completa commitada e enviada pro GitHub
(`github.com/Hendrickvk/residencia-med`, commit `bf5798d`), clonada no
servidor em `/var/www/residencia-med`:

```bash
git clone https://github.com/Hendrickvk/residencia-med.git /var/www/residencia-med
cd /var/www/residencia-med
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
```

`frontend/dist/` é o build estático que o Caddy serve (passo 6) — build
confirmado (`✓ built in 7.13s`, 3 arquivos gerados).

### Se o repositório virar privado: chave de deploy

O clone acima é HTTPS **anônimo**, e a atualização é `git pull`: os dois só
funcionam enquanto o repositório é público. Tornar o repositório privado sem
mais nada quebra o `git pull` no servidor com "Authentication failed" /
"repository not found" — não é restrição da Oracle, é o git pedindo credencial
que ninguém configurou ali.

A saída é uma **chave de deploy só de leitura**, gerada no próprio servidor
(nunca uma chave que já exista em outro lugar), pelo usuário que roda o `pull`:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/github-deploy -N ""   # sem passphrase: o pull roda sem interação
cat ~/.ssh/github-deploy.pub                          # colar em Settings > Deploy keys, SEM "Allow write access"
printf 'Host github.com\n  IdentityFile ~/.ssh/github-deploy\n  IdentitiesOnly yes\n' >> ~/.ssh/config
ssh-keyscan github.com >> ~/.ssh/known_hosts          # senão a primeira conexão para, esperando confirmação
cd /var/www/residencia-med
git remote set-url origin git@github.com:Hendrickvk/residencia-med.git
git pull
```

Chave de deploy é por repositório e só de leitura — se o servidor for
comprometido, o atacante lê o código (que ele já teria, tendo a máquina) e não
escreve no repositório. Um token de acesso pessoal também resolveria, mas vale
para a conta inteira, o que é poder demais para um `git pull`.

Como o deploy hoje está parado por falta de SSH, a ordem que evita surpresa é:
tornar privado quando for entrar no servidor de qualquer forma, e configurar a
chave antes do primeiro `git pull` da visita.

## 4. Segredos ✅ Concluído (2026-09-12)

`.env.production` gerado no próprio servidor (nunca passou pelo terminal
local), extraindo `DATABASE_URL` do `.streamlit/secrets.toml` (copiado via
scp) e gerando um `JWT_SECRET_KEY` novo com `secrets.token_urlsafe(32)`.
`COOKIE_SECURE=false` e `CORS_ORIGENS=http://64.181.167.174` (ver seção 2
sobre a decisão de publicar sem domínio por ora).

## 5. Processos (systemd) ✅ Concluído (2026-09-12)

Os `.service` rodam como usuário de sistema dedicado `residenciamed`
(criado com `useradd --system --create-home --shell /usr/sbin/nologin`),
dono de `/var/www/residencia-med`:

```bash
sudo useradd --system --create-home --shell /usr/sbin/nologin residenciamed
sudo chown -R residenciamed:residenciamed /var/www/residencia-med
sudo cp deploy/residencia-api.service deploy/residencia-streamlit.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now residencia-api residencia-streamlit
```

Confirmado `active (running)` para os dois serviços.

## 6. Proxy reverso ✅ Concluído (2026-09-12, HTTPS em 2026-09-22)

```bash
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

O `deploy/Caddyfile` é a configuração de verdade: os dois subdomínios do
DuckDNS com HTTPS automático, a API em `/api` no mesmo host do front (same-origin,
sem CORS entre eles) e o redirect do IP antigo. Desde 2026-09-23 ele também
traz os cabeçalhos de segurança (HSTS, CSP e companhia) e, no admin, um
`import admin-auth.conf` — o `basic_auth`, que **não está no repositório**:
`/etc/caddy/admin-auth.conf`, criado à mão no servidor. Sem esse arquivo o
Caddy recusa a config inteira, então **num servidor novo ele tem que ser
recriado antes do primeiro reload** (`caddy hash-password` gera o hash).
**Permissão: `root:caddy 640`** — o `ExecReload` do unit roda como o usuário
`caddy`, e com um `600` do root o reload morre em `permission denied`
(aconteceu em 23/09). Valide como ele antes de recarregar:
`sudo -u caddy caddy validate --config /etc/caddy/Caddyfile --adapter
caddyfile`. Um reload com config inválida falha e mantém a antiga no ar — é
por isso que o site não saiu do ar naquele erro.

A versão que servia por IP puro ficou em
`/etc/caddy/Caddyfile.antes-do-https` no servidor, para rollback; a de antes
dos cabeçalhos, em `/etc/caddy/Caddyfile.antes-headers`.

**Armadilha encontrada na troca (2026-09-22).** A ideia era aplicar primeiro uma
versão com `auto_https disable_redirects`, para a porta 80 continuar servindo o
site caso a 443 estivesse fechada na Oracle. **Não é isso que essa opção faz**:
ela só remove o redirect, e um site declarado como `host { }` passa a ser servido
apenas em 443 — a porta 80 ficou sem servir nada por dois minutos. Se algum dia
precisar desse escalonamento de verdade, declare um bloco explícito
`http://host { }`. No caso não houve prejuízo, porque a 443 estava aberta desde
sempre: a conexão que não respondia antes era ausência de quem escutasse, e não
firewall. **Como distinguir os dois**, que foi o que levou tempo: porta fechada
por firewall dá timeout (o `-m` do curl estoura), porta sem ninguém escutando dá
recusa rápida — e, em dúvida, `ss -lntp` no servidor responde na hora.

## 7. Usuário de demonstração ✅ Já populado (executado antes desta publicação)

`demo@residenciamed.com` tem ~400 respostas sintéticas espalhadas em 8 semanas
(rodado direto contra o Neon de produção, antes mesmo do servidor existir —
mesmo banco, então nada a refazer).

A senha **não fica escrita aqui nem no `scripts/seed_demo_user.py`**, que agora
a lê de `SENHA_DEMO` no ambiente. Ela estava nos dois lugares, neste
repositório público, e continuava valendo na conta de produção quando a
auditoria de 2026-09-20 a encontrou — qualquer pessoa que lesse o repositório
entrava na plataforma e, autenticada, baixava as 1074 questões com gabarito e
explicação pelo `/praticar/sessao`. Tirar o literal não desfaz a publicação: o
histórico do git é público para sempre, então a senha antiga **tinha de ser
trocada** — foi, em 22/09 — e a nova não volta para cá: ela vive no `.env`
local (gitignorado), em `SENHA_DEMO`, que é de onde o script a lê.

## 8. Checklist final antes de compartilhar qualquer link

Conferido em 2026-09-22, no deploy que trouxe os 60 commits parados desde
12/09 (`bf5798d` → `04ffc5b`):

- [x] `https://qualaconduta.com.br` → 200, com certificado Let's Encrypt
- [x] `http://` → 308 para o https; DuckDNS, `www` e IP antigo → 302
- [x] `https://admin.qualaconduta.com.br` → 200, e o websocket do Streamlit
      negocia `101 Switching Protocols` através do Caddy (é o que costuma
      quebrar em proxy novo)
- [x] `COOKIE_SECURE=true` e `CORS_ORIGENS=https://qualaconduta.com.br`
- [x] Cookie de sessão conferido em produção: `HttpOnly; Secure; SameSite=lax;
      Path=/; Max-Age=43200` — verificado com uma conta descartável
      `@teste.local` criada pela API e removida depois, para não usar
      credencial de ninguém
- [x] `.env.production` com as 9 variáveis (inclusive `APP_URL` e as três do
      Brevo, sem as quais o "esqueci minha senha" só escreve o link no log) e
      permissão **600** — estava 664, com `DATABASE_URL` e `JWT_SECRET_KEY`
      legíveis por qualquer usuário da máquina
- [x] 8080 fechada e a mudança persistida
- [x] Senha do `demo@residenciamed.com` rotacionada em 22/09 (ver seção 7): a
      publicada devolve 401 no site, a nova vive só no `.env` local
- [ ] Login real no navegador, pelo https (o resto foi verificado por curl)
- [x] E-mail saindo de `acesso@qualaconduta.com.br` (conferido na API do Brevo)
- [ ] Limpar a regra de ingresso da 8080 na Security List da Oracle

### O front é construído aqui, não no servidor

A instância tem 954 MB de RAM e **nenhum swap**, com API, Streamlit e Caddy
rodando: sobram ~390 MB, e `npm install` + build ali é convite a OOM. Desde
2026-09-22 o build sai da máquina de desenvolvimento e vai empacotado, com
troca atômica para não haver janela de 404:

```bash
cd frontend && npm run build && cd ..
tar -czf /tmp/dist.tgz -C frontend dist
scp /tmp/dist.tgz residencia-med:/tmp/dist.tgz
ssh residencia-med 'cd /var/www/residencia-med/frontend \
  && sudo -u residenciamed tar -xzf /tmp/dist.tgz --transform "s|^dist|dist.novo|" \
  && sudo -u residenciamed rm -rf dist.antigo \
  && sudo -u residenciamed mv dist dist.antigo && sudo -u residenciamed mv dist.novo dist'
```

`dist.antigo` fica no servidor: rollback é um `mv` de volta. O
`frontend/.env.production` é versionado e usa `VITE_API_URL=/api`, caminho
relativo — por isso o mesmo bundle serve http e https sem rebuild.

O código no servidor pertence ao usuário `residenciamed`, então todo `git` e
todo `pip` ali vão com `sudo -u residenciamed` (rodar como `ubuntu` dá
"dubious ownership").
