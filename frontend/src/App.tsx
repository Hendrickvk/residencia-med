import { Navigate, Route, Routes } from "react-router-dom";
import { RequireAuth } from "./components/RequireAuth";
import { AppShell } from "./components/shell/AppShell";
import { NAV } from "./lib/nav";
import Login from "./pages/Login";
import Materiais from "./pages/materiais";
import Painel from "./pages/painel";
import { PermaneceNoStreamlit } from "./pages/PermaneceNoStreamlit";
import Praticar from "./pages/praticar";
import Revisao from "./pages/revisao";
import Simulado from "./pages/simulado";

// Fase 7 do MIGRACAO.md §5: decidido manter as 4 telas administrativas
// (grupo "Acervo") no Streamlit — não vão ganhar rota React própria.
const ROTAS_REACT = new Set(["/painel", "/praticar", "/revisao", "/simulado", "/materiais"]);

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route element={<RequireAuth />}>
        <Route element={<AppShell />}>
          <Route index element={<Navigate to="/painel" replace />} />
          <Route path="/painel" element={<Painel />} />
          <Route path="/praticar" element={<Praticar />} />
          <Route path="/revisao" element={<Revisao />} />
          <Route path="/simulado" element={<Simulado />} />
          <Route path="/materiais" element={<Materiais />} />
          {NAV.filter((item) => !ROTAS_REACT.has(item.path)).map((item) => (
            <Route key={item.path} path={item.path} element={<PermaneceNoStreamlit titulo={item.label} />} />
          ))}
          <Route path="*" element={<Navigate to="/painel" replace />} />
        </Route>
      </Route>
    </Routes>
  );
}
