import { useState } from "react";
import Configurador from "./Configurador";
import EmAndamento from "./EmAndamento";
import Resultado from "./Resultado";

export default function Simulado() {
  const [simuladoId, setSimuladoId] = useState<number | null>(null);
  const [finalizado, setFinalizado] = useState(false);
  // Como no Praticar: a primeira fase entra com a troca de tela do AppShell.
  const [trocouFase, setTrocouFase] = useState(false);
  const entrada = trocouFase ? "animate-entrar" : "";

  if (simuladoId === null) {
    return (
      <div key="config" className={entrada}>
        <Configurador
          onIniciado={(id) => {
            setSimuladoId(id);
            setFinalizado(false);
            setTrocouFase(true);
          }}
        />
      </div>
    );
  }

  if (!finalizado) {
    return (
      <EmAndamento
        simuladoId={simuladoId}
        onFinalizado={() => {
          setFinalizado(true);
          setTrocouFase(true);
        }}
      />
    );
  }

  return (
    <div key="resultado" className={entrada}>
      <Resultado
        simuladoId={simuladoId}
        onNovoSimulado={() => {
          setSimuladoId(null);
          setFinalizado(false);
          setTrocouFase(true);
        }}
      />
    </div>
  );
}
