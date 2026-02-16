interface ToastProps {
  message: string;
  tone?: "success" | "error";
}

export default function Toast({
  message,
  tone = "success",
}: ToastProps): JSX.Element {
  return <div className={`toast toast-${tone}`}>{message}</div>;
}
