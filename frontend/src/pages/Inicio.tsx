import { ArrowRight, CircleCheck, Clock, RotateCcw } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { Simbolo } from "../components/shell/Marca";
import { useMe } from "../lib/auth";
import { BOTAO_PRIMARIO, BOTAO_SECUNDARIO } from "../lib/estilos";
import { formatarPctBR } from "../lib/format";
import { atraso } from "../lib/movimento";
import { BANCAS_OFICIAIS } from "../lib/simulados";
import { CLASSES_NIVEL, NIVEIS, nivelTriagem } from "../lib/triagem";

// Página pública (`/`): o que quem recebeu o link vê antes de ter conta.
// Decisões do usuário em 26/09: não prometer preço ("Criar conta", nunca
// "grátis"), abrir com as provas oficiais comentadas, quatro blocos — promessa
// com o painel, como funciona, as provas, o convite — e **nenhuma contagem**
// ("13 provas", "1.163 questões"): perto dos concorrentes, número pequeno
// diminui a plataforma; o que vende é a qualidade e o peso das bancas.
// Quem já tem sessão vai direto ao Painel, e o app instalado abre em /painel.

const TITULO = "Conduta — as provas oficiais do Revalida e do ENAMED, comentadas";

export default function Inicio() {
  const { data: me, isLoading } = useMe();
  // Quem tem sessão costuma receber o /me em poucos décimos e vai ao Painel sem
  // ver esta página piscar; se o /me demorar (API fora, rede lenta), a página
  // aparece mesmo assim — ela é pública e não depende dele.
  const [esperou, setEsperou] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setEsperou(true), 800);
    return () => clearTimeout(t);
  }, []);
  useEffect(() => {
    const antes = document.title;
    document.title = TITULO;
    return () => {
      document.title = antes;
    };
  }, []);

  if (me) return <Navigate to="/painel" replace />;
  if (isLoading && !esperou) return <div className="min-h-screen bg-ground" />;
  return <Pagina />;
}

