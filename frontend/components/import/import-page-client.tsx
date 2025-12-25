"use client";

import { useReducer, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import {
  AlertCircle,
  FileSpreadsheet,
  ArrowLeft,
  Sparkles,
  RefreshCw,
} from "lucide-react";
import { FileDropzone } from "./file-dropzone";
import { MonthPreviewTable } from "./month-preview-table";
import { ImportOptions } from "./import-options";
import { ProgressPanel } from "./progress-panel";
import { ResultsSummary } from "./results-summary";
import { TransactionReviewSheet } from "./transaction-review-sheet";
import { uploadCSV, categorize } from "@/lib/api-client";
import { getMonthKeys } from "@/lib/utils";
import { t } from "@/lib/translations";
import type {
  ImportState,
  ImportAction,
  ImportMode,
  UploadResponse,
  CategorizeResponse,
} from "@/types";

const initialState: ImportState = {
  pageState: "empty",
  file: null,
  uploadResponse: null,
  selectedMonths: new Set(),
  importMode: "merge",
  categorizeResponse: null,
  error: null,
  isReviewSheetOpen: false,
};

function importReducer(state: ImportState, action: ImportAction): ImportState {
  switch (action.type) {
    case "FILE_SELECTED":
      return {
        ...state,
        file: action.payload,
        error: null,
      };

    case "FILE_VALIDATION_ERROR":
      return {
        ...state,
        error: action.payload,
      };

    case "UPLOAD_START":
      return {
        ...state,
        pageState: "uploading",
        error: null,
      };

    case "UPLOAD_SUCCESS": {
      const allMonthKeys = getMonthKeys(action.payload.months_detected);
      return {
        ...state,
        pageState: "preview",
        uploadResponse: action.payload,
        selectedMonths: new Set(allMonthKeys),
      };
    }

    case "UPLOAD_ERROR":
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
      return {
        ...state,
        pageState: "error",
        error: action.payload,
      };

    case "RESET":
      return initialState;

    case "OPEN_REVIEW_SHEET":
      return {
        ...state,
        isReviewSheetOpen: true,
      };

    case "CLOSE_REVIEW_SHEET":
      return {
        ...state,
        isReviewSheetOpen: false,
      };

    default:
      return state;
  }
}

export function ImportPageClient() {
  const router = useRouter();
  const [state, dispatch] = useReducer(importReducer, initialState);

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

  const handleToggleMonth = useCallback((monthKey: string) => {
    dispatch({ type: "TOGGLE_MONTH", payload: monthKey });
  }, []);

  const handleSelectAll = useCallback(() => {
    dispatch({ type: "SELECT_ALL_MONTHS" });
  }, []);

  const handleDeselectAll = useCallback(() => {
    dispatch({ type: "DESELECT_ALL_MONTHS" });
  }, []);

  const handleModeChange = useCallback((mode: ImportMode) => {
    dispatch({ type: "SET_IMPORT_MODE", payload: mode });
  }, []);

  const handleFinish = useCallback(() => {
    router.push("/");
  }, [router]);

  const handleOpenReviewSheet = useCallback(() => {
    dispatch({ type: "OPEN_REVIEW_SHEET" });
  }, []);

  const handleCloseReviewSheet = useCallback(() => {
    dispatch({ type: "CLOSE_REVIEW_SHEET" });
  }, []);

  const handleCancel = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  const handleRetry = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  const handleValidationError = useCallback((message: string) => {
    dispatch({ type: "FILE_VALIDATION_ERROR", payload: message });
  }, []);

  const isProcessing =
    state.pageState === "uploading" || state.pageState === "categorizing";
  const canCategorize =
    state.pageState === "preview" && state.selectedMonths.size > 0;

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      {/* Page header */}
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">{t.import.title}</h1>
        <p className="text-muted-foreground">{t.import.subtitle}</p>
      </div>

      {/* Error alert */}
      {state.error && (
        <Alert
          variant="destructive"
          className="border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950"
        >
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>{state.error}</span>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRetry}
              className="gap-2"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              {t.import.retry}
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Empty state - show dropzone */}
      {(state.pageState === "empty" || state.pageState === "error") && (
        <div className="animate-fade-in-up">
          <FileDropzone
            onFileSelected={handleFileSelected}
            onValidationError={handleValidationError}
            file={state.file}
            isDisabled={isProcessing}
            error={state.error}
          />
        </div>
      )}

      {/* Uploading state */}
      {state.pageState === "uploading" && (
        <Card className="border-0 shadow-lg">
          <CardContent className="flex flex-col items-center justify-center gap-4 py-16">
            <div className="relative">
              <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary/20 border-t-primary" />
            </div>
            <div className="space-y-1 text-center">
              <p className="font-medium">{t.import.analyzing}</p>
              <p className="text-sm text-muted-foreground">
                {t.import.detectingMonths}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Preview state - show file analysis */}
      {state.pageState === "preview" && state.uploadResponse && (
        <Card className="border-0 shadow-lg animate-fade-in-up">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/10">
                <FileSpreadsheet className="h-5 w-5 text-violet-600 dark:text-violet-400" />
              </div>
              <div>
                <CardTitle className="text-lg">
                  {t.fileAnalysis.title}
                </CardTitle>
                <CardDescription>
                  {state.uploadResponse.total_transactions}{" "}
                  {t.fileAnalysis.transactions}{" "}
                  {state.uploadResponse.months_detected.length}{" "}
                  {t.fileAnalysis.months}
                </CardDescription>
              </div>
            </div>
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

            <Separator />

            <ImportOptions
              mode={state.importMode}
              onModeChange={handleModeChange}
              isDisabled={isProcessing}
            />

            <Separator />

            <div className="flex items-center justify-between">
              <Button
                variant="ghost"
                onClick={handleCancel}
                className="gap-2 text-muted-foreground"
              >
                <ArrowLeft className="h-4 w-4" />
                {t.fileAnalysis.startOver}
              </Button>
              <Button
                onClick={handleCategorize}
                disabled={!canCategorize}
                className="gap-2"
              >
                <Sparkles className="h-4 w-4" />
                {t.fileAnalysis.categorize}
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
        <>
          <ResultsSummary
            results={state.categorizeResponse.months_processed}
            monthsNotFound={state.categorizeResponse.months_not_found}
            totalApiCalls={state.categorizeResponse.total_api_calls}
            onFinish={handleFinish}
            onReviewClick={handleOpenReviewSheet}
          />

          <TransactionReviewSheet
            isOpen={state.isReviewSheetOpen}
            onClose={handleCloseReviewSheet}
            monthResults={state.categorizeResponse.months_processed}
          />
        </>
      )}
    </div>
  );
}
