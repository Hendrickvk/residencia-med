// `alvo` é a altura que a barra assume sob o cursor, escrita como fator de
// escala literal porque o Tailwind só gera a classe que encontra escrita por
// extenso. O meio (12px) é o próprio espelho e não se mexe.
const BARRAS = [
  { altura: 20, classe: "bg-t1", alvo: "group-hover/marca:scale-y-[0.2]" },
  { altura: 16, classe: "bg-t2", alvo: "group-hover/marca:scale-y-[0.5]" },
  { altura: 12, classe: "bg-t3", alvo: "" },
  { altura: 8, classe: "bg-t4", alvo: "group-hover/marca:scale-y-[2]" },
  { altura: 4, classe: "bg-t5", alvo: "group-hover/marca:scale-y-[5]" },
];

// Símbolo da marca (DESIGN_TRIAGEM.md §3): as cinco barras da escala de
// triagem, do nível mais grave ao mais leve.
//
// Sob o cursor a escala se inverte, uma barra depois da outra, e volta ao sair:
// o vermelho encolhe e o verde cresce, que é o caminho que a plataforma existe
// para fazer o aluno percorrer. É `transform`, não altura, para não recalcular
// layout dentro da barra superior; a altura do conjunto não muda, então nada em
// volta se desloca. Quem pediu menos movimento não vê nada: a regra global de
// `prefers-reduced-motion` no theme.css zera a transição.
export function Simbolo({ escala = 1 }: { escala?: number }) {
  return (
    <span className="flex shrink-0 items-end" style={{ gap: 2 * escala, height: 20 * escala }} aria-hidden="true">
      {BARRAS.map((b, i) => (
        <span
          key={b.classe}
          className={`block origin-bottom rounded-[1px] transition-transform duration-desliza ease-suave ${b.classe} ${b.alvo}`}
          style={{ width: 4 * escala, height: b.altura * escala, transitionDelay: `${i * 45}ms` }}
        />
      ))}
    </span>
  );
}

export function Marca({ grande = false }: { grande?: boolean }) {
  return (
    <span className={`flex items-center ${grande ? "gap-4" : "gap-2.5"}`}>
      <Simbolo escala={grande ? 2 : 1} />
      {/* Em tela estreita o símbolo sozinho sustenta a marca: a barra da sessão
          precisa da largura para manter a saída (Encerrar/Finalizar/Sair)
          visível, que o DESIGN_TRIAGEM.md §5 exige em toda sessão. */}
      <span className={grande ? "marca-texto text-[44px]" : "marca-texto hidden sm:inline"}>Conduta</span>
    </span>
  );
}
