import { useState } from "react";
import Configurador from "./Configurador";
import EmAndamento from "./EmAndamento";
import Resultado from "./Resultado";

export default function Simulado() {
  const [simuladoId, setSimuladoId] = useState<number | null>(null);
  const [finalizado, setFinalizado] = useState(false);

  if (simuladoId === null) {
    return (
      <Configurador
        onIniciado={(id) => {
          setSimuladoId(id);
          setFinalizado(false);
        }}
      />
    );
  }

  if (!finalizado) {
    return <EmAndamento simuladoId={simuladoId} onFinalizado={() => setFinalizado(true)} />;
  }

  return (
    <Resultado
      simuladoId={simuladoId}
      onNovoSimulado={() => {
        setSimuladoId(null);
        setFinalizado(false);
      }}
    />
  );
}
