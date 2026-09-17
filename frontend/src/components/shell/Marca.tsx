const BARRAS = [
  { altura: 20, classe: "bg-t1" },
  { altura: 16, classe: "bg-t2" },
  { altura: 12, classe: "bg-t3" },
  { altura: 8, classe: "bg-t4" },
  { altura: 4, classe: "bg-t5" },
];

// Símbolo da marca (DESIGN_TRIAGEM.md §3): as cinco barras da escala de
// triagem, do nível mais grave ao mais leve.
export function Simbolo({ escala = 1 }: { escala?: number }) {
  return (
    <span className="flex shrink-0 items-end" style={{ gap: 2 * escala, height: 20 * escala }} aria-hidden="true">
      {BARRAS.map((b) => (
        <span key={b.classe} className={`block rounded-[1px] ${b.classe}`} style={{ width: 4 * escala, height: b.altura * escala }} />
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
