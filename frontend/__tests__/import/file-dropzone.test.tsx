import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { FileDropzone } from "@/components/import/file-dropzone";

describe("FileDropzone", () => {
  it("accepts CSV file and triggers onFileSelected callback", () => {
    const onFileSelected = vi.fn();
    const onValidationError = vi.fn();
    render(
      <FileDropzone
        onFileSelected={onFileSelected}
        onValidationError={onValidationError}
        file={null}
        isDisabled={false}
        error={null}
      />,
    );

    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;
    const csvFile = new File(["content"], "test.csv", { type: "text/csv" });

    fireEvent.change(input, { target: { files: [csvFile] } });

    expect(onFileSelected).toHaveBeenCalledWith(csvFile);
    expect(onValidationError).not.toHaveBeenCalled();
  });

  it("rejects non-CSV file via input and triggers onValidationError", () => {
    const onFileSelected = vi.fn();
    const onValidationError = vi.fn();
    render(
      <FileDropzone
        onFileSelected={onFileSelected}
        onValidationError={onValidationError}
        file={null}
        isDisabled={false}
        error={null}
      />,
    );

    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;
    const excelFile = new File(["content"], "test.xlsx", {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });

    fireEvent.change(input, { target: { files: [excelFile] } });

    expect(onFileSelected).not.toHaveBeenCalled();
    expect(onValidationError).toHaveBeenCalledWith(
      "Invalid file type. Please select a CSV file (.csv extension required).",
    );
  });

  it("rejects non-CSV file dropped on dropzone", () => {
    const onFileSelected = vi.fn();
    const onValidationError = vi.fn();
    render(
      <FileDropzone
        onFileSelected={onFileSelected}
        onValidationError={onValidationError}
        file={null}
        isDisabled={false}
        error={null}
      />,
    );

    const dropzone = screen.getByTestId("dropzone");
    const excelFile = new File(["content"], "test.xlsx", {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });

    fireEvent.drop(dropzone, {
      dataTransfer: { files: [excelFile] },
    });

    expect(onFileSelected).not.toHaveBeenCalled();
    expect(onValidationError).toHaveBeenCalledWith(
      "Invalid file type. Please select a CSV file (.csv extension required).",
    );
  });

  it("displays error message when error prop is set", () => {
    const onFileSelected = vi.fn();
    const onValidationError = vi.fn();
    render(
      <FileDropzone
        onFileSelected={onFileSelected}
        onValidationError={onValidationError}
        file={null}
        isDisabled={false}
        error="Only CSV files are accepted"
      />,
    );

    expect(
      screen.getByText(/only csv files are accepted/i),
    ).toBeInTheDocument();
  });

  it("shows visual feedback on drag-over state", () => {
    const onFileSelected = vi.fn();
    const onValidationError = vi.fn();
    render(
      <FileDropzone
        onFileSelected={onFileSelected}
        onValidationError={onValidationError}
        file={null}
        isDisabled={false}
        error={null}
      />,
    );

    const dropzone = screen.getByTestId("dropzone");

    fireEvent.dragOver(dropzone, {
      dataTransfer: { types: ["Files"] },
    });

    // [>]: Dropzone should show "Drop to upload" text when dragging.
    expect(screen.getByText(/drop to upload/i)).toBeInTheDocument();
  });
});
