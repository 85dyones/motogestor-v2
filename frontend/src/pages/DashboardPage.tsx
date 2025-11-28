import React, { useEffect, useState } from "react";
import Card from "../components/ui/Card";
import Badge from "../components/ui/Badge";
import StateBlock from "../components/ui/StateBlock";
import { useAuth } from "../contexts/AuthContext";
import { apiRequest, ApiError } from "../lib/api";

type Overview = {
  service_orders?: {
    total?: number;
    open?: number;
    completed?: number;
    error?: unknown;
  };
  receivables?: {
    pending_count?: number;
    pending_total?: number;
    error?: unknown;
  };
  tasks?: {
    open_count?: number;
    error?: unknown;
  };
};

const DashboardPage: React.FC = () => {
  const { token } = useAuth();
  const [overview, setOverview] = useState<Overview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    const load = async () => {
      setLoading(true);
      try {
        const data = await apiRequest<Overview>("/overview", { token });
        setOverview(data);
        setError(null);
      } catch (err) {
        const message = err instanceof ApiError ? err.message : "Erro ao carregar";
        setError(message);
        setOverview(null);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [token]);

  const so = overview?.service_orders || {};
  const rec = overview?.receivables || {};
  const tasks = overview?.tasks || {};

  return (
    <div className="py-5 space-y-5">
      <div className="flex items-baseline justify-between">
        <div>
          <h1 className="text-lg font-semibold text-slate-50">
            Visão geral da operação
          </h1>
          <p className="text-sm text-slate-400">
            Um resumo rápido do que está pegando hoje na oficina.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs uppercase tracking-wide text-slate-400">
              Ordens de Serviço
            </span>
            <Badge tone="info">OS</Badge>
          </div>
          {loading && <StateBlock state="loading" />}
          {!loading && error && <StateBlock state="error" message={error} />}
          {!loading && !error && (
            <>
              <div className="text-2xl font-semibold text-slate-50">
                {so.total ?? 0}
              </div>
              <div className="mt-2 text-xs text-slate-400 space-y-1">
                <div>
                  Abertas:{" "}
                  <span className="text-sky-300 font-medium">
                    {so.open ?? 0}
                  </span>
                </div>
                <div>
                  Concluídas:{" "}
                  <span className="text-emerald-300 font-medium">
                    {so.completed ?? 0}
                  </span>
                </div>
              </div>
            </>
          )}
        </Card>

        <Card>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs uppercase tracking-wide text-slate-400">
              Contas a receber
            </span>
            <Badge tone="warning">Financeiro</Badge>
          </div>
          {loading && <StateBlock state="loading" />}
          {!loading && error && <StateBlock state="error" message={error} />}
          {!loading && !error && (
            <>
              <div className="text-2xl font-semibold text-slate-50">
                R$ {Number(rec.pending_total ?? 0).toFixed(2)}
              </div>
              <div className="mt-2 text-xs text-slate-400">
                {rec.pending_count ?? 0} lançamentos pendentes
              </div>
            </>
          )}
        </Card>

        <Card>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs uppercase tracking-wide text-slate-400">
              Tarefas da equipe
            </span>
            <Badge tone="success">Equipe & CRM</Badge>
          </div>
          {loading && <StateBlock state="loading" />}
          {!loading && error && <StateBlock state="error" message={error} />}
          {!loading && !error && (
            <>
              <div className="text-2xl font-semibold text-slate-50">
                {tasks.open_count ?? 0}
              </div>
              <div className="mt-2 text-xs text-slate-400">
                tarefas em andamento ou pendentes
              </div>
            </>
          )}
        </Card>
      </div>

      <Card className="mt-2">
        <h2 className="text-sm font-medium text-slate-100 mb-1">
          Próximos passos sugeridos
        </h2>
        <p className="text-xs text-slate-400 mb-2">
          Use este painel como ponto de partida diário:
        </p>
        <ul className="text-xs text-slate-300 space-y-1 list-disc list-inside">
          <li>Priorize OS abertas com maior tempo de espera.</li>
          <li>Faça um pente fino nas contas a receber em atraso.</li>
          <li>Distribua tarefas claras para a equipe antes de começar o dia.</li>
        </ul>
      </Card>
    </div>
  );
};

export default DashboardPage;
