import React, { useEffect, useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import Card from "../../components/ui/Card";
import Input from "../../components/ui/Input";
import Button from "../../components/ui/Button";

const API_URL = import.meta.env.VITE_API_URL || "";

type Customer = {
  id: number;
  name: string;
  phone?: string;
  email?: string;
  document?: string;
};

const CustomerListPage: React.FC = () => {
  const { token } = useAuth();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  const loadCustomers = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const resp = await fetch(`${API_URL}/management/customers`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (resp.ok) {
        const data = (await resp.json()) as Customer[];
        setCustomers(data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCustomers();
  }, [token]);

  const filtered = customers.filter(c =>
    [c.name, c.phone, c.email].some(v =>
      v?.toLowerCase().includes(search.toLowerCase())
    )
  );

  return (
    <div className="py-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-slate-50">Clientes</h1>
          <p className="text-sm text-slate-400">
            Base de clientes da oficina. Use como ponto central para OS, contatos e CRM.
          </p>
        </div>
      </div>

      <Card>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-3">
          <Input
            placeholder="Buscar por nome, telefone ou e-mail..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          <Button variant="outline" onClick={loadCustomers}>
            Atualizar lista
          </Button>
        </div>

        <div className="border border-slate-800/80 rounded-2xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-900/70 text-slate-400 text-xs uppercase tracking-wide">
              <tr>
                <th className="text-left px-3 py-2">Nome</th>
                <th className="text-left px-3 py-2">Telefone</th>
                <th className="text-left px-3 py-2">E-mail</th>
                <th className="text-left px-3 py-2 w-10"></th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td
                    colSpan={4}
                    className="px-3 py-4 text-center text-slate-500"
                  >
                    Carregando clientes...
                  </td>
                </tr>
              )}
              {!loading && filtered.length === 0 && (
                <tr>
                  <td
                    colSpan={4}
                    className="px-3 py-4 text-center text-slate-500"
                  >
                    Nenhum cliente encontrado.
                  </td>
                </tr>
              )}
              {!loading &&
                filtered.map(c => (
                  <tr
                    key={c.id}
                    className="border-t border-slate-800/60 hover:bg-slate-900/40"
                  >
                    <td className="px-3 py-2 text-slate-50">{c.name}</td>
                    <td className="px-3 py-2 text-slate-200">
                      {c.phone || "-"}
                    </td>
                    <td className="px-3 py-2 text-slate-300">
                      {c.email || "-"}
                    </td>
                    <td className="px-3 py-2 text-right text-xs text-slate-500">
                      {/* futuro: actions */}
                      ...
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

export default CustomerListPage;
