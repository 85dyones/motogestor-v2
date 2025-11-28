import React from "react";
import Card from "../../components/ui/Card";
import { useThemeMoto } from "../../contexts/ThemeContext";
import { useAuth } from "../../contexts/AuthContext";

const SettingsPage: React.FC = () => {
  const { palette, availableThemes, setPaletteById, plan } = useThemeMoto();
  const { user } = useAuth();

  return (
    <div className="py-5 space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-slate-50">Configurações</h1>
        <p className="text-sm text-slate-400">
          Ajustes visuais e informações básicas da sua oficina.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <h2 className="text-sm font-medium text-slate-100 mb-2">
            Sua oficina
          </h2>
          <div className="text-sm text-slate-300 space-y-1">
            <div>
              <span className="text-slate-400">Nome: </span>
              <span>{user?.tenant_name || "-"}</span>
            </div>
            <div>
              <span className="text-slate-400">Plano: </span>
              <span className="uppercase text-sky-300">
                {plan.toLowerCase()}
              </span>
            </div>
          </div>
          <p className="text-xs text-slate-500 mt-3">
            Planos PRO e ENTERPRISE desbloqueiam mais opções de personalização
            e recursos avançados de automação e IA.
          </p>
        </Card>

        <Card>
          <h2 className="text-sm font-medium text-slate-100 mb-2">
            Tema da interface
          </h2>
          <p className="text-xs text-slate-400 mb-3">
            Escolha a paleta que melhor combina com a identidade da sua oficina.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {availableThemes.map(t => (
              <button
                key={t.id}
                type="button"
                onClick={() => setPaletteById(t.id)}
                className={`rounded-2xl border px-3 py-2 text-left text-xs transition ${
                  palette?.id === t.id
                    ? "border-primary/70 bg-slate-900/80"
                    : "border-slate-800 bg-slate-950/60 hover:border-slate-600"
                }`}
              >
                <div className="font-medium text-slate-100 mb-1">{t.name}</div>
                <div className="flex gap-1">
                  <span
                    className="h-4 w-4 rounded-full border border-slate-900"
                    style={{ backgroundColor: t.primary }}
                  />
                  <span
                    className="h-4 w-4 rounded-full border border-slate-900"
                    style={{ backgroundColor: t.secondary }}
                  />
                  <span
                    className="h-4 w-4 rounded-full border border-slate-900"
                    style={{ backgroundColor: t.accent }}
                  />
                </div>
              </button>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default SettingsPage;
