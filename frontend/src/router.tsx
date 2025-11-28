import React from "react";
import { Navigate, RouteObject, useRoutes } from "react-router-dom";
import { useAuth } from "./contexts/AuthContext";

import LoginPage from "./pages/auth/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import CustomerListPage from "./pages/customers/CustomerListPage";
import ServiceOrderListPage from "./pages/os/ServiceOrderListPage";
import TasksPage from "./pages/tasks/TasksPage";
import FinancePage from "./pages/finance/FinancePage";
import SettingsPage from "./pages/settings/SettingsPage";
import AppShell from "./components/layout/AppShell";

const AppRoutes: React.FC = () => {
  const { user } = useAuth();

  const routes: RouteObject[] = [
    {
      path: "/login",
      element: user ? <Navigate to="/" replace /> : <LoginPage />
    },
    {
      path: "/",
      element: user ? <AppShell /> : <Navigate to="/login" replace />,
      children: [
        { index: true, element: <DashboardPage /> },
        { path: "customers", element: <CustomerListPage /> },
        { path: "os", element: <ServiceOrderListPage /> },
        { path: "tasks", element: <TasksPage /> },
        { path: "finance", element: <FinancePage /> },
        { path: "settings", element: <SettingsPage /> }
      ]
    },
    { path: "*", element: <Navigate to={user ? "/" : "/login"} replace /> }
  ];

  return useRoutes(routes);
};

export default AppRoutes;
