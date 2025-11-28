import React, { useEffect, useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";

const API_URL = import.meta.env.VITE_API_URL || "";

type ServiceOrder = {
  id: number;
  code?: string;
  customer_name?: string;
  bike_model?: string;
  plate?: string;
  status: string;
  total_amount?: number;
};

const statusLabel: Record<string, string> = {
  OPEN: "Aberta",
  IN_PROGRESS: "Em execução",
  WAITING_PARTS: "Aguardando peças",
  COMPLETED: "Concluída",
  CANCELLED: "Cancelada"
};

const ServiceOrderListPage: React.FC = () => {
  const { token } = useAuth();
  const [orders, setOrders] = useState<ServiceOrder[]>([]);
  const [loading, setLoading] = useState(true);

  const loadOS = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const resp = await fetch(`${API_URL}/management/os`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (resp.ok) {
        const data = (await resp.json()) as ServiceOrder[];
        setOrders(data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOS();
  }, [token]);

  const badgeTone = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return "success";
      case "WAITING_PARTS":
      case "OPEN":
      case "IN_PROGRESS":
        return "info";
      case "CANCELLED":
      default:
        return "warning";
    }
  };

  return (
    <div className="py-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-slate-50">
            Ordens de Serviço
          </h1>
          <p className="text-sm text-slate-400">
            Controle de OS em andamento, concluídas e pendentes.
          </p>
        </div>
        <Button variant="primary" onClick={() => {}}>
          Nova OS
        </Button>
      </div>

      <Card>
        <div className="border border-slate-800/80 rounded-2xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-900/70 text-slate-400 text-xs uppercase tracking-wide">
              <tr>
                <th className="text-left px-3 py-2">Código</th>
                <th className="text-left px-3 py-2">Cliente</th>
                <th className="text-left px-3 py-2">Moto</th>
                <th className="text-left px-3 py-2">Placa</th>
                <th className="text-left px-3 py-2">Status</th>
                <th className="text-right px-3 py-2">Total</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-3 py-4 text-center text-slate-500"
                  >
                    Carregando OS...
                  </td>
                </tr>
              )}
              {!loading && orders.length === 0 && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-3 py-4 text-center text-slate-500"
                  >
                    Nenhuma OS cadastrada.
                  </td>
                </tr>
              )}
              {!loading &&
                orders.map(o => (
                  <tr
                    key={o.id}
                    className="border-t border-slate-800/60 hover:bg-slate-900/40"
                  >
                    <td className="px-3 py-2 text-slate-50">
                      {o.code || `OS-${o.id}`}
                    </td>
                    <td className="px-3 py-2 text-slate-200">
                      {o.customer_name || "-"}
                    </td>
                    <td className="px-3 py-2 text-slate-200">
                      {o.bike_model || "-"}
                    </td>
                    <td className="px-3 py-2 text-slate-300">
                      {o.plate || "-"}
                    </td>
                    <td className="px-3 py-2">
                      <Badge tone={badgeTone(o.status)}>
                        {statusLabel[o.status] || o.status}
                      </Badge>
                    </td>
                    <td className="px-3 py-2 text-right text-slate-100">
                      R$ {Number(o.total_amount ?? 0).toFixed(2)}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

export default ServiceOrderListPage;
