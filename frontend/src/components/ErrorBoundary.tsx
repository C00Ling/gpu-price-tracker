// Error boundary and error display components
import { Component } from 'react';
import type { ReactNode } from 'react';
import { Button } from './Button';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error, reset: () => void) => ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  reset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.reset);
      }

      return <ErrorFallback error={this.state.error} reset={this.reset} />;
    }

    return this.props.children;
  }
}

interface ErrorFallbackProps {
  error: Error;
  reset: () => void;
}

export function ErrorFallback({ error, reset }: ErrorFallbackProps) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#1E1E1E] px-4">
      <div className="max-w-md w-full bg-zinc-900 border border-zinc-800 rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-500/10 rounded-full">
          <span className="text-2xl">⚠️</span>
        </div>

        <h2 className="mt-4 text-xl font-semibold text-center text-white">
          Нещо се обърка
        </h2>

        <p className="mt-2 text-sm text-gray-400 text-center">
          Възникна грешка при зареждане на страницата
        </p>

        {error.message && (
          <div className="mt-4 p-3 bg-zinc-800 rounded text-xs text-gray-300 font-mono overflow-x-auto">
            {error.message}
          </div>
        )}

        <div className="mt-6 flex justify-center">
          <Button onClick={reset}>
            Опитай отново
          </Button>
        </div>
      </div>
    </div>
  );
}

interface ErrorMessageProps {
  message: string;
  retry?: () => void;
}

export function ErrorMessage({ message, retry }: ErrorMessageProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="text-red-500 text-5xl mb-4">⚠️</div>
      <h3 className="text-lg font-semibold text-white mb-2">Грешка</h3>
      <p className="text-gray-400 text-center mb-4">{message}</p>
      {retry && (
        <Button onClick={retry} variant="outline" size="sm">
          Опитай отново
        </Button>
      )}
    </div>
  );
}
