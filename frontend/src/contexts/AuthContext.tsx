import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState
} from "react";
import { ApiError, apiRequest } from "../lib/api";

type User = {
  id: number;
  name: string;
  email: string;
  tenant_id: number;
  tenant_name?: string;
  plan?: "BASIC" | "PRO" | "ENTERPRISE";
  role?: string;
};

type AuthContextValue = {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const STORAGE_KEY = "motogestor_auth";

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Carrega sessão do localStorage
  useEffect(() => {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      try {
        const parsed = JSON.parse(raw);
        setUser(parsed.user || null);
        setToken(parsed.token || null);
      } catch {
        localStorage.removeItem(STORAGE_KEY);
      }
    }
    setLoading(false);
  }, []);

  const persist = (u: User | null, t: string | null) => {
    if (!u || !t) {
      localStorage.removeItem(STORAGE_KEY);
      return;
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ user: u, token: t }));
  };

  const login = useCallback(async (email: string, password: string) => {
    setLoading(true);
    try {
      const data = await apiRequest<{ access_token: string; user: User }>(
        "/auth/login",
        {
          method: "POST",
          body: { email, password }
        }
      );
      const jwt = data.access_token;

      const me = await apiRequest<User>("/auth/me", { token: jwt });
      setUser(me);
      setToken(jwt);
      persist(me, jwt);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Falha ao entrar";
      throw new Error(message);
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    persist(null, null);
  }, []);

  const value = useMemo(
    () => ({ user, token, loading, login, logout }),
    [user, token, loading, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth deve ser usado dentro de AuthProvider");
  return ctx;
};
