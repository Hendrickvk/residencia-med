import { ExternalLink } from "lucide-react";

interface Props {
  titulo: string;
}

const STREAMLIT_URL = import.meta.env.VITE_STREAMLIT_URL ?? "http://localhost:8501";

// Decisão registrada em MIGRACAO.md §5 (Fase 7): as 4 telas administrativas
// (Banco de Questões, Nova Questão, Importar Planilha, Sincronizar
// MediaFire) continuam no Streamlit — só o administrador as usa, e migrar
// não compensaria o esforço enquanto a plataforma tiver um único admin.
// Streamlit não tem rota por URL (a página é escolhida por session_state),
// então o link abre a raiz do app, não a tela específica.
export function PermaneceNoStreamlit({ titulo }: Props) {
  return (
    <div className="flex h-[60vh] flex-col items-center justify-center gap-3 rounded-panel border border-line bg-surface text-center">
      <h1 className="text-h1 text-ink-700">{titulo}</h1>
      <p className="max-w-md text-corpo text-ink-500">
        Tela administrativa — continua no Streamlit por decisão registrada no MIGRACAO.md, apontando para o mesmo
        banco de dados.
      </p>
      <a
        href={STREAMLIT_URL}
        target="_blank"
        rel="noreferrer"
        className="flex items-center gap-2 rounded-btn bg-action px-4 py-2 text-sm font-medium text-white transition-hover hover:bg-action-hover"
      >
        Abrir no Streamlit
        <ExternalLink size={16} strokeWidth={1.5} />
      </a>
    </div>
  );
}
