import type { InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
}

export default function Input({
  label,
  className = "",
  ...props
}: InputProps): JSX.Element {
  return (
    <label className="field-label">
      <span>{label}</span>
      <input className={`input ${className}`.trim()} {...props} />
    </label>
  );
}
