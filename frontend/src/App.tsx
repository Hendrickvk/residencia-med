import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { EsqueletoApp, RequireAuth } from "./components/RequireAuth";
import { ACERVO } from "./lib/nav";
import Inicio from "./pages/Inicio";
import Login from "./pages/Login";
import Confirmar from "./pages/Confirmar";
import Senha from "./pages/Senha";
import { PermaneceNoStreamlit } from "./pages/PermaneceNoStreamlit";

// O app por trás do login vem sob demanda. Quem chega pela página pública — o
// link compartilhado, quase sempre no celular — baixava o app inteiro (533 KB)
// para ver uma página que usa uma fração dele. As telas públicas ficam no pacote
// de entrada; a casca e cada tela do app, num arquivo próprio.
const carregarCasca = () => import("./components/shell/AppShell");
const TELAS = {
  painel: () => import("./pages/painel"),
  praticar: () => import("./pages/praticar"),
  revisao: () => import("./pages/revisao"),
  baralhos: () => import("./pages/baralhos"),
  perfil: () => import("./pages/perfil"),
  simulado: () => import("./pages/simulado"),
};
const carregarBaralho = () => import("./pages/baralhos/Baralho");

const AppShell = lazy(() => carregarCasca().then((m) => ({ default: m.AppShell })));
const Painel = lazy(TELAS.painel);
const Praticar = lazy(TELAS.praticar);
const Revisao = lazy(TELAS.revisao);
const Baralhos = lazy(TELAS.baralhos);
const Baralho = lazy(carregarBaralho);
const PaginaPerfil = lazy(TELAS.perfil);
const Simulado = lazy(TELAS.simulado);

// Quem abre direto numa tela do app (o app instalado abre em /painel) começa a
// baixar a casca e a tela junto com o /me, em vez de esperar por ele. O erro
// fica para quando a tela for de fato aberta.
const [, secao, detalhe] = window.location.pathname.split("/");
if (secao in TELAS) {
  const ignorar = () => {};
  carregarCasca().catch(ignorar);
  (secao === "baralhos" && detalhe ? carregarBaralho : TELAS[secao as keyof typeof TELAS])().catch(ignorar);
}

export default function App() {
  return (
    <Routes>
      {/* Página pública: quem tem sessão é mandado ao Painel lá dentro. */}
      <Route path="/" element={<Inicio />} />
      <Route path="/login" element={<Login />} />
      {/* Link do e-mail de redefinição: público, porque quem chega aqui é
          exatamente quem não consegue entrar. */}
      <Route path="/senha/:token" element={<Senha />} />
      {/* Link de confirmação: também público, e pelo mesmo motivo — ele costuma
          ser aberto no celular, não no navegador onde a conta foi criada. */}
      <Route path="/confirmar/:token" element={<Confirmar />} />

      <Route element={<RequireAuth />}>
        <Route
          element={
            <Suspense fallback={<EsqueletoApp />}>
              <AppShell />
            </Suspense>
          }
        >
          <Route path="/painel" element={<Painel />} />
          <Route path="/praticar" element={<Praticar />} />
          <Route path="/revisao" element={<Revisao />} />
          <Route path="/baralhos" element={<Baralhos />} />
          <Route path="/baralhos/:id" element={<Baralho />} />
          {/* Fora do NAV de propósito: a conta não é uma aba de estudo, e o
              caminho para ela é o menu da conta. */}
          <Route path="/perfil" element={<PaginaPerfil />} />
          <Route path="/simulado" element={<Simulado />} />
          {/* Fase 7 do MIGRACAO.md §5: as telas do Acervo ficam no Streamlit
              e não ganham rota React própria. */}
          {ACERVO.map((item) => (
            <Route key={item.path} path={item.path} element={<PermaneceNoStreamlit titulo={item.label} />} />
          ))}
          <Route path="*" element={<Navigate to="/painel" replace />} />
        </Route>
      </Route>
    </Routes>
  );
}
