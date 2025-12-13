import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ImportOptions } from "@/components/import/import-options";

describe("ImportOptions", () => {
  it("renders Replace and Merge radio options", () => {
    render(
      <ImportOptions mode="merge" onModeChange={vi.fn()} isDisabled={false} />,
    );

    expect(screen.getByLabelText(/Remplacer/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Fusionner/i)).toBeInTheDocument();
  });

  it("mode change triggers callback with correct value", () => {
    const onModeChange = vi.fn();
    render(
      <ImportOptions
        mode="merge"
        onModeChange={onModeChange}
        isDisabled={false}
      />,
    );

    // [>]: Click the Replace option.
    fireEvent.click(screen.getByLabelText(/Remplacer/i));

    expect(onModeChange).toHaveBeenCalledWith("replace");
  });
});
