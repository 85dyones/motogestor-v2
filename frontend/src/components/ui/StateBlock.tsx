import React from "react";
import { AlertTriangle, Loader2 } from "lucide-react";

const StateBlock: React.FC<{
  state: "loading" | "error" | "empty";
  message?: string;
}> = ({ state, message }) => {
  if (state === "loading") {
    return (
      <div className="flex items-center gap-2 text-slate-400 text-sm">
        <Loader2 className="h-4 w-4 animate-spin" /> Carregando...
      </div>
    );
  }
  if (state === "error") {
    return (
      <div className="flex items-center gap-2 text-red-300 text-sm">
        <AlertTriangle className="h-4 w-4" /> {message || "Erro ao carregar"}
      </div>
    );
  }
  return <div className="text-xs text-slate-500">Nenhum dado para exibir.</div>;
};

export default StateBlock;
