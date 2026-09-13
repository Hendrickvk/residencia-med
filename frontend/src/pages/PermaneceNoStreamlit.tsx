import { ExternalLink } from "lucide-react";
import { BOTAO_PRIMARIO } from "../lib/estilos";

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
    <div className="mx-auto flex max-w-[640px] flex-col items-start gap-4 rounded-caso border border-dashed border-line px-8 py-12">
      <span className="rotulo text-muted">Acervo · Streamlit</span>
      <h1 className="text-titulo">{titulo}</h1>
      <p className="text-corpo text-ink-2">
        Esta tela administrativa continua no Streamlit, ligada ao mesmo banco de dados. O Streamlit não abre telas
        por endereço: depois de entrar, escolha "{titulo}" no menu lateral.
      </p>
      <a href={STREAMLIT_URL} target="_blank" rel="noreferrer" className={BOTAO_PRIMARIO}>
        Abrir no Streamlit
        <ExternalLink size={16} strokeWidth={2} />
      </a>
    </div>
  );
}
