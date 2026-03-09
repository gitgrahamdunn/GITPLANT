import React from 'react';

type Props = React.PropsWithChildren;
type State = { hasError: boolean };

export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false };
  static getDerivedStateFromError(): State { return { hasError: true }; }
  render() {
    if (this.state.hasError) return <div role="alert">Application error occurred.</div>;
    return this.props.children;
  }
}
