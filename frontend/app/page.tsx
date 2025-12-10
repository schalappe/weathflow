import { DashboardClient } from "@/components/dashboard/dashboard-client";
import { ErrorBoundary } from "@/components/ui/error-boundary";

export default function Home() {
  return (
    <ErrorBoundary>
      <DashboardClient />
    </ErrorBoundary>
  );
}
