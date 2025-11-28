import React, { useEffect, useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";

const API_URL = import.meta.env.VITE_API_URL || "";

type Task = {
  id: number;
  title: string;
  status: string;
  priority: string;
  assigned_to_name?: string | null;
  related_order_id?: number | null;
};

const TasksPage: React.FC = () => {
  const { token } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  const loadTasks = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const resp = await fetch(`${API_URL}/teamcrm/tasks?only_open=1`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (resp.ok) {
        const data = (await resp.json()) as Task[];
        setTasks(data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, [token]);

  return (
    <div className="py-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-slate-50">Tarefas</h1>
          <p className="text-sm text-slate-400">
            Organização do dia da equipe. Distribua responsabilidades, não caos.
          </p>
        </div>
        <Button variant="outline" onClick={loadTasks}>
          Atualizar
        </Button>
      </div>

      <Card>
        {loading ? (
          <div className="py-4 text-sm text-slate-400">
            Carregando tarefas...
          </div>
        ) : tasks.length === 0 ? (
          <div className="py-4 text-sm text-slate-400">
            Nenhuma tarefa aberta. Ótimo sinal, ou alguém esqueceu de cadastrar.
          </div>
        ) : (
          <div className="space-y-2">
            {tasks.map(t => (
              <div
                key={t.id}
                className="rounded-2xl border border-slate-800/80 bg-slate-950/60 px-3 py-2.5 flex items-center justify-between"
              >
                <div className="flex flex-col">
                  <span className="text-sm text-slate-50">{t.title}</span>
                  <span className="text-[0.7rem] text-slate-500">
                    {t.assigned_to_name
                      ? `Responsável: ${t.assigned_to_name}`
                      : "Sem responsável definido"}
                    {t.related_order_id
                      ? ` • OS #${t.related_order_id}`
                      : ""}
                  </span>
                </div>
                <span className="text-[0.7rem] uppercase tracking-wide text-slate-400">
                  {t.priority}
                </span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

export default TasksPage;
