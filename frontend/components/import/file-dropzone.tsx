"use client";

import { useCallback, useState, useRef } from "react";
import { Upload, FileCheck, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { t } from "@/lib/translations";

interface FileDropzoneProps {
  onFileSelected: (file: File) => void;
  onValidationError: (message: string) => void;
  file: File | null;
  isDisabled: boolean;
  error: string | null;
}

export function FileDropzone({
  onFileSelected,
  onValidationError,
  file,
  isDisabled,
  error,
}: FileDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndSelect = useCallback(
    (selectedFile: File) => {
      // [>]: Only accept .csv files.
      if (!selectedFile.name.toLowerCase().endsWith(".csv")) {
        onValidationError(t.dropzone.invalidFile);
        return;
      }
      onFileSelected(selectedFile);
    },
    [onFileSelected, onValidationError],
  );

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (!isDisabled) {
        setIsDragging(true);
      }
    },
    [isDisabled],
  );

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      if (isDisabled) return;

      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) {
        validateAndSelect(droppedFile);
      }
    },
    [isDisabled, validateAndSelect],
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0];
      if (selectedFile) {
        validateAndSelect(selectedFile);
      }
    },
    [validateAndSelect],
  );

  const handleClick = useCallback(() => {
    if (!isDisabled) {
      inputRef.current?.click();
    }
  }, [isDisabled]);

  // [>]: Determine visual state: uploaded > error > dragging > default.
  const hasFile = file !== null;
  const hasError = error !== null;

  return (
    <div
      data-testid="dropzone"
      onClick={handleClick}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={cn(
        "relative flex flex-col items-center justify-center gap-4 rounded-xl border-2 border-dashed p-12 transition-all duration-200 cursor-pointer",
        // Default state
        !hasFile &&
          !hasError &&
          !isDragging &&
          "border-muted-foreground/25 bg-muted/30 hover:border-muted-foreground/50 hover:bg-muted/50",
        // Dragging state
        isDragging &&
          "border-primary bg-primary/5 scale-[1.02] shadow-lg shadow-primary/10",
        // Uploaded state
        hasFile &&
          !hasError &&
          "border-emerald-500 bg-emerald-50 dark:bg-emerald-950/20",
        // Error state
        hasError && "border-destructive bg-destructive/5",
        // Disabled state
        isDisabled && "opacity-50 cursor-not-allowed",
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv"
        onChange={handleInputChange}
        disabled={isDisabled}
        className="hidden"
      />

      {/* Icon */}
      <div
        className={cn(
          "flex h-16 w-16 items-center justify-center rounded-full transition-colors",
          !hasFile && !hasError && "bg-muted text-muted-foreground",
          isDragging && "bg-primary/10 text-primary",
          hasFile &&
            !hasError &&
            "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/50",
          hasError && "bg-destructive/10 text-destructive",
        )}
      >
        {hasFile && !hasError ? (
          <FileCheck className="h-8 w-8" />
        ) : hasError ? (
          <AlertCircle className="h-8 w-8" />
        ) : (
          <Upload className="h-8 w-8" />
        )}
      </div>

      {/* Text */}
      <div className="text-center">
        {isDragging ? (
          <p className="text-lg font-medium text-primary">
            {t.dropzone.dropToUpload}
          </p>
        ) : hasFile && !hasError ? (
          <>
            <p className="text-lg font-medium text-emerald-700 dark:text-emerald-400">
              {file.name}
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              {t.dropzone.clickToReplace}
            </p>
          </>
        ) : (
          <>
            <p className="text-lg font-medium text-foreground">
              {t.dropzone.dragHere}
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              {t.dropzone.orClick}
            </p>
          </>
        )}
      </div>

      {/* Error message */}
      {hasError && (
        <p className="text-sm font-medium text-destructive">{error}</p>
      )}

      {/* File format hint */}
      {!hasFile && !hasError && (
        <p className="text-xs text-muted-foreground/70">
          {t.dropzone.acceptedFormat}
        </p>
      )}
    </div>
  );
}
