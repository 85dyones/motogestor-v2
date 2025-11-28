import React from "react";
import { LogOut, Palette } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { useThemeMoto } from "../../contexts/ThemeContext";

const Topbar: React.FC = () => {
  const { user, logout } = useAuth();
  const { palette, availableThemes, setPaletteById } = useThemeMoto();

  return (
    <header className="h-14 flex items-center justify-between px-5 border-b border-slate-800/80 bg-slate-950/60 backdrop-blur-xl">
      <div className="flex flex-col">
        <span className="text-xs text-slate-400 uppercase tracking-wide">
          Painel
        </span>
        <span className="text-sm font-medium text-slate-50">
          MotoGestor v2
        </span>
      </div>

      <div className="flex items-center gap-4">
        {/* seletor de tema simples */}
        <div className="flex items-center gap-2">
          <Palette className="h-4 w-4 text-slate-400" />
          <select
            className="bg-slate-900/80 border border-slate-700 rounded-lg text-xs px-2 py-1 text-slate-100"
            value={palette?.id || ""}
            onChange={e => setPaletteById(e.target.value)}
          >
            {availableThemes.map(t => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex flex-col text-right">
            <span className="text-xs text-slate-300">{user?.name}</span>
            <span className="text-[0.7rem] text-slate-500">
              {user?.email}
            </span>
          </div>
          <button
            onClick={logout}
            className="p-2 rounded-xl hover:bg-slate-800/80 text-slate-300"
            title="Sair"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
  );
};

export default Topbar;
