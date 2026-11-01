import { blocosDoEnunciado } from "../lib/enunciado";

// Tabela de verdade, com rolagem própria: num celular de 320 px, três colunas de exame
// não podem empurrar a página para o lado.
export function TextoEnunciado({ texto }: { texto: string }) {
  return (
    <div className="flex flex-col gap-4">
      {blocosDoEnunciado(texto).map((bloco, i) =>
        bloco.tipo === "texto" ? (
          <p key={i} className="leitura-enunciado text-ink">
            {bloco.texto}
          </p>
        ) : (
          <div key={i} className="overflow-x-auto rounded-card border border-line">
            <table className="w-full border-collapse text-left text-apoio tabular-nums text-ink">
              <thead className="bg-ground">
                <tr>
                  {bloco.titulo.map((celula, j) => (
                    <th key={j} scope="col" className="border-b border-line px-3 py-2 font-semibold">
                      {celula}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {bloco.linhas.map((linha, j) => (
                  <tr key={j} className="border-b border-line-soft last:border-0">
                    {linha.map((celula, k) => (
                      <td key={k} className="px-3 py-2 align-top">
                        {celula}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ),
      )}
    </div>
  );
}
