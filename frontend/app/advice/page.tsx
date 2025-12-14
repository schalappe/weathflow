import { AdvicePageClient } from "@/components/advice/advice-page-client";
import { ErrorBoundary } from "@/components/ui/error-boundary";

export default function AdvicePage() {
  return (
    <ErrorBoundary>
      <AdvicePageClient />
    </ErrorBoundary>
  );
}
