"use client";

import { useState } from "react";
import { Download } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { exportMonthData, type ExportFormat } from "@/lib/api-client";

interface ExportButtonsProps {
  year: number;
  month: number;
  disabled?: boolean;
}

export function ExportButtons({ year, month, disabled }: ExportButtonsProps) {
  // [>]: Track which format is currently exporting (null when idle).
  const [exportingFormat, setExportingFormat] = useState<ExportFormat | null>(
    null,
  );

  async function handleExport(format: ExportFormat) {
    setExportingFormat(format);

    try {
      const blob = await exportMonthData(year, month, format);
      const url = window.URL.createObjectURL(blob);
      try {
        const a = document.createElement("a");
        a.href = url;
        a.download = `moneymap-${year}-${String(month).padStart(2, "0")}.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        toast.success(`${format.toUpperCase()} exported successfully`);
      } finally {
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error(
        `Export error for ${year}-${String(month).padStart(2, "0")} (${format}):`,
        error,
      );
      toast.error("Export failed", {
        description:
          error instanceof Error
            ? error.message
            : "An unexpected error occurred",
      });
    } finally {
      setExportingFormat(null);
    }
  }

  function renderExportButton(format: ExportFormat) {
    const isExporting = exportingFormat === format;

    return (
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleExport(format)}
        disabled={disabled || exportingFormat !== null}
      >
        <Download className="h-4 w-4" />
        {isExporting ? "Exporting..." : format.toUpperCase()}
      </Button>
    );
  }

  return (
    <div className="flex gap-2">
      {renderExportButton("json")}
      {renderExportButton("csv")}
    </div>
  );
}
