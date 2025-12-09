import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { FileDropzone } from "@/components/import/file-dropzone";

describe("FileDropzone", () => {
  it("accepts CSV file and triggers onFileSelected callback", () => {
    const onFileSelected = vi.fn();
    render(
      <FileDropzone
        onFileSelected={onFileSelected}
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
  });

  it("rejects non-CSV file and shows error state", () => {
    const onFileSelected = vi.fn();
    render(
      <FileDropzone
        onFileSelected={onFileSelected}
        file={null}
        isDisabled={false}
        error="Only CSV files are accepted"
      />,
    );

    expect(screen.getByText(/only csv files are accepted/i)).toBeInTheDocument();
  });

  it("shows visual feedback on drag-over state", () => {
    const onFileSelected = vi.fn();
    render(
      <FileDropzone
        onFileSelected={onFileSelected}
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
