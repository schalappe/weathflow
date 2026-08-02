import { AdvicePageClient } from "@/components/advice/advice-page-client";
import { ClarificationPrototype } from "@/components/advice/clarification-prototype";
import { ErrorBoundary } from "@/components/ui/error-boundary";

export default async function AdvicePage({
  searchParams,
}: {
  searchParams: Promise<{ prototype?: string; variant?: string }>;
}) {
  const query = await searchParams;

  return (
    <ErrorBoundary>
      {process.env.NODE_ENV !== "production" &&
      query.prototype === "clarification" ? (
        <ClarificationPrototype initialVariant={query.variant} />
      ) : (
        <AdvicePageClient />
      )}
    </ErrorBoundary>
  );
}
