import React from "react";
import AppRoutes from "./router";
import { useAuth } from "./contexts/AuthContext";

const App: React.FC = () => {
  const { loading } = useAuth();

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-slate-950">
        <div className="text-slate-300 text-sm">Carregando sessão...</div>
      </div>
    );
  }

  return <AppRoutes />;
};

export default App;
