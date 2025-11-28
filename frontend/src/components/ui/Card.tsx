import React from "react";

const Card: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = ""
}) => (
  <div className={`bg-surface/80 border border-slate-800/80 rounded-2xl p-4 ${className}`}>
    {children}
  </div>
);

export default Card;
