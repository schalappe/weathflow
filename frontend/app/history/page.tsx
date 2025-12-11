import { HistoryClient } from "@/components/history/history-client";
import { ErrorBoundary } from "@/components/ui/error-boundary";

export default function HistoryPage() {
  return (
    <ErrorBoundary>
      <HistoryClient />
    </ErrorBoundary>
  );
}
