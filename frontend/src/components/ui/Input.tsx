import React from "react";

type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  error?: string;
};

const Input: React.FC<InputProps> = ({ label, error, ...rest }) => {
  return (
    <label className="flex flex-col gap-1 text-sm text-slate-200">
      {label && <span className="text-xs uppercase tracking-wide">{label}</span>}
      <input
        className="px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-sm text-slate-50 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-500/70 focus:border-slate-500"
        {...rest}
      />
      {error && <span className="text-xs text-red-400 mt-0.5">{error}</span>}
    </label>
  );
};

export default Input;
