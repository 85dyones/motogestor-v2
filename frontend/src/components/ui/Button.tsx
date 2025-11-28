import React from "react";
import { Loader2 } from "lucide-react";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  loading?: boolean;
  variant?: "primary" | "ghost" | "outline";
};

const Button: React.FC<ButtonProps> = ({
  children,
  loading,
  disabled,
  variant = "primary",
  className = "",
  ...rest
}) => {
  const base =
    "inline-flex items-center justify-center rounded-lg text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-slate-500 focus-visible:ring-offset-slate-900 disabled:opacity-60 disabled:cursor-not-allowed";
  const variants: Record<typeof variant, string> = {
    primary: "px-4 py-2 btn-primary text-white shadow-soft",
    ghost: "px-3 py-2 text-slate-200 hover:bg-slate-800/60",
    outline:
      "px-3 py-2 border border-slate-700 text-slate-100 hover:bg-slate-800/60"
  };

  return (
    <button
      className={`${base} ${variants[variant]} ${className}`}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && (
        <Loader2 className="mr-2 h-4 w-4 animate-spin text-slate-200" />
      )}
      {children}
    </button>
  );
};

export default Button;
