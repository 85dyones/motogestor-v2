import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback
} from "react";
import { useAuth } from "./AuthContext";

type ThemePalette = {
  id: string;
  name: string;
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  surface: string;
};

type ThemeContextValue = {
  palette: ThemePalette | null;
  plan: "BASIC" | "PRO" | "ENTERPRISE";
  loading: boolean;
  availableThemes: ThemePalette[];
  setPaletteById: (id: string) => void;
};

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

const API_URL = import.meta.env.VITE_API_URL || "";

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({
  children
}) => {
  const { token, user } = useAuth();
  const [palette, setPalette] = useState<ThemePalette | null>(null);
  const [availableThemes, setAvailableThemes] = useState<ThemePalette[]>([]);
  const [plan, setPlan] = useState<"BASIC" | "PRO" | "ENTERPRISE">("BASIC");
  const [loading, setLoading] = useState(true);

  const applyPaletteToDocument = useCallback((pal: ThemePalette | null) => {
    const root = document.documentElement;
    if (!pal) return;
    root.style.setProperty("--color-primary", pal.primary);
    root.style.setProperty("--color-secondary", pal.secondary);
    root.style.setProperty("--color-accent", pal.accent);
    root.style.setProperty("--color-background", pal.background);
    root.style.setProperty("--color-surface", pal.surface);
  }, []);

  // busca tema do tenant
  useEffect(() => {
    if (!token || !user) {
      setLoading(false);
      return;
    }

    const fetchTheme = async () => {
      setLoading(true);
      try {
        const resp = await fetch(`${API_URL}/tenant/theme`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!resp.ok) throw new Error("Falha ao carregar tema");
        const data = await resp.json();

        const tPlan =
          (data.tenant?.plan as "BASIC" | "PRO" | "ENTERPRISE") || "BASIC";
        setPlan(tPlan);

        const themes = (data.themes || []) as ThemePalette[];
        setAvailableThemes(themes);

        const chosen = themes[0] ?? null;
        setPalette(chosen);
        applyPaletteToDocument(chosen);
      } catch {
        // vida que segue com padrão
      } finally {
        setLoading(false);
      }
    };

    fetchTheme();
  }, [token, user, applyPaletteToDocument]);

  const setPaletteById = (id: string) => {
    const found = availableThemes.find(t => t.id === id) || availableThemes[0];
    if (!found) return;
    setPalette(found);
    applyPaletteToDocument(found);
  };

  return (
    <ThemeContext.Provider
      value={{ palette, plan, loading, availableThemes, setPaletteById }}
    >
      {children}
    </ThemeContext.Provider>
  );
};

export const useThemeMoto = (): ThemeContextValue => {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useThemeMoto deve ser usado dentro de ThemeProvider");
  return ctx;
};
