import React from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

const AppShell: React.FC = () => {
  return (
    <div className="h-screen w-screen overflow-hidden theme-bg">
      <div className="h-full max-w-7xl mx-auto flex">
        <Sidebar />
        <main className="flex-1 flex flex-col">
          <Topbar />
          <div className="flex-1 overflow-y-auto px-5 pb-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default AppShell;
