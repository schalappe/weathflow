"use client";

import { useState } from "react";
import { Download } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ExportButtonsProps {
  year: number;
  month: number;
  disabled?: boolean;
}

export function ExportButtons({ year, month, disabled }: ExportButtonsProps) {
  const [isExportingJson, setIsExportingJson] = useState(false);
  const [isExportingCsv, setIsExportingCsv] = useState(false);

  const handleExport = async (format: "json" | "csv") => {
    const setLoading =
      format === "json" ? setIsExportingJson : setIsExportingCsv;
    setLoading(true);

    try {
      const response = await fetch(
        `${API_BASE}/api/months/${year}/${month}/export/${format}`,
      );

      if (!response.ok) {
        // [>]: Extract error message from response body if available.
        const error = await response
          .json()
          .catch(() => ({ detail: "Export failed" }));
        throw new Error(error.detail);
      }

      // [>]: Create blob and trigger download via hidden anchor element.
      const blob = await response.blob();
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
        // [>]: Always cleanup blob URL to prevent memory leaks.
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error("Export error:", error);
      toast.error("Export failed", {
        description:
          error instanceof Error
            ? error.message
            : "An unexpected error occurred",
      });
    } finally {
      setLoading(false);
    }
  };

  const isExporting = isExportingJson || isExportingCsv;

  return (
    <div className="flex gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleExport("json")}
        disabled={disabled || isExporting}
      >
        <Download className="h-4 w-4" />
        {isExportingJson ? "Exporting..." : "JSON"}
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleExport("csv")}
        disabled={disabled || isExporting}
      >
        <Download className="h-4 w-4" />
        {isExportingCsv ? "Exporting..." : "CSV"}
      </Button>
    </div>
  );
}
