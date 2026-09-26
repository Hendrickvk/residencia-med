"""
O e-mail com a cara da plataforma (DESIGN_TRIAGEM.md).

E-mail não é página: o Gmail corta o `<style>` do `<head>` em parte dos
clientes, o Outlook desenha com o motor do Word (sem flexbox, sem `border-radius`
em `<div>`, sem `padding` confiável em `<a>`) e ninguém carrega fonte do Google.
Por isso aqui é tudo **tabela e estilo inline**, o botão é uma célula pintada
com o texto dentro, e a Archivo entra como primeira opção de uma pilha que
termina em Arial — quem tiver a fonte vê a marca certa, quem não tiver lê
igual.

O que o sistema visual manda e sobrevive nesse meio: papel `--ground`, cartão
`--surface` com borda de 1px e nada de sombra, tinta no botão primário (preto,
não colorido — §1), raios de no máximo 8px, e o símbolo da marca em cinco
barras t1→t5, que é o único lugar onde a escala de triagem aparece sem
significar um nível (§3).

Sem tema escuro: cliente de e-mail inverte cor sozinho e de forma imprevisível,
então a mensagem se declara clara (`color-scheme`) e para de pé.
"""

# Tokens do tema claro (DESIGN_TRIAGEM.md §3), copiados porque o CSS da
# aplicação não chega aqui. Se os tokens mudarem lá, mudam aqui à mão — é a
# troca consciente por não ter build de e-mail.
GROUND = "#F2F3EF"
SURFACE = "#FFFFFF"
INK = "#111315"
INK_2 = "#3E4247"
MUTED = "#6C7178"
LINE = "#DFE1DC"
ON_INK = "#FFFFFF"
TRIAGEM = ("#CF3328", "#F17C1B", "#EDBB1C", "#23804A", "#2D6CD2")
ALTURAS = (20, 16, 12, 8, 4)

FONTE = "'Archivo', 'Helvetica Neue', Helvetica, Arial, sans-serif"


def _simbolo() -> str:
    """As cinco barras da triagem, alinhadas pela base como na barra superior
    do app. Cada barra é uma célula de 4px de largura com altura própria; o
    espaçamento de 2px sai de uma célula vazia entre elas, porque `gap` não
    existe em tabela."""
    celulas = []
    for i, (cor, altura) in enumerate(zip(TRIAGEM, ALTURAS)):
        if i:
            celulas.append('<td width="2" style="width:2px;font-size:0;line-height:0;">&nbsp;</td>')
        celulas.append(
            f'<td width="4" valign="bottom" style="width:4px;font-size:0;line-height:0;">'
            f'<div style="width:4px;height:{altura}px;background-color:{cor};font-size:0;line-height:0;">&nbsp;</div>'
            f"</td>"
        )
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">'
        f'<tr valign="bottom">{"".join(celulas)}</tr></table>'
    )


def _paragrafo(texto: str, cor: str = INK_2) -> str:
    return (
        f'<p style="margin:0 0 14px 0;font-family:{FONTE};font-size:15.5px;'
        f'line-height:1.55;color:{cor};">{texto}</p>'
    )


def montar_html(*, titulo: str, paragrafos: list[str], botao_texto: str,
                botao_url: str, rodape: str) -> str:
    """Monta a mensagem inteira. `paragrafos` já vem com o texto pronto — nada
    aqui escapa HTML, então quem chama não pode passar conteúdo de usuário."""
    corpo = "".join(_paragrafo(p) for p in paragrafos)
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<title>{titulo}</title>
</head>
<body style="margin:0;padding:0;background-color:{GROUND};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
       style="border-collapse:collapse;background-color:{GROUND};">
<tr>
<td align="center" style="padding:32px 16px;">

  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
         style="border-collapse:collapse;max-width:520px;width:100%;">

    <!-- Marca: símbolo + nome, como na barra superior. Parada, sem link:
         no e-mail o hover não existe e promessa de clique aqui seria falsa. -->
    <tr><td style="padding:0 0 24px 4px;">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">
        <tr>
          <td valign="bottom">{_simbolo()}</td>
          <td valign="bottom" style="padding-left:9px;font-family:{FONTE};font-size:21px;
              font-weight:800;letter-spacing:-0.03em;color:{INK};line-height:20px;">Conduta</td>
        </tr>
      </table>
    </td></tr>

    <tr><td style="background-color:{SURFACE};border:1px solid {LINE};border-radius:8px;padding:28px 26px;">
      <h1 style="margin:0 0 16px 0;font-family:{FONTE};font-size:24px;line-height:1.2;
          font-weight:800;letter-spacing:-0.02em;color:{INK};">{titulo}</h1>
      {corpo}

      <!-- Botão "à prova de Outlook": célula pintada, texto dentro. Tinta, e
           não cor de marca (DESIGN_TRIAGEM.md §1). -->
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;margin:22px 0 6px 0;">
        <tr><td bgcolor="{INK}" style="border-radius:5px;">
          <a href="{botao_url}" style="display:inline-block;padding:13px 22px;font-family:{FONTE};
             font-size:15px;font-weight:700;line-height:1;color:{ON_INK};text-decoration:none;
             border-radius:5px;">{botao_texto}</a>
        </td></tr>
      </table>

      <!-- Cliente que bloqueia o botão, ou quem copia o link para outro
           navegador: o endereço em texto, quebrando em qualquer largura. -->
      <p style="margin:14px 0 0 0;font-family:{FONTE};font-size:13.5px;line-height:1.45;color:{MUTED};">
        Se o botão não funcionar, copie este endereço:<br>
        <span style="color:{INK_2};word-break:break-all;">{botao_url}</span>
      </p>
    </td></tr>

    <tr><td style="padding:18px 4px 0 4px;font-family:{FONTE};font-size:13.5px;
        line-height:1.45;color:{MUTED};">{rodape}</td></tr>

  </table>

