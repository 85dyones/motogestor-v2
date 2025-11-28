import React, { useEffect, useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";

const API_URL = import.meta.env.VITE_API_URL || "";

type Receivable = {
  id: number;
  customer_name?: string;
  description?: string;
  due_date?: string;
  amount: number;
};

type Payable = {
  id: number;
  supplier_name?: string;
  description?: string;
  due_date?: string;
  amount: number;
};

const FinancePage: React.FC = () => {
  const { token } = useAuth();
  const [receivables, setReceivables] = useState<Receivable[]>([]);
  const [payables, setPayables] = useState<Payable[]>([]);
  const [loading, setLoading] = useState(true);

  const loadFinance = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [recResp, payResp] = await Promise.all([
        fetch(`${API_URL}/financial/receivables?status=PENDING`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${API_URL}/financial/payables?status=PENDING`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      if (recResp.ok) {
        setReceivables((await recResp.json()) as Receivable[]);
      }
      if (payResp.ok) {
        setPayables((await payResp.json()) as Payable[]);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFinance();
  }, [token]);

  const totalRec = receivables.reduce((s, r) => s + Number(r.amount || 0), 0);
  const totalPay = payables.reduce((s, p) => s + Number(p.amount || 0), 0);

  return (
    <div className="py-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-slate-50">Financeiro</h1>
          <p className="text-sm text-slate-400">
            Visão rápida de contas a receber e a pagar. Não é um ERP inteiro,
            é o que importa pro caixa.
          </p>
        </div>
        <Button variant="outline" onClick={loadFinance}>
          Atualizar
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs uppercase tracking-wide text-slate-400">
              Contas a receber (pendentes)
            </span>
            <span className="text-xs text-emerald-300">
              Total R$ {totalRec.toFixed(2)}
            </span>
          </div>
          {loading ? (
            <div className="py-3 text-sm text-slate-400">
              Carregando recebíveis...
            </div>
          ) : receivables.length === 0 ? (
            <div className="py-3 text-sm text-slate-400">
              Nenhum recebível pendente.
            </div>
          ) : (
            <div className="space-y-1 max-h-72 overflow-y-auto pr-1">
              {receivables.map(r => (
                <div
                  key={r.id}
                  className="border border-slate-800/70 rounded-xl px-3 py-2 bg-slate-950/60"
                >
                  <div className="flex justify-between text-sm text-slate-50">
                    <span>{r.customer_name || "Cliente não informado"}</span>
                    <span>R$ {Number(r.amount).toFixed(2)}</span>
                  </div>
                  <div className="text-[0.7rem] text-slate-500 flex justify-between mt-0.5">
                    <span>{r.description || "Sem descrição"}</span>
                    <span>
                      Vencimento:{" "}
                      {r.due_date
                        ? new Date(r.due_date).toLocaleDateString("pt-BR")
                        : "-"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs uppercase tracking-wide text-slate-400">
              Contas a pagar (pendentes)
            </span>
            <span className="text-xs text-red-300">
              Total R$ {totalPay.toFixed(2)}
            </span>
          </div>
          {loading ? (
            <div className="py-3 text-sm text-slate-400">
              Carregando pagáveis...
            </div>
          ) : payables.length === 0 ? (
            <div className="py-3 text-sm text-slate-400">
              Nenhuma conta a pagar pendente.
            </div>
          ) : (
            <div className="space-y-1 max-h-72 overflow-y-auto pr-1">
              {payables.map(p => (
                <div
                  key={p.id}
                  className="border border-slate-800/70 rounded-xl px-3 py-2 bg-slate-950/60"
                >
                  <div className="flex justify-between text-sm text-slate-50">
                    <span>{p.supplier_name || "Fornecedor não informado"}</span>
                    <span>R$ {Number(p.amount).toFixed(2)}</span>
                  </div>
                  <div className="text-[0.7rem] text-slate-500 flex justify-between mt-0.5">
                    <span>{p.description || "Sem descrição"}</span>
                    <span>
                      Vencimento:{" "}
                      {p.due_date
                        ? new Date(p.due_date).toLocaleDateString("pt-BR")
                        : "-"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default FinancePage;
