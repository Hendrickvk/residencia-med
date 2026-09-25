import {
  Brain,
  Database,
  FilePlus2,
  LayoutDashboard,
  Layers,
  type LucideIcon,
  PencilLine,
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
  { label: "Baralhos", path: "/baralhos", icon: Layers },
];

/** De que lado a tela nova entra (DESIGN_TRIAGEM.md §3): entre abas, pela ordem
 *  delas; dentro de uma aba, pela profundidade do caminho (entrar num baralho
 *  vem da direita, voltar à lista vem da esquerda). `null` quando não há lado —
 *  perfil, primeira carga, troca entre irmãos —, e aí a tela só sobe. */
export function direcaoDaNavegacao(de: string, para: string): "frente" | "tras" | null {
  const aba = (caminho: string) => NAV.findIndex((i) => caminho === i.path || caminho.startsWith(`${i.path}/`));
  const [a, b] = [aba(de), aba(para)];
  if (a >= 0 && b >= 0 && a !== b) return b > a ? "frente" : "tras";
  if (para.startsWith(`${de}/`)) return "frente";
  if (de.startsWith(`${para}/`)) return "tras";
  return null;
}

// Telas administrativas que ficam no Streamlit (MIGRACAO.md §5). Aparecem só
// no menu da conta, e só para admin (DESIGN_TRIAGEM.md §5).
export const ACERVO: ItemNav[] = [
  { label: "Banco de questões", path: "/banco", icon: Database },
  { label: "Nova questão", path: "/nova-questao", icon: FilePlus2 },
  { label: "Importar planilha", path: "/importar", icon: UploadCloud },
];
