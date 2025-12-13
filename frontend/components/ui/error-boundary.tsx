"use client";

import { Component, type ReactNode } from "react";
import { Card, CardContent } from "./card";
import { Button } from "./button";
import { AlertCircle } from "lucide-react";
import { t } from "@/lib/translations";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

// [>]: Error Boundary catches runtime errors in child components to prevent full page crashes.
export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.error("[ErrorBoundary] Caught error:", error, errorInfo);
  }

  handleRetry = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Card className="mx-auto mt-8 max-w-md">
          <CardContent className="flex flex-col items-center gap-4 py-8 text-center">
            <div className="rounded-full bg-red-100 p-3">
              <AlertCircle className="h-6 w-6 text-red-500" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">{t.errorBoundary.title}</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                {t.errorBoundary.description}
              </p>
            </div>
            <Button onClick={this.handleRetry}>{t.errorBoundary.retry}</Button>
          </CardContent>
        </Card>
      );
    }

    return this.props.children;
  }
}
