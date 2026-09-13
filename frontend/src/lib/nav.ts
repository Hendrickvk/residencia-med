import {
  BookOpen,
  Brain,
  Database,
  FilePlus2,
  LayoutDashboard,
  type LucideIcon,
  PencilLine,
  RefreshCw,
  Timer,
  UploadCloud,
} from "lucide-react";

export interface ItemNav {
  label: string;
  // Rótulo da aba na barra superior, quando o completo não cabe (DESIGN_TRIAGEM.md §5).
  curto?: string;
  path: string;
  icon: LucideIcon;
}

// path é a chave estável de roteamento (MIGRACAO.md §1) — nunca renomear
// um path pra "arrumar" a URL sem migrar quem já tem link/sessão salva.
export const NAV: ItemNav[] = [
  { label: "Painel", path: "/painel", icon: LayoutDashboard },
  { label: "Praticar", path: "/praticar", icon: PencilLine },
  { label: "Simulado", path: "/simulado", icon: Timer },
  { label: "Revisão espaçada", curto: "Revisão", path: "/revisao", icon: Brain },
  { label: "Materiais", path: "/materiais", icon: BookOpen },
];

// Telas administrativas que ficam no Streamlit (MIGRACAO.md §5). Aparecem só
// no menu da conta, e só para admin (DESIGN_TRIAGEM.md §5).
export const ACERVO: ItemNav[] = [
  { label: "Banco de questões", path: "/banco", icon: Database },
  { label: "Nova questão", path: "/nova-questao", icon: FilePlus2 },
  { label: "Importar planilha", path: "/importar", icon: UploadCloud },
  { label: "Sincronizar MediaFire", path: "/sincronizar", icon: RefreshCw },
];

export const LABEL_POR_PATH: Record<string, string> = Object.fromEntries(
  [...NAV, ...ACERVO].map((item) => [item.path, item.label]),
);
