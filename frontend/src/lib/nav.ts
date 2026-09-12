import {
  Brain,
  Database,
  FilePlus2,
  LayoutDashboard,
  type LucideIcon,
  PencilLine,
  RefreshCw,
  BookOpen,
  Timer,
  UploadCloud,
} from "lucide-react";

export interface ItemNav {
  grupo: "Estudo" | "Acervo";
  label: string;
  path: string;
  icon: LucideIcon;
}

// path é a chave estável de roteamento (MIGRACAO.md §1) — nunca renomear
// um path pra "arrumar" a URL sem migrar quem já tem link/sessão salva.
export const NAV: ItemNav[] = [
  { grupo: "Estudo", label: "Painel", path: "/painel", icon: LayoutDashboard },
  { grupo: "Estudo", label: "Praticar", path: "/praticar", icon: PencilLine },
  { grupo: "Estudo", label: "Simulado", path: "/simulado", icon: Timer },
  { grupo: "Estudo", label: "Revisão espaçada", path: "/revisao", icon: Brain },
  { grupo: "Estudo", label: "Materiais", path: "/materiais", icon: BookOpen },
  { grupo: "Acervo", label: "Banco de questões", path: "/banco", icon: Database },
  { grupo: "Acervo", label: "Nova questão", path: "/nova-questao", icon: FilePlus2 },
  { grupo: "Acervo", label: "Importar planilha", path: "/importar", icon: UploadCloud },
  { grupo: "Acervo", label: "Sincronizar MediaFire", path: "/sincronizar", icon: RefreshCw },
];

export const LABEL_POR_PATH: Record<string, string> = Object.fromEntries(
  NAV.map((item) => [item.path, item.label]),
);
