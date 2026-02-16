import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

type ButtonVariant = "primary" | "secondary" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  fullWidth?: boolean;
}

export default function Button({
  children,
  variant = "primary",
  fullWidth = false,
  className = "",
  ...props
}: PropsWithChildren<ButtonProps>): JSX.Element {
  return (
    <button
      className={`btn btn-${variant}${fullWidth ? " btn-full" : ""} ${className}`.trim()}
      {...props}
    >
      {children}
    </button>
  );
}
