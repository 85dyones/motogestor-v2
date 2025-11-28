import React from "react";
import { NavLink } from "react-router-dom";
import {
  Gauge,
  Users,
  Wrench,
  ClipboardList,
  CreditCard,
  Settings
} from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { useThemeMoto } from "../../contexts/ThemeContext";

const navItems = [
  { to: "/", label: "Visão geral", icon: Gauge },
  { to: "/customers", label: "Clientes", icon: Users },
  { to: "/os", label: "Ordens de Serviço", icon: Wrench },
  { to: "/tasks", label: "Tarefas", icon: ClipboardList },
  { to: "/finance", label: "Financeiro", icon: CreditCard },
  { to: "/settings", label: "Configurações", icon: Settings }
];

const Sidebar: React.FC = () => {
  const { user } = useAuth();
  const { plan } = useThemeMoto();

  return (
    <aside className="w-60 border-r border-slate-800/80 bg-slate-950/60 backdrop-blur-xl flex flex-col">
      <div className="px-4 pt-4 pb-3 border-b border-slate-800/80">
        <div className="flex items-center gap-2">
          <div className="h-9 w-9 rounded-2xl bg-primary flex items-center justify-center text-xs font-bold text-white shadow-soft">
            MG
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold text-slate-50">
              {user?.tenant_name || "MotoGestor"}
            </span>
            <span className="chip-plan border border-slate-700 text-slate-300 bg-slate-900/60">
              {plan.toLowerCase()}
            </span>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(item => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                [
                  "flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm transition",
                  isActive
                    ? "bg-primary/15 text-primary font-medium border border-primary/50"
                    : "text-slate-300 hover:bg-slate-800/60 border border-transparent"
                ].join(" ")
              }
            >
              <Icon className="h-4 w-4" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="px-4 pb-4 text-[0.68rem] text-slate-500 border-t border-slate-800/80">
        <div>MotoGestor v2</div>
        <div className="text-slate-600">Gestão de oficinas sem drama.</div>
      </div>
    </aside>
  );
};

export default Sidebar;
