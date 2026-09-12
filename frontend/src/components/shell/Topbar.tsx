import { Flame, LogOut, Menu, Moon, Sun } from "lucide-react";
import { useState } from "react";
import type { Me } from "../../lib/types";
import type { Tema } from "../../lib/theme";
import { BuscaGlobal } from "./BuscaGlobal";

interface TopbarProps {
  titulo: string;
  tema: Tema;
  onAlternarTema: () => void;
  onAbrirMenu: () => void;
  me?: Me;
  onSair: () => void;
}

function diasAteProva(provaAlvo: string | null): string {
  if (!provaAlvo) return "prova alvo não definida";
  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  const alvo = new Date(`${provaAlvo}T00:00:00`);
  const dias = Math.round((alvo.getTime() - hoje.getTime()) / 86_400_000);
  if (dias < 0) return "data da prova já passou";
  return `prova em ${dias} dia${dias !== 1 ? "s" : ""}`;
}

export function Topbar({ titulo, tema, onAlternarTema, onAbrirMenu, me, onSair }: TopbarProps) {
  const [popoverAberto, setPopoverAberto] = useState(false);
  const iniciais = me?.email ? me.email[0].toUpperCase() : "?";

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b border-line bg-surface px-4">
      <button
        type="button"
        onClick={onAbrirMenu}
        className="rounded-btn p-1.5 text-ink-500 hover:bg-canvas md:hidden"
        aria-label="Abrir menu"
      >
        <Menu size={20} strokeWidth={1.5} />
      </button>

      <div className="text-[15px] font-semibold text-ink-700">{titulo}</div>

      <div className="ml-auto flex items-center gap-3">
        <BuscaGlobal />

        {me && (
          <span
            className={`flex items-center gap-1.5 rounded-pill px-2.5 py-1 text-apoio font-medium ${
              me.respondeu_hoje ? "bg-correct-soft text-correct" : "bg-warn-soft text-warn"
            }`}
          >
            <Flame size={13} strokeWidth={1.5} />
            {me.ofensiva_dias} dia{me.ofensiva_dias !== 1 ? "s" : ""}
          </span>
        )}

        <span className="hidden items-center rounded-pill bg-canvas px-2.5 py-1 text-apoio text-ink-500 sm:flex">
          {diasAteProva(me?.prova_alvo ?? null)}
        </span>

        <button
          type="button"
          onClick={onAlternarTema}
          className="rounded-btn p-1.5 text-ink-500 transition-hover hover:bg-canvas"
          aria-label="Alternar tema"
        >
          {tema === "light" ? <Moon size={18} strokeWidth={1.5} /> : <Sun size={18} strokeWidth={1.5} />}
        </button>

        <div className="relative">
          <button
            type="button"
            onClick={() => setPopoverAberto((v) => !v)}
            className="flex h-8 w-8 items-center justify-center rounded-pill bg-action-soft text-apoio font-medium text-action"
          >
            {iniciais}
          </button>
          {popoverAberto && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setPopoverAberto(false)} />
              <div className="absolute right-0 top-10 z-50 w-56 rounded-panel border border-line bg-surface p-3 shadow-sm">
                <div className="mb-3 break-all text-apoio text-ink-500">{me?.email}</div>
                <button
                  type="button"
                  onClick={onSair}
                  className="flex w-full items-center gap-2 rounded-btn border border-line px-3 py-2 text-corpo text-ink-700 transition-hover hover:border-ink-300"
                >
                  <LogOut size={16} strokeWidth={1.5} />
                  Sair da conta
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