function Pagina() {
  return (
    <div className="min-h-screen bg-ground text-ink">
      <header className="mx-auto flex h-16 max-w-[1200px] items-center justify-between px-4 md:px-10">
        <span className="flex items-center gap-2.5">
          <Simbolo />
          <span className="marca-texto">Conduta</span>
        </span>
        <nav className="flex items-center gap-1.5 sm:gap-2" aria-label="Acesso">
          <Link to="/login" className="rounded-btn px-3 py-2 text-[15px] font-medium text-ink-2 transition-colors duration-hover ease-brand hover:text-ink">
            Entrar
          </Link>
          <Link to="/login?criar" className={`${BOTAO_PRIMARIO} h-10 px-4`}>
            Criar conta
          </Link>
        </nav>
      </header>

      <main>
        {/* Promessa + o painel de verdade (com dados de exemplo). */}
        <section className="mx-auto grid max-w-[1200px] items-center gap-12 px-4 pb-16 pt-8 md:px-10 md:pb-24 md:pt-14 lg:grid-cols-[minmax(0,1fr)_minmax(0,520px)] lg:gap-16">
          <div className="animate-entrar">
            <h1 className="text-[40px] font-extrabold leading-[1.02] tracking-[-0.035em] [text-wrap:balance] md:text-[56px] lg:text-[64px]">
              As provas oficiais do Revalida e do ENAMED, comentadas.
            </h1>
            <p className="mt-5 max-w-[34rem] text-[17px] leading-[1.55] text-ink-2 md:text-[19px]">
              Cada questão com a discussão de todas as alternativas, e um painel que mostra onde você está perdendo
              pontos e por onde começar.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/login?criar" className={BOTAO_PRIMARIO}>
                Criar conta
                <ArrowRight size={18} strokeWidth={2} aria-hidden="true" />
              </Link>
              <Link to="/login" className={BOTAO_SECUNDARIO}>
                Já tenho conta
              </Link>
            </div>
            {/* As bancas como selo, sem contagem nenhuma. */}
            <ul className="mt-9 flex flex-wrap gap-x-6 gap-y-2 text-[13px] font-bold uppercase tracking-[0.1em] text-muted [font-stretch:80%]" aria-label="Bancas">
              {BANCAS_OFICIAIS.map((b) => (
                <li key={b.nome}>{b.nome}</li>
              ))}
            </ul>
          </div>
          <PainelExemplo />
        </section>

        <Bloco
          titulo="Cada caso, discutido alternativa por alternativa."
          texto="Você responde, vê na hora qual era a conduta e lê por que cada alternativa está certa ou errada — o raciocínio, não só o gabarito. Explicações próprias, escritas para cada questão e revisadas uma a uma."
          visual={<CasoExemplo />}
        />
        <Bloco
          invertido
          titulo="Revisão espaçada, no ritmo da sua memória."
          texto="Todo caso que você responde entra numa fila que volta no dia certo: dez minutos depois de um erro, e cada vez mais espaçado quando você lembra. Os cartões que você cria seguem o mesmo ritmo."
          visual={<RevisaoExemplo />}
        />
        <Bloco
          titulo="Simulados no tempo da prova."
          texto="Refaça um caderno inteiro, na ordem original e com 3 minutos por questão, como no dia. No fim, a nota, o tempo gasto em cada questão e os temas que pedem revisão."
          visual={<SimuladoExemplo />}
        />

        <section className="border-t border-line">
          <div className="mx-auto max-w-[1200px] px-4 py-16 md:px-10 md:py-24">
            <h2 className="text-[30px] font-extrabold leading-[1.08] tracking-[-0.03em] [text-wrap:balance] md:text-[38px]">
              Provas oficiais, revisadas questão por questão.
            </h2>
            <p className="mt-4 max-w-[36rem] text-[17px] leading-[1.6] text-ink-2">
              Os cadernos inteiros do Revalida e do ENAMED, na ordem em que caíram, e provas de residência de São
              Paulo. Cada explicação passou por revisão, e as questões anuladas ficaram de fora.
            </p>
            {/* Quatro colunas só a partir de 1024 px: antes disso, "UNICAMP" em 32 px passava da borda do card. */}
            <ul className="mt-10 grid grid-cols-2 gap-3 lg:grid-cols-4">
              {BANCAS_OFICIAIS.map((b) => (
                <li key={b.nome} className="rounded-caso border border-line bg-surface px-5 py-6">
                  <span className="block text-[22px] font-extrabold leading-none tracking-[-0.03em] [font-stretch:110%] sm:text-[32px]">
                    {b.nome}
                  </span>
                  <span className="mt-2 block text-apoio text-muted">{b.orgao}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="border-t border-line bg-surface">
          <div className="mx-auto flex max-w-[1200px] flex-col items-start gap-6 px-4 py-16 md:px-10 md:py-24">
            <h2 className="text-[34px] font-extrabold leading-[1.05] tracking-[-0.035em] md:text-[48px]">
              Descubra onde você perde pontos.
            </h2>
            <p className="max-w-[34rem] text-[17px] leading-[1.6] text-ink-2">
              Crie sua conta, responda os primeiros casos e o painel começa a apontar por onde seguir.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link to="/login?criar" className={BOTAO_PRIMARIO}>
                Criar conta
                <ArrowRight size={18} strokeWidth={2} aria-hidden="true" />
              </Link>
              <Link to="/login" className={BOTAO_SECUNDARIO}>
                Entrar
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="mx-auto flex max-w-[1200px] flex-col gap-3 px-4 py-10 text-apoio text-muted md:flex-row md:items-center md:justify-between md:px-10">
        <span className="flex items-center gap-2.5 text-ink">
          <Simbolo />
          <span className="marca-texto text-[17px]">Conduta</span>
        </span>
        <p className="max-w-[40rem]">
          As questões são das provas oficiais publicadas pelo INEP, pela FUVEST e pela COMVEST. As explicações são
          próprias do Conduta.
        </p>
      </footer>
    </div>
  );
}

function Bloco({ titulo, texto, visual, invertido = false }: { titulo: string; texto: string; visual: React.ReactNode; invertido?: boolean }) {
  return (
    <section className="border-t border-line">
      <div className="mx-auto grid max-w-[1200px] items-center gap-10 px-4 py-16 md:px-10 md:py-20 lg:grid-cols-2 lg:gap-16">
        <div className={invertido ? "lg:order-2" : ""}>
          <h2 className="text-[30px] font-extrabold leading-[1.08] tracking-[-0.03em] [text-wrap:balance] md:text-[38px]">{titulo}</h2>
          <p className="mt-4 max-w-[32rem] text-[17px] leading-[1.6] text-ink-2">{texto}</p>
        </div>
        <div className={invertido ? "lg:order-1" : ""}>{visual}</div>
      </div>
    </section>
  );
}

// Moldura das demonstrações: o mesmo cartão do app, com a etiqueta que diz o que
// é real e o que é exemplo. O conteúdo é ilustração (aria-hidden), e a legenda
// para leitor de tela está no figcaption.
function Moldura({ etiqueta, legenda, children }: { etiqueta: string; legenda: string; children: React.ReactNode }) {
  return (
    <figure className="rounded-caso border border-line bg-surface p-5 md:p-6">
      <figcaption className="sr-only">{legenda}</figcaption>
      <div aria-hidden="true">
        <div className="mb-4 flex justify-end">
          <span className="rounded-etq border border-line px-1.5 py-0.5 text-[11px] font-semibold text-muted">{etiqueta}</span>
        </div>
        {children}
      </div>
    </figure>
  );
}

// As cinco áreas em cinco níveis: mostra a escala inteira de uma vez.
const AREAS_EXEMPLO = [
  { area: "Clínica Médica", pct: 32.6 },
  { area: "Ginecologia e Obstetrícia", pct: 46.0 },
  { area: "Pediatria", pct: 58.3 },
  { area: "Cirurgia", pct: 64.3 },
  { area: "Medicina Preventiva e Social", pct: 86.2 },
];

function PainelExemplo() {
  return (
    <Moldura etiqueta="Exemplo" legenda="Exemplo do painel do Conduta: as cinco grandes áreas classificadas por nível de triagem, da emergência ao não urgente.">
      <p className="text-[24px] font-extrabold leading-[1.1] tracking-[-0.02em] md:text-[28px]">Clínica Médica é a sua maior lacuna.</p>
      <p className="mt-2 text-apoio text-muted">128 acertos em 222 questões · prova em 71 dias</p>
      <ul className="mt-6 flex flex-col gap-4">
        {AREAS_EXEMPLO.map(({ area, pct }, i) => {
          const nivel = nivelTriagem(pct);
          const c = CLASSES_NIVEL[nivel];
          return (
            <li key={area} className="grid animate-entrar grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-x-3 gap-y-2" style={atraso(i, 70)}>
              <span className={`rotulo rounded-etq px-1.5 py-1 text-[11px] ${c.cheio} ${c.texto}`}>{NIVEIS[nivel - 1].nome}</span>
              {/* Quebra em vez de cortar: no celular "Ginecologia e Obstetrícia"
                  virava "Ginecologia e Ob…", justo o que a demonstração mostra. */}
              <span className="text-[15px] font-semibold leading-tight">{area}</span>
              <span className="text-[20px] font-extrabold tabular-nums tracking-[-0.02em] [font-stretch:110%]">{formatarPctBR(pct)}%</span>
              <span className="col-span-3 h-1 overflow-hidden rounded-pill bg-line-soft">
                <span
                  className={`block h-full origin-left animate-crescer rounded-pill ${c.cheio}`}
                  style={{ width: `${pct}%`, animationDelay: `${160 + i * 90}ms` }}
                />
              </span>
            </li>
          );
        })}
      </ul>
    </Moldura>
  );
}

// Questão real do banco (Revalida 2022/1, questão 46) com o começo da discussão
// que está no banco. Se a explicação for reescrita, atualizar aqui.
const ALTERNATIVAS_CASO = [
  { letra: "A", texto: "pielonefrite grave." },
  { letra: "B", texto: "sepse de foco urinário." },
  { letra: "C", texto: "bacteriúria assintomática.", marcada: true },
  { letra: "D", texto: "infecção de trato urinário não complicada.", correta: true },
];

function CasoExemplo() {
  return (
    <Moldura etiqueta="Questão real · Revalida 2022/1" legenda="Exemplo de caso comentado: uma questão do Revalida 2022/1 com a alternativa marcada, a correta e o começo da discussão.">
      <div className="flex items-center gap-2 text-apoio text-muted">
        <CircleCheck size={16} strokeWidth={2} className="text-t4" />
        Prova oficial · Revalida 2022/1 · questão 46
      </div>
      <p className="mt-3 text-[15.5px] leading-[1.7] text-ink [font-stretch:104%]">
        Uma paciente com 30 anos de idade, sem comorbidades, compareceu à Unidade Básica de Saúde com queixas de
        disúria, tenesmo vesical, polaciúria e ardência miccional há 2 dias. […] Diante desses dados, a principal
        hipótese diagnóstica é
      </p>
      <ul className="mt-4 flex flex-col gap-2">
        {ALTERNATIVAS_CASO.map((a) => {
          const estilo = a.correta
            ? "border-2 border-t4 bg-t4-soft"
            : a.marcada
              ? "border-2 border-t1 bg-t1-soft"
              : "border border-line text-muted";
          const letra = a.correta ? "bg-t4 text-t4-on" : a.marcada ? "bg-t1 text-t1-on" : "bg-ground";
          return (
            <li key={a.letra} className={`grid grid-cols-[28px_minmax(0,1fr)] items-center gap-3 rounded-card px-3 py-2.5 ${estilo}`}>
              <span className={`flex h-7 w-7 items-center justify-center rounded-col text-[13px] font-bold ${letra}`}>{a.letra}</span>
              <span className="text-[14.5px]">
                {a.texto}
                {(a.correta || a.marcada) && (
                  <span className={`rotulo ml-2 inline-block rounded-etq px-1.5 py-0.5 align-middle text-[10.5px] ${a.correta ? "bg-t4 text-t4-on" : "bg-t1 text-t1-on"}`}>
                    {a.correta ? "Conduta correta" : "Sua conduta"}
                  </span>
                )}
              </span>
            </li>
          );
        })}
      </ul>
      <p className="mt-5 border-t border-line-soft pt-4 text-[15px] leading-[1.7] text-ink-2 [font-stretch:104%]">
        Disúria, polaciúria, ardência e tenesmo vesical de início recente, sem febre nem dor lombar, em uma mulher
        jovem, não gestante, sem comorbidades e sem alteração conhecida do trato urinário, é cistite — infecção do
        trato urinário não complicada, a alternativa D. […]
      </p>
    </Moldura>
  );
}

// Prazos ilustrativos: no app eles vêm do SM-2 de cada caso (`prever_prazos`).
const NOTAS_EXEMPLO = [
  { rotulo: "Com esforço", prazo: "volta em 2 dias", cor: "bg-t2" },
  { rotulo: "Lembrei", prazo: "volta em 6 dias", cor: "bg-t4" },
  { rotulo: "Fácil", prazo: "volta em 11 dias", cor: "bg-t5" },
];

function RevisaoExemplo() {
  return (
    <Moldura etiqueta="Exemplo" legenda="Exemplo da revisão espaçada: depois de acertar, a pessoa diz como foi lembrar e cada resposta agenda a próxima revisão.">
      <div className="flex items-baseline justify-between gap-4">
        <span className="text-[15px] font-semibold">Revisão espaçada</span>
        <span className="text-apoio text-muted">
          <span className="tabular-nums">20</span> restantes · ~32 min
        </span>
      </div>
      <p className="mt-6 text-[20px] font-extrabold tracking-[-0.02em]">Como foi lembrar?</p>
      <div className="mt-4 flex flex-col gap-2 sm:grid sm:grid-cols-3">
        {NOTAS_EXEMPLO.map((n) => (
          <span key={n.rotulo} className="flex flex-col gap-1 rounded-btn border border-line px-3 py-3">
            <span className="flex items-center gap-2 text-[15px] font-semibold">
              <span className={`h-2.5 w-2.5 rounded-[2px] ${n.cor}`} />
              {n.rotulo}
            </span>
            <span className="text-apoio text-muted">{n.prazo}</span>
          </span>
        ))}
      </div>
      <p className="mt-5 flex items-center gap-2 border-t border-line-soft pt-4 text-apoio text-muted">
        <RotateCcw size={16} strokeWidth={2} />
        Errou? O caso volta na sua revisão em 10 minutos.
      </p>
    </Moldura>
  );
}

// 97 questões, como o Revalida 2025/1: respondidas até a atual, algumas
// marcadas para voltar, o resto em branco.
const TOTAL_QUESTOES = 97;
const ATUAL = 37;
const MARCADAS = new Set([9, 22, 31]);

function SimuladoExemplo() {
  return (
    <Moldura etiqueta="Exemplo" legenda="Exemplo de simulado: a prova oficial inteira no tempo da prova, com a grade de questões respondidas, marcadas e em branco.">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <span className="text-[15px] font-semibold">Revalida 2025/1 · questão {ATUAL} de {TOTAL_QUESTOES}</span>
        <span className="flex items-center gap-1.5 text-[22px] font-extrabold tabular-nums tracking-[-0.02em] [font-stretch:80%]">
          <Clock size={18} strokeWidth={2} className="text-muted" />
          3:12:08
        </span>
      </div>
      <div className="mt-5 grid grid-cols-[repeat(auto-fill,minmax(22px,1fr))] gap-1.5">
        {Array.from({ length: TOTAL_QUESTOES }, (_, i) => {
          const n = i + 1;
          const respondida = n < ATUAL;
          const classe =
            n === ATUAL ? "border-2 border-ink" : respondida ? "bg-ink" : "border border-line";
          return (
            <span key={n} className={`relative aspect-square rounded-[3px] ${classe}`}>
              {MARCADAS.has(n) && <span className="absolute right-0 top-0 h-1.5 w-1.5 rounded-bl-[2px] bg-t3" />}
            </span>
          );
        })}
      </div>
      <p className="mt-5 border-t border-line-soft pt-4 text-apoio text-muted">
        3 minutos por questão · a correção aparece só no final
      </p>
    </Moldura>
  );
}
