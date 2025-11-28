import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState
} from "react";

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

const API_URL = import.meta.env.VITE_API_URL || "";

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
      const resp = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });

      if (!resp.ok) {
        throw new Error("Credenciais inválidas");
      }

      const data = await resp.json();
      const jwt = data.access_token as string;

      // busca /me
      const meResp = await fetch(`${API_URL}/me`, {
        headers: { Authorization: `Bearer ${jwt}` }
      });
      if (!meResp.ok) throw new Error("Falha ao carregar dados do usuário");
      const me = (await meResp.json()) as User;

      setUser(me);
      setToken(jwt);
      persist(me, jwt);
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    persist(null, null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextValue => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth deve ser usado dentro de AuthProvider");
  return ctx;
};
