// O tema só aparece depois da resposta, junto da discussão: antes, numa questão
// que pede o diagnóstico, ele entregaria o gabarito (DESIGN_TRIAGEM.md §6).
export function TemaDoCaso({ tema }: { tema: string | null | undefined }) {
  if (!tema) return null;
  return (
    <span className="text-apoio text-muted">
      Tema: <span className="font-medium text-ink-2">{tema}</span>
    </span>
  );
}
