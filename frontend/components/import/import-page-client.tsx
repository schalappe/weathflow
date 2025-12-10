"use client";

import { useReducer, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, FileSpreadsheet } from "lucide-react";
import { FileDropzone } from "./file-dropzone";
import { MonthPreviewTable } from "./month-preview-table";
import { ImportOptions } from "./import-options";
import { ProgressPanel } from "./progress-panel";
import { ResultsSummary } from "./results-summary";
import { uploadCSV, categorize } from "@/lib/api-client";
import { getMonthKeys } from "@/lib/utils";
import type {
  ImportState,
  ImportAction,
  ImportMode,
  UploadResponse,
  CategorizeResponse,
} from "@/types";

// [>]: Initial state for the import page reducer.
const initialState: ImportState = {
  pageState: "empty",
  file: null,
  uploadResponse: null,
  selectedMonths: new Set(),
  importMode: "merge",
  categorizeResponse: null,
  error: null,
};

// [>]: Reducer function handles all state transitions.
function importReducer(state: ImportState, action: ImportAction): ImportState {
  switch (action.type) {
    case "FILE_SELECTED":
      return {
        ...state,
        file: action.payload,
        error: null,
      };

    case "UPLOAD_START":
      return {
        ...state,
        pageState: "uploading",
        error: null,
      };

    case "UPLOAD_SUCCESS": {
      // [>]: Select all months by default after upload.
      const allMonthKeys = getMonthKeys(action.payload.months_detected);
      return {
        ...state,
        pageState: "preview",
        uploadResponse: action.payload,
        selectedMonths: new Set(allMonthKeys),
      };
    }

    case "UPLOAD_ERROR":
      // [>]: Clear file on upload error - user must select again.
      return {
        ...initialState,
        pageState: "error",
        error: action.payload,
      };

    case "TOGGLE_MONTH": {
      const newSelected = new Set(state.selectedMonths);
      if (newSelected.has(action.payload)) {
        newSelected.delete(action.payload);
      } else {
        newSelected.add(action.payload);
      }
      return {
        ...state,
        selectedMonths: newSelected,
      };
    }

    case "SELECT_ALL_MONTHS": {
      if (!state.uploadResponse) return state;
      const allMonthKeys = getMonthKeys(state.uploadResponse.months_detected);
      return {
        ...state,
        selectedMonths: new Set(allMonthKeys),
      };
    }

    case "DESELECT_ALL_MONTHS":
      return {
        ...state,
        selectedMonths: new Set(),
      };

    case "SET_IMPORT_MODE":
      return {
        ...state,
        importMode: action.payload,
      };

    case "CATEGORIZE_START":
      return {
        ...state,
        pageState: "categorizing",
        error: null,
      };

    case "CATEGORIZE_SUCCESS":
      return {
        ...state,
        pageState: "results",
        categorizeResponse: action.payload,
      };

    case "CATEGORIZE_ERROR":
      // [>]: Keep file and selections on categorize error for retry.
      return {
        ...state,
        pageState: "error",
        error: action.payload,
      };

    case "RESET":
      return initialState;

    default:
      return state;
  }
}

export function ImportPageClient() {
  const [state, dispatch] = useReducer(importReducer, initialState);

  // [>]: Handle file selection and trigger upload.
  const handleFileSelected = useCallback(async (file: File) => {
    dispatch({ type: "FILE_SELECTED", payload: file });
    dispatch({ type: "UPLOAD_START" });

    try {
      const response: UploadResponse = await uploadCSV(file);
      dispatch({ type: "UPLOAD_SUCCESS", payload: response });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to upload file";
      dispatch({ type: "UPLOAD_ERROR", payload: message });
    }
  }, []);

  // [>]: Handle categorization.
  const handleCategorize = useCallback(async () => {
    if (!state.file) return;

    dispatch({ type: "CATEGORIZE_START" });

    try {
      const months = Array.from(state.selectedMonths);
      const response: CategorizeResponse = await categorize(
        state.file,
        months,
        state.importMode,
      );
      dispatch({ type: "CATEGORIZE_SUCCESS", payload: response });
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Failed to categorize transactions";
      dispatch({ type: "CATEGORIZE_ERROR", payload: message });
    }
  }, [state.file, state.selectedMonths, state.importMode]);

  // [>]: Handle month toggle.
  const handleToggleMonth = useCallback((monthKey: string) => {
    dispatch({ type: "TOGGLE_MONTH", payload: monthKey });
  }, []);

  // [>]: Handle select/deselect all.
  const handleSelectAll = useCallback(() => {
    dispatch({ type: "SELECT_ALL_MONTHS" });
  }, []);

  const handleDeselectAll = useCallback(() => {
    dispatch({ type: "DESELECT_ALL_MONTHS" });
  }, []);

  // [>]: Handle import mode change.
  const handleModeChange = useCallback((mode: ImportMode) => {
    dispatch({ type: "SET_IMPORT_MODE", payload: mode });
  }, []);

  // [>]: Handle finish/reset.
  const handleFinish = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  // [>]: Handle cancel - reset to initial state.
  const handleCancel = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  // [>]: Handle retry after error.
  const handleRetry = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  const isProcessing =
    state.pageState === "uploading" || state.pageState === "categorizing";
  const canCategorize =
    state.pageState === "preview" && state.selectedMonths.size > 0;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Import Transactions
        </h1>
        <p className="text-muted-foreground">
          Upload your Bankin`&apos;` CSV export to categorize transactions
        </p>
      </div>

      {/* Error alert */}
      {state.error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>{state.error}</span>
            <Button variant="outline" size="sm" onClick={handleRetry}>
              Try Again
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Empty state - show dropzone */}
      {(state.pageState === "empty" || state.pageState === "error") && (
        <FileDropzone
          onFileSelected={handleFileSelected}
          file={state.file}
          isDisabled={isProcessing}
          error={null}
        />
      )}

      {/* Uploading state */}
      {state.pageState === "uploading" && (
        <div className="flex items-center justify-center py-12">
          <div className="flex flex-col items-center gap-4">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            <p className="text-muted-foreground">Analyzing file...</p>
          </div>
        </div>
      )}

      {/* Preview state - show file analysis */}
      {state.pageState === "preview" && state.uploadResponse && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileSpreadsheet className="h-5 w-5" />
              File Analysis
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              {state.uploadResponse.total_transactions} transactions detected
              across {state.uploadResponse.months_detected.length} months
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            <MonthPreviewTable
              months={state.uploadResponse.months_detected}
              selectedMonths={state.selectedMonths}
              onToggleMonth={handleToggleMonth}
              onSelectAll={handleSelectAll}
              onDeselectAll={handleDeselectAll}
              isDisabled={isProcessing}
            />

            <ImportOptions
              mode={state.importMode}
              onModeChange={handleModeChange}
              isDisabled={isProcessing}
            />

            <div className="flex items-center gap-3 pt-4 border-t">
              <Button variant="outline" onClick={handleCancel}>
                Cancel
              </Button>
              <Button onClick={handleCategorize} disabled={!canCategorize}>
                Categorize Selected Months
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Categorizing state */}
      {state.pageState === "categorizing" && (
        <ProgressPanel
          selectedMonthCount={state.selectedMonths.size}
          onCancel={handleCancel}
        />
      )}

      {/* Results state */}
      {state.pageState === "results" && state.categorizeResponse && (
        <ResultsSummary
          results={state.categorizeResponse.months_processed}
          monthsNotFound={state.categorizeResponse.months_not_found}
          totalApiCalls={state.categorizeResponse.total_api_calls}
          onFinish={handleFinish}
        />
      )}
    </div>
  );
}
