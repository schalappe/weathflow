"use client";

import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { pluralize } from "@/lib/utils";

interface ProgressPanelProps {
  selectedMonthCount: number;
  onCancel: () => void;
}

export function ProgressPanel({
  selectedMonthCount,
  onCancel,
}: ProgressPanelProps) {
  return (
    <div className="flex flex-col items-center gap-6 rounded-xl border bg-card p-8">
      <div className="flex items-center gap-3">
        <Loader2 className="h-5 w-5 animate-spin text-primary" />
        <p className="text-lg font-medium">
          Processing {pluralize(selectedMonthCount, "month")}...
        </p>
      </div>

      {/* [>]: Indeterminate progress - using animation to show activity. */}
      <div className="w-full max-w-md">
        <Progress value={undefined} className="h-2 animate-pulse" />
      </div>

      <p className="text-sm text-muted-foreground">
        This may take a moment depending on the number of transactions
      </p>

      <Button variant="outline" onClick={onCancel}>
        Cancel
      </Button>
    </div>
  );
}
