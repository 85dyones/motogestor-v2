import React, { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import Button from "../../components/ui/Button";
import Input from "../../components/ui/Input";
import { Wrench } from "lucide-react";

const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email.trim(), password);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Falha ao entrar. Tente novamente."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="h-screen w-screen theme-bg flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-slate-950/70 border border-slate-800/80 rounded-3xl p-6 shadow-soft backdrop-blur-xl">
        <div className="flex items-center gap-3 mb-5">
          <div className="h-10 w-10 rounded-2xl bg-primary flex items-center justify-center shadow-soft">
            <Wrench className="h-5 w-5 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold text-slate-50">
              MotoGestor v2
            </span>
            <span className="text-xs text-slate-400">
              Gestão de oficinas com cara de 2025.
            </span>
          </div>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <Input
            label="E-mail"
            type="email"
            placeholder="voce@oficina.com.br"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
          />
          <Input
            label="Senha"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
          />

          {error && (
            <div className="text-xs text-red-400 bg-red-950/40 border border-red-700/40 rounded-xl px-3 py-2">
              {error}
            </div>
          )}

          <Button
            type="submit"
            loading={submitting}
            className="w-full mt-2"
          >
            Entrar
          </Button>
        </form>

        <p className="mt-4 text-[0.75rem] text-slate-500">
          Acesso destinado às oficinas credenciadas. Em caso de dúvida, fale com
          o suporte da V2O5.
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
