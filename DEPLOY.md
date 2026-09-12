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

## 3. Deploy do código

```bash
git clone <url-do-repo> /var/www/residencia-med
cd /var/www/residencia-med
python -m venv .venv
.venv/bin/pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
```

`frontend/dist/` é o build estático que o Caddy serve (passo 6).

## 4. Segredos

```bash
cp deploy/.env.production.example .env.production
# editar .env.production: DATABASE_URL (mesma do .streamlit/secrets.toml),
# JWT_SECRET_KEY (gerar com o comando comentado dentro do arquivo),
# ADMIN_EMAILS, CORS_ORIGENS
```

O Streamlit continua lendo `.streamlit/secrets.toml` como sempre — esse
arquivo (não versionado) precisa existir no servidor também, com a mesma
`DATABASE_URL`.

## 5. Processos (systemd)

```bash
sudo cp deploy/residencia-api.service deploy/residencia-streamlit.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now residencia-api residencia-streamlit
sudo systemctl status residencia-api residencia-streamlit   # conferir que subiram
```

## 6. Proxy reverso

```bash
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Sem domínio ainda, esse `Caddyfile` serve por IP puro em HTTP (porta 80
pro frontend+API, porta 8080 pro Streamlit) — sem edição necessária, já
aponta pros paths certos. Quando houver domínio, usar
`deploy/Caddyfile.com-dominio.example` no lugar (HTTPS automático via
Let's Encrypt, só editar as duas ocorrências de `SEUDOMINIO.com`).

## 7. Usuário de demonstração

```bash
.venv/bin/python scripts/seed_demo_user.py
```

Semeia ~400 respostas reais (questões existentes, histórico sintético)
espalhadas em 8 semanas com desempenho desigual entre áreas — pra o Painel
não parecer amador com uma conta vazia. Credenciais impressas no final do
script (`demo@residenciamed.com` / senha definida em
`scripts/seed_demo_user.py`). Rodar uma vez só.

## 8. Checklist final antes de compartilhar qualquer link

- [ ] `COOKIE_SECURE=false` em `.env.production` (sem HTTPS ainda — trocar
      pra `true` só depois de migrar pro `Caddyfile.com-dominio.example`)
- [ ] Usuário de demonstração populado (passo 7)
- [ ] Login funciona em `http://64.181.167.174`
- [ ] `http://64.181.167.174:8080` abre o Streamlit (só do IP liberado —
      ver seção 2)
- [ ] Testar o fluxo de Praticar de ponta a ponta no IP real, não só em
      `localhost`

Quando migrar pra domínio + HTTPS, revisitar esta checklist: `COOKIE_SECURE`
volta a `true`, `CORS_ORIGENS` e `VITE_STREAMLIT_URL` voltam a usar o
domínio real, e a porta 8080 pode ser fechada na Security List (Streamlit
passa a viver em `admin.SEUDOMINIO.com` via HTTPS).
