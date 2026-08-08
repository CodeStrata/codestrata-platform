import { Component, type ErrorInfo, type ReactNode } from "react";

interface State {
  failed: boolean;
}

export class DashboardErrorBoundary extends Component<
  { children: ReactNode },
  State
> {
  state: State = { failed: false };

  static getDerivedStateFromError(): State {
    return { failed: true };
  }

  componentDidCatch(_error: Error, _info: ErrorInfo): void {
    // Do not dump stack/payload to UI.
  }

  render(): ReactNode {
    if (this.state.failed) {
      return (
        <div className="cs-state cs-state--error" role="alert">
          <strong>Dashboard error</strong>
          <span>Something went wrong rendering Community Insights. Try refreshing.</span>
          <button
            type="button"
            className="cs-button"
            onClick={() => this.setState({ failed: false })}
          >
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
