import React from "react";

const Badge: React.FC<{ children: React.ReactNode; tone?: "success" | "warning" | "info" }> = ({
  children,
  tone = "info"
}) => {
  const map: Record<typeof tone, string> = {
    success: "bg-emerald-500/10 text-emerald-300 border-emerald-500/40",
    warning: "bg-amber-500/10 text-amber-300 border-amber-500/40",
    info: "bg-sky-500/10 text-sky-300 border-sky-500/40"
  };
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[0.7rem] border ${map[tone]}`}
    >
      {children}
    </span>
  );
};

export default Badge;
