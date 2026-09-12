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

## 2. Domínio + DNS — adiado, publicando por IP (decisão de 2026-09-12)

Por ora, sem domínio: acesso direto por `http://64.181.167.174`. Isso
significa **sem HTTPS automático** (Let's Encrypt via Caddy exige um
domínio real pra validar o certificado) — o site fica em HTTP puro
enquanto isso durar.

Portas liberadas (firewall do servidor + Security List da Oracle VCN):

| Porta | Uso | Origem permitida |
|-------|-----|-------------------|
| 22 | SSH | qualquer IP (protegido pela chave privada) |
| 80 | Frontend + API via Caddy | qualquer IP |
| 443 | reservada pra quando houver HTTPS | qualquer IP |
| 8080 | Streamlit (admin) via Caddy | **só o IP `179.216.39.216/32`** |

A porta do admin foi restrita de propósito: sem HTTPS, a senha de login do
Streamlit trafega em texto claro, então não expusemos essa porta pra
qualquer IP da internet — só o IP de quem administra hoje. **Se esse IP
mudar** (troca de rede, provedor dinâmico), a regra da Security List
precisa ser atualizada (Oracle Console → Networking → Virtual Cloud
Networks → `residencia-med-vcn` → Security → `Default Security List for
residencia-med-vcn` → editar a regra da porta 8080), senão o admin fica
inacessível. Alternativa mais robusta: acessar via túnel SSH
(`ssh -L 8501:localhost:8501 ubuntu@64.181.167.174` e abrir
`http://localhost:8501`) em vez de depender de IP fixo.

Quando houver um domínio real, trocar `deploy/Caddyfile` pela versão em
`deploy/Caddyfile.com-dominio.example` (HTTPS automático, Streamlit em
subdomínio em vez de porta), e então dois registros DNS tipo A:

```
SEUDOMINIO.com        → 64.181.167.174
admin.SEUDOMINIO.com  → 64.181.167.174
```

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

## 6. Proxy reverso ✅ Concluído (2026-09-12)

```bash
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Sem domínio ainda, esse `Caddyfile` serve por IP puro em HTTP (porta 80
pro frontend+API, porta 8080 pro Streamlit). Quando houver domínio, usar
`deploy/Caddyfile.com-dominio.example` no lugar (HTTPS automático via
Let's Encrypt, só editar as duas ocorrências de `SEUDOMINIO.com`).

## 7. Usuário de demonstração ✅ Já populado (executado antes desta publicação)

`demo@residenciamed.com` / `ResidenciaDemo2026!` já tem ~400 respostas
sintéticas espalhadas em 8 semanas (rodado direto contra o Neon de
produção, antes mesmo do servidor existir — mesmo banco, então nada a
refazer). Confirmado via login real na API publicada: ofensiva de 36 dias,
458 questões, 1646 materiais.

## 8. Checklist final antes de compartilhar qualquer link

- [x] `COOKIE_SECURE=false` em `.env.production` (sem HTTPS ainda — trocar
      pra `true` só depois de migrar pro `Caddyfile.com-dominio.example`)
- [x] Usuário de demonstração populado (passo 7)
- [x] Login funciona em `http://64.181.167.174` (testado via curl:
      `POST /api/auth/login` → 200, `GET /api/me` autenticado → 200)
- [x] `http://64.181.167.174:8080` abre o Streamlit (só do IP liberado —
      ver seção 2) — testado, HTTP 200
- [x] Testar o fluxo de Praticar de ponta a ponta no navegador (não só
      curl) — login real no Chrome, painel com dados reais, uma questão
      respondida com feedback instantâneo e explicação exibidos sem
      round-trip; Streamlit também confirmado carregando via WebSocket
      através do proxy Caddy

Quando migrar pra domínio + HTTPS, revisitar esta checklist: `COOKIE_SECURE`
volta a `true`, `CORS_ORIGENS` e `VITE_STREAMLIT_URL` voltam a usar o
domínio real, e a porta 8080 pode ser fechada na Security List (Streamlit
passa a viver em `admin.SEUDOMINIO.com` via HTTPS).
