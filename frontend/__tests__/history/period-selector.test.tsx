import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { PeriodSelector } from "@/components/history/period-selector";

describe("PeriodSelector", () => {
  it("renders with default value (12)", () => {
    render(<PeriodSelector value={12} onChange={() => {}} />);

    // [>]: The trigger should display the selected period label.
    expect(screen.getByRole("combobox")).toHaveTextContent("12 mois");
  });

  it("calls onChange with correct value when selection changes", async () => {
    const user = userEvent.setup();
    const handleChange = vi.fn();

    render(<PeriodSelector value={12} onChange={handleChange} />);

    // [>]: Open the dropdown and select a different option.
    await user.click(screen.getByRole("combobox"));
    await user.click(screen.getByRole("option", { name: "3 mois" }));

    expect(handleChange).toHaveBeenCalledWith(3);
  });

  it("displays all 3 period options", async () => {
    const user = userEvent.setup();

    render(<PeriodSelector value={12} onChange={() => {}} />);

    // [>]: Open dropdown to see all options.
    await user.click(screen.getByRole("combobox"));

    expect(screen.getByRole("option", { name: "3 mois" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "6 mois" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "12 mois" })).toBeInTheDocument();
  });
});
