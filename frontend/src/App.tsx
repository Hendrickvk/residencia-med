import { Navigate, Route, Routes } from "react-router-dom";
import { RequireAuth } from "./components/RequireAuth";
import { AppShell } from "./components/shell/AppShell";
import { ACERVO } from "./lib/nav";
import Login from "./pages/Login";
import Confirmar from "./pages/Confirmar";
import Senha from "./pages/Senha";
import Painel from "./pages/painel";
import { PermaneceNoStreamlit } from "./pages/PermaneceNoStreamlit";
import PaginaPerfil from "./pages/perfil";
import Praticar from "./pages/praticar";
import Revisao from "./pages/revisao";
import Simulado from "./pages/simulado";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      {/* Link do e-mail de redefinição: público, porque quem chega aqui é
          exatamente quem não consegue entrar. */}
      <Route path="/senha/:token" element={<Senha />} />
      {/* Link de confirmação: também público, e pelo mesmo motivo — ele costuma
          ser aberto no celular, não no navegador onde a conta foi criada. */}
      <Route path="/confirmar/:token" element={<Confirmar />} />

      <Route element={<RequireAuth />}>
        <Route element={<AppShell />}>
          <Route index element={<Navigate to="/painel" replace />} />
          <Route path="/painel" element={<Painel />} />
          <Route path="/praticar" element={<Praticar />} />
          <Route path="/revisao" element={<Revisao />} />
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