</td>
</tr>
</table>
</body>
</html>"""


def _duracao(casos: int, segundos_por_caso: float) -> str:
    """A mesma conta do `estimarDuracao` do front (lib/prazo.ts)."""
    minutos = max(1, round(casos * segundos_por_caso / 60))
    if minutos < 60:
        return f"uns {minutos} minutos"
    horas, resto = divmod(minutos, 60)
    return f"cerca de {horas} h {resto:02d} min" if resto else f"cerca de {horas} h"


def lembrete_revisao(*, casos: int, cartoes: int, segundos_por_caso: float, app_url: str):
    """O lembrete de revisão, que a aluna liga no Perfil (é opcional, desligado
    por padrão). Devolve (assunto, texto, html). Só números entram aqui — nada
    escrito por alguém —, porque `montar_html` não escapa."""
    partes = []
    if casos:
        partes.append(f"{casos} caso{'s' if casos != 1 else ''}")
    if cartoes:
        partes.append(f"{cartoes} cart{'ões' if cartoes != 1 else 'ão'}")
    oque = " e ".join(partes)
    assunto = f"{oque} para revisar hoje"
    paragrafos = [f"Hoje há {oque} para revisar."]
    if casos:
        paragrafos.append(f"No seu ritmo, os casos levam {_duracao(casos, segundos_por_caso)}.")
    # Só cartão vencido: o botão vai direto para o estudo dos baralhos.
    destino = f"{app_url}/revisao" if casos else f"{app_url}/baralhos?estudar=tudo"
    # O link de desligar abre o Perfil já no interruptor (a página rola até
    # `#lembretes`); deslogada, ela passa pelo login e volta para lá.
    desligar = f"{app_url}/perfil#lembretes"
    rodape = "Você recebe este e-mail porque ligou o lembrete de revisão no seu Perfil."
    rodape_html = (
        f'{rodape} <a href="{desligar}" style="color:{MUTED};text-decoration:underline;">'
        "Desligar o lembrete</a>."
    )
    texto = "\n\n".join([*paragrafos, f"Revisar agora: {destino}", f"{rodape} Para desligar: {desligar}"])
    html = montar_html(
        titulo="Revisões de hoje", paragrafos=paragrafos, botao_texto="Revisar agora",
        botao_url=destino, rodape=rodape_html,
    )
    return assunto, texto, html


def relatorio_diario(*, dia, resumo: dict, suspeitas: list, erros: list, admin_url: str):
    """O dia anterior para quem administra (ADMIN_EMAILS). Devolve (assunto,
    texto, html). As mensagens de erro vêm do navegador das alunas: no HTML
    entram escapadas, porque `montar_html` não escapa nada."""
    import html as _html

    data = dia.strftime("%d/%m")
    r = resumo
    assunto = (f"Conduta, {data}: {r['estudaram']} estudaram, {r['contas_novas']} conta(s) nova(s), "
               f"{r['erros_app']} erro(s) do app")
    base = [
        f"Em {data}, {r['estudaram']} conta(s) estudaram: {r['respostas']} resposta(s), "
        f"{r['revisoes']} caso(s) revisado(s) e {r['cartoes']} cartão(ões) avaliado(s).",
        f"Contas novas: {r['contas_novas']}.",
    ]
    if suspeitas:
        ids = ", ".join(str(s["id"]) for s in suspeitas[:10])
        base.append(f"{len(suspeitas)} questão(ões) suspeita(s) (acerto muito baixo, ou a maioria na mesma "
                    f"errada): {ids}.")
    if erros:
        cru = "; ".join(f"{e['vezes']}× {e['mensagem'][:120]}" for e in erros[:5])
        esc = "; ".join(f"{e['vezes']}× {_html.escape(e['mensagem'][:120])}" for e in erros[:5])
        linha_texto, linha_html = f"Erros do app nas últimas 24 h: {cru}.", f"Erros do app nas últimas 24 h: {esc}."
    else:
        linha_texto = linha_html = "Nenhum erro do app nas últimas 24 h."
    rodape = "Relatório automático da rotina diária (scripts/rotina_diaria.py), para quem está em ADMIN_EMAILS."
    texto = "\n\n".join([*base, linha_texto, f"Uso da plataforma: {admin_url}", rodape])
    html = montar_html(
        titulo=f"O dia {data} na Conduta", paragrafos=[*base, linha_html],
        botao_texto="Abrir o uso da plataforma", botao_url=admin_url, rodape=rodape,
    )
    return assunto, texto, html
