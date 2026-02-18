import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error("Unhandled React error", error, errorInfo);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <main className="error-boundary-fallback">
          <h1>Something went wrong</h1>
          <p>Please refresh the page. The error has been logged.</p>
        </main>
      );
    }

    return this.props.children;
  }
}
